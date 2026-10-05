from .services import release_stock
import uuid
import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Order, Payment

@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=503)
    try:
        event = stripe.Webhook.construct_event(
            request.body, request.headers.get("Stripe-Signature", ""),
            settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)
    event_type = event["type"]
    if event_type not in {
        "checkout.session.completed", "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed", "checkout.session.expired",
    }:
        return HttpResponse(status=200)
    session = event["data"]["object"]
    try:
        order_id = uuid.UUID(session.get("metadata", {}).get("order_id", ""))
    except (ValueError, TypeError, AttributeError):
        return HttpResponse(status=400)
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
            payment = Payment.objects.select_for_update().get(order=order)
        except (Order.DoesNotExist, Payment.DoesNotExist):
            return HttpResponse(status=404)
        # A webhook may arrive before the checkout API call returns.
        if payment.session_id and payment.session_id != session["id"]:
            return HttpResponse(status=400)
        if (session.get("client_reference_id") != str(order.id)
                or session.get("currency") != order.currency
                or session.get("amount_total") != int(order.total * 100)):
            return HttpResponse(status=400)
        if order.status == Order.Status.PAID:
            return HttpResponse(status=200)
        payment.session_id = session["id"]
        if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            if session.get("payment_status") != "paid":
                return HttpResponse(status=200)
            order.status = Order.Status.PAID
            payment.payment_intent = session.get("payment_intent") or ""
            payment.paid_at = timezone.now()
        elif event_type == "checkout.session.expired":
            order.status = Order.Status.EXPIRED
        else:
            order.status = Order.Status.FAILED
        order.save(update_fields=["status"])
        payment.save()
        release_stock(order.pk)
    return HttpResponse(status=200)

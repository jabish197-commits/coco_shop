from .services import release_stock
import stripe
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils import timezone

def create_checkout(order):
    if not settings.STRIPE_SECRET_KEY:
        raise ImproperlyConfigured("Stripe is not configured.")
    confirmation = settings.SITE_URL + reverse("orders:confirmation", args=[order.id])
    if order.payment.session_id:
        session = stripe.checkout.Session.retrieve(
            order.payment.session_id, api_key=settings.STRIPE_SECRET_KEY)
        if session.status == "open":
            return session.url
        if session.status == "expired":
            # Conditional update cannot overwrite a concurrently confirmed payment.
            type(order).objects.filter(pk=order.pk, status="pending").update(status="expired")
        release_stock(order.pk)
        return confirmation
    if order.created_at < timezone.now() - timedelta(hours=23):
        raise ImproperlyConfigured("Old unlinked checkout requires payment reconciliation.")
    # Parameters and idempotency key remain identical across retries.
    session = stripe.checkout.Session.create(
        api_key=settings.STRIPE_SECRET_KEY,
        idempotency_key=f"checkout-{order.id}",
        mode="payment",
        payment_method_types=["card"],
        client_reference_id=str(order.id),
        customer_email=order.email,
        metadata={"order_id": str(order.id)},
        line_items=[{"price_data": {
            "currency": order.currency,
            "product_data": {"name": item.name},
            "unit_amount": int(item.price * 100),
        }, "quantity": item.quantity} for item in order.items.all()],
        success_url=settings.SITE_URL + reverse("orders:confirmation", args=[order.id]),
        cancel_url=settings.SITE_URL + reverse("orders:failed", args=[order.id]),
    )
    payment = order.payment
    payment.session_id = session.id
    payment.save(update_fields=["session_id"])
    return session.url

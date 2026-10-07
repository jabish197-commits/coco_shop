import logging
import uuid
from smtplib import SMTPException

import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.cart import Cart
from .forms import CheckoutForm
from .models import Order
from .payments import create_checkout
from .services import create_order
from .phone_verification import verified_phone
from accounts.email_verification import email_is_verified


logger = logging.getLogger(__name__)


@login_required
def checkout(request):
    if not email_is_verified(request.user):
        return redirect("accounts:verify_email")
    basket = Cart(request)

    if not len(basket):
        return redirect("cart:detail")

    key = request.session.setdefault(
        "checkout_key",
        str(uuid.uuid4()),
    )

    form = CheckoutForm(
        request.POST if request.method == "POST" else None,
        initial={
            "email": request.user.email,
            "checkout_key": key,
            "full_name": request.user.get_full_name(),
        },
    )

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        submitted = data.pop("checkout_key")

        if str(submitted) != str(key):
            form.add_error(
                None,
                "This checkout has expired. Reload this page.",
            )
        elif data['email'].casefold() != request.user.email.casefold():
            form.add_error('email', 'Use your verified account email. Change and verify it in your profile first.')
        elif not verified_phone(request.user, key, data['phone']):
            form.add_error('phone', 'Verify this phone number before saving your order.')
        else:
            try:
                order = create_order(
                    request.user,
                    basket,
                    data,
                    submitted,
                )

            except IntegrityError:
                # Reuse an existing order without sending another email.
                order = get_object_or_404(
                    Order,
                    checkout_key=submitted,
                    user=request.user,
                )
                messages.info(
                    request,
                    "This order has already been saved.",
                )

            except ValueError as error:
                form.add_error(None, str(error))
                return render(
                    request,
                    "orders/checkout.html",
                    {"form": form, "basket": basket},
                )

            except Exception:
                logger.exception("Could not create the order")
                form.add_error(
                    None,
                    "There was a problem saving your order. Please try again.",
                )
                return render(
                    request,
                    "orders/checkout.html",
                    {"form": form, "basket": basket},
                )

            else:
                # Send to the customer address entered in the form.
                customer_email = form.cleaned_data["email"]

                try:
                    sent = send_mail(
                        subject=f"Your order #{order.id} has been saved",
                        message=(
                            f"Hello {order.full_name},\n\n"
                            f"Your order #{order.id} has been saved.\n"
                            "Please review your order and complete payment.\n\n"
                            "Delivery address:\n"
                            f"{order.address}\n"
                            f"{order.city}, {order.postal_code}\n"
                            f"{order.country}\n\n"
                            "Thank you for shopping with us.\n\n"
                            "Cocoa Bliss"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[customer_email],
                        fail_silently=False,
                    )

                except (SMTPException, OSError):
                    logger.exception(
                        "Email failed for order %s",
                        order.id,
                    )
                    messages.warning(
                        request,
                        "Your order was saved, but the email could not be sent.",
                    )

                except Exception:
                    # Email errors must not undo an already saved order.
                    logger.exception(
                        "Unexpected email error for order %s",
                        order.id,
                    )
                    messages.warning(
                        request,
                        "Your order was saved, but the email could not be sent.",
                    )

                else:
                    if sent == 1:
                        messages.success(
                            request,
                            "Email sent successfully!",
                        )
                    else:
                        messages.warning(
                            request,
                            "Your order was saved, but the email could not be sent.",
                        )

            basket.clear()
            request.session.pop("checkout_key", None)

            return redirect(
                "orders:confirmation",
                order_id=order.id,
            )

    return render(
        request,
        "orders/checkout.html",
        {"form": form, "basket": basket},
    )


@login_required
@require_POST
def pay(request, order_id):
    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user,
    )

    if order.status != Order.Status.PENDING:
        return redirect(
            "orders:confirmation",
            order_id=order.id,
        )

    try:
        return redirect(create_checkout(order))

    except (stripe.StripeError, ImproperlyConfigured):
        logger.exception(
            "Could not start payment for order %s",
            order.id,
        )
        messages.error(
            request,
            "Payment is unavailable. Your order is saved; "
            "please try again later.",
        )
        return redirect(
            "orders:failed",
            order_id=order.id,
        )


@login_required
def confirmation(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        pk=order_id,
        user=request.user,
    )

    return render(
        request,
        "orders/order_confirmation.html",
        {"order": order},
    )


@login_required
def failed(request, order_id):
    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user,
    )

    return render(
        request,
        "orders/payment_failed.html",
        {"order": order},
    )


@login_required
def history(request):
    return render(
        request,
        "orders/history.html",
        {"orders": request.user.orders.all()[:100]},
    )
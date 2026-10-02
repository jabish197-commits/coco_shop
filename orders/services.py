from django.conf import settings
from django.db import transaction
from .models import Order, OrderItem, Payment

@transaction.atomic
def create_order(user, cart, data, checkout_key):
    existing = Order.objects.filter(checkout_key=checkout_key, user=user).first()
    if existing:
        return existing
    rows = list(cart)
    if not rows:
        raise ValueError("Your cart is empty.")
    order = Order.objects.create(user=user, checkout_key=checkout_key,
        currency=settings.CURRENCY, total=sum(row["total"] for row in rows), **data)
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=row["product"], name=row["product"].name,
                  price=row["price"], quantity=row["quantity"]) for row in rows
    ])
    Payment.objects.create(order=order)
    return order


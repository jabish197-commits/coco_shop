from django.db.models import F
from shop.models import Product
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
    for row in rows:
        updated = Product.objects.filter(pk=row['product'].pk, active=True, stock_quantity__gte=row['quantity']).update(stock_quantity=F('stock_quantity')-row['quantity'])
        if not updated:
            raise ValueError(f"Not enough stock for {row['product'].name}. Please update your bag.")
    order = Order.objects.create(user=user, checkout_key=checkout_key,
        stock_reserved=True, currency=settings.CURRENCY, total=sum(row["total"] for row in rows), **data)
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=row["product"], name=row["product"].name,
                  price=row["price"], quantity=row["quantity"]) for row in rows
    ])
    Payment.objects.create(order=order)
    return order



@transaction.atomic
def release_stock(order_id):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.stock_reserved and order.status in ('failed', 'expired'):
        for item in order.items.all():
            Product.objects.filter(pk=item.product_id).update(stock_quantity=F('stock_quantity')+item.quantity)
        order.stock_reserved = False
        order.save(update_fields=['stock_reserved'])

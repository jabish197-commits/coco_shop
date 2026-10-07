import uuid
from django.utils import timezone
from django.conf import settings
from django.db import models

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting payment"
        PAID = "paid", "Paid"
        FAILED = "failed", "Payment failed"
        EXPIRED = "expired", "Checkout expired"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_reserved = models.BooleanField(default=False, editable=False)
    checkout_key = models.UUIDField(unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=16, blank=True)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default="IN")
    gift_message = models.TextField(max_length=500, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="inr")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return str(self.id)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("shop.Product", on_delete=models.PROTECT)
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveSmallIntegerField()
    @property
    def total(self):
        return self.price * self.quantity

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payment_intent = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)


class PhoneVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=16, blank=True)
    checkout_key = models.UUIDField(null=True)
    window_start = models.DateTimeField(default=timezone.now)
    sends = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True)
    verified_until = models.DateTimeField(null=True)

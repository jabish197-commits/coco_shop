import json
import uuid
import hashlib
import hmac
import time
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from shop.models import Category, Product
from .models import Order, Payment
from .payments import create_checkout

@override_settings(STRIPE_WEBHOOK_SECRET="whsec_test", STRIPE_SECRET_KEY="sk_test_example")
class OrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", "buyer@example.com", "complex-pass-123!")
        self.client.force_login(self.user)
        category = Category.objects.create(name="Bars", slug="bars")
        self.product = Product.objects.create(category=category, name="Bar", slug="bar", price="8.50")
        self.client.post(f"/cart/add/{self.product.pk}/", {"quantity": 2})
        self.client.get("/orders/checkout/")
        self.data = {"checkout_key": self.client.session["checkout_key"],
            "full_name": "Ada Example", "email": "buyer@example.com", "address": "1 Main St",
            "city": "Boston", "postal_code": "02101", "country": "india", "gift_message": "Enjoy!"}
        self.client.post("/orders/checkout/", self.data)
        self.order = Order.objects.get()

    def event(self, event_type="checkout.session.completed", amount=1700):
        return {"id": "evt_example", "type": event_type, "data": {"object": {
            "id": "cs_example", "metadata": {"order_id": str(self.order.pk)},
            "client_reference_id": str(self.order.pk), "amount_total": amount,
            "currency": "usd", "payment_status": "paid", "payment_intent": "pi_example"}}}

    def deliver(self, event):
        with patch("orders.webhooks.stripe.Webhook.construct_event", return_value=event):
            return self.client.post("/orders/webhook/", data=json.dumps(event), content_type="application/json")

    def test_order_snapshot_and_duplicate_submit(self):
        self.product.price = Decimal("10")
        self.product.save()
        self.assertEqual(self.order.total, Decimal("17"))
        self.assertEqual(self.order.items.get().price, Decimal("8.50"))
        self.client.post("/orders/checkout/", self.data)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_authorization(self):
        other = User.objects.create_user("other", password="complex-pass-456!")
        self.client.force_login(other)
        self.assertEqual(self.client.get(f"/orders/{self.order.pk}/").status_code, 404)
        self.assertEqual(self.client.post(f"/orders/{self.order.pk}/pay/").status_code, 404)

    def test_success_page_does_not_mark_paid(self):
        self.assertEqual(self.client.get(f"/orders/{self.order.pk}/").status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_webhook_idempotent_and_no_status_regression(self):
        self.assertEqual(self.deliver(self.event()).status_code, 200)
        paid_at = Payment.objects.get().paid_at
        self.deliver(self.event())
        self.deliver(self.event("checkout.session.expired"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(Payment.objects.get().paid_at, paid_at)

    def test_wrong_amount_and_signature_rejected(self):
        self.assertEqual(self.deliver(self.event(amount=1)).status_code, 400)
        self.assertEqual(self.client.post("/orders/webhook/", data="{}", content_type="application/json").status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_wrong_session_rejected(self):
        payment = self.order.payment
        payment.session_id = "cs_original"
        payment.save()
        self.assertEqual(self.deliver(self.event()).status_code, 400)

    def test_real_webhook_signature(self):
        payload = json.dumps(self.event())
        timestamp = str(int(time.time()))
        signature = hmac.new(b"whsec_test", (timestamp + "." + payload).encode(), hashlib.sha256).hexdigest()
        response = self.client.post("/orders/webhook/", data=payload,
            content_type="application/json", HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}")
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_old_unlinked_checkout_requires_reconciliation(self):
        self.order.created_at = timezone.now() - timedelta(hours=24)
        with self.assertRaises(ImproperlyConfigured):
            create_checkout(self.order)

    @patch("orders.payments.stripe.checkout.Session.retrieve")
    def test_expired_session_closes_order(self, retrieve):
        payment = self.order.payment
        payment.session_id = "cs_expired"
        payment.save()
        retrieve.return_value.status = "expired"
        create_checkout(self.order)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "expired")

    @patch("orders.payments.stripe.checkout.Session.retrieve")
    @patch("orders.payments.stripe.checkout.Session.create")
    def test_payment_parameters_and_retry_key(self, create, retrieve):
        create.return_value.id = "cs_example"
        create.return_value.url = "https://checkout.stripe.com/example"
        retrieve.return_value.status = "open"
        retrieve.return_value.url = create.return_value.url
        create_checkout(self.order)
        create_checkout(self.order)
        self.assertEqual(create.call_count, 1)
        self.assertEqual(create.call_args.kwargs["idempotency_key"], f"checkout-{self.order.pk}")
        self.assertEqual(create.call_args.kwargs["line_items"][0]["price_data"]["unit_amount"], 850)

    def test_payment_outage_keeps_order(self):
        with patch("orders.views.create_checkout", side_effect=__import__("stripe").APIConnectionError("offline")):
            response = self.client.post(f"/orders/{self.order.pk}/pay/")
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

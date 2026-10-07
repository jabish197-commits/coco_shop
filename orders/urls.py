from django.urls import path
from . import views
from .webhooks import stripe_webhook
from .phone_verification import phone_otp
app_name = "orders"
urlpatterns = [
    path("phone-otp/", phone_otp, name="phone_otp"),
    path("", views.history, name="history"),
    path("checkout/", views.checkout, name="checkout"),
    path("webhook/", stripe_webhook, name="webhook"),
    path("<uuid:order_id>/", views.confirmation, name="confirmation"),
    path("<uuid:order_id>/pay/", views.pay, name="pay"),
    path("<uuid:order_id>/failed/", views.failed, name="failed"),
]

from django.urls import path
from . import views
from .webhooks import stripe_webhook
app_name = "orders"
urlpatterns = [
    path("", views.history, name="history"),
    path("checkout/", views.checkout, name="checkout"),
    path("webhook/", stripe_webhook, name="webhook"),
    path("<uuid:order_id>/", views.confirmation, name="confirmation"),
    path("<uuid:order_id>/pay/", views.pay, name="pay"),
    path("<uuid:order_id>/failed/", views.failed, name="failed"),
]

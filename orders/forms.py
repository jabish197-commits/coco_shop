from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    checkout_key = forms.UUIDField(widget=forms.HiddenInput)
    country = forms.ChoiceField(
        choices=[("IN", "India")],
        initial="IN",
    )
    class Meta:
        model = Order
        fields = ["full_name", "email", "address", "city", "postal_code", "country", "gift_message"]

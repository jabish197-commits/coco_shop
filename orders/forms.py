from django import forms
from .models import Order
from .phone_verification import normalize_phone

class CheckoutForm(forms.ModelForm):
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"type":"tel", "autocomplete":"tel", "placeholder":"+91 mobile number"}))

    def clean_phone(self):
        try:
            return normalize_phone(self.cleaned_data["phone"])
        except ValueError as error:
            raise forms.ValidationError(str(error))

    checkout_key = forms.UUIDField(widget=forms.HiddenInput)
    country = forms.ChoiceField(
        choices=[("IN", "India")],
        initial="IN",
    )
    class Meta:
        model = Order
        fields = ["full_name", "email", "phone", "address", "city", "postal_code", "country", "gift_message"]

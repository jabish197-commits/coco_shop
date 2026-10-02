from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]

    def clean_website(self):
        if self.cleaned_data["website"]:
            raise forms.ValidationError("Unable to accept this message.")
        return ""

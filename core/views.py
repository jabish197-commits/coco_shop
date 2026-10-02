from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from shop.models import Product
from .forms import ContactForm

def home(request):
    return render(request, "core/home.html", {"products": Product.objects.filter(active=True, featured=True)[:4]})

def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thank you. Your message has been received.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})

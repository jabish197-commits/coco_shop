from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import RegistrationForm

def register(request):
    if request.user.is_authenticated:
        return redirect("shop:product_list")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("shop:product_list")
    return render(request, "accounts/register.html", {"form": form})

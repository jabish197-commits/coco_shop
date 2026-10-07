from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import RegistrationForm

def register(request):
    if request.user.is_authenticated:
        return redirect("shop:product_list")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        request.session["pending_email_user"] = user.pk
        return redirect("accounts:verify_email")
    return render(request, "accounts/register.html", {"form": form})


from django.contrib.auth.views import LoginView
from django.urls import reverse

class RoleLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        # Admins always land on their dashboard, including customer next links.
        if self.request.user.is_staff:
            return reverse("admin:index")
        return super().get_success_url()


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import ProfileForm

@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})

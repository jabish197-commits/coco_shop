from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView
from .views import register, RoleLoginView, profile
from .email_verification import verify_email
app_name = "accounts"
urlpatterns = [
    path("verify-email/", verify_email, name="verify_email"),
    path("profile/", profile, name="profile"),
    path("register/", register, name="register"),
    path("login/", RoleLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logged-out/", TemplateView.as_view(template_name="accounts/logged_out.html"), name="logged_out"),
]

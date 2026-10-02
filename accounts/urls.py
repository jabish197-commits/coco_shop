from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView
from .views import register
app_name = "accounts"
urlpatterns = [
    path("register/", register, name="register"),
    path("login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logged-out/", TemplateView.as_view(template_name="accounts/logged_out.html"), name="logged_out"),
]

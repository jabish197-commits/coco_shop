from django.urls import path
from django.views.generic import TemplateView
from . import views
app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", TemplateView.as_view(template_name="core/about.html"), name="about"),
    path("faq/", TemplateView.as_view(template_name="core/faq.html"), name="faq"),
    path("contact/", views.contact, name="contact"),
]

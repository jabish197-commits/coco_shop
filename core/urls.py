from django.urls import path
from django.views.generic import TemplateView, RedirectView
from . import views
app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", RedirectView.as_view(pattern_name="shop:product_list", permanent=False), name="about"),
    path("faq/", TemplateView.as_view(template_name="core/faq.html"), name="faq"),
    path("contact/", views.contact, name="contact"),
]


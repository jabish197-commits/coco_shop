from django.urls import path
from . import views
app_name = "shop"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("favourites/", views.favourites, name="favourites"),
    path("gift-boxes/", views.product_list, {"gifts": True}, name="gift_boxes"),
    path("<slug:slug>/", views.product_detail, name="product_detail"),
]

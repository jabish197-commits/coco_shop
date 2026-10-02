from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from cart.forms import CartAddForm
from .models import Product, Category

def favourites(request):
    return render(request, "shop/favourites.html", {
        "products": Product.objects.filter(active=True).prefetch_related("images"),
    })

def product_list(request, gifts=False):
    products = Product.objects.filter(active=True).prefetch_related("images")
    if gifts:
        products = products.filter(is_gift_box=True)
    category = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()[:100]
    if category:
        products = products.filter(category__slug=category)
    if len(query) >= 2:
        products = products.filter(name__icontains=query)
    elif query:
        products = products.filter(
            Q(name__istartswith=query)
            | Q(name__icontains=" " + query)
            | Q(name__icontains="-" + query)
        )
    return render(request, "shop/gift_boxes.html" if gifts else "shop/product_list.html", {
        "page_obj": Paginator(products, 12).get_page(request.GET.get("page")),
        "categories": Category.objects.all(), "query": query, "selected_category": category})

def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related("images"), slug=slug, active=True)
    return render(request, "shop/product_detail.html", {"product": product, "form": CartAddForm()})

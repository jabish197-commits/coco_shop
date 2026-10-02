from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from .forms import CartAddForm

def detail(request):
    return render(request, "cart/cart_detail.html", {"basket": Cart(request)})

@require_POST
def add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)
    form = CartAddForm(request.POST)
    if form.is_valid():
        try:
            Cart(request).add(product, form.cleaned_data["quantity"], request.POST.get("replace") == "1")
        except ValueError as error:
            messages.error(request, str(error))
    else:
        messages.error(request, "Choose a quantity from 1 to 99.")
    return redirect("cart:detail")

@require_POST
def remove(request, product_id):
    Cart(request).remove(product_id)
    return redirect("cart:detail")

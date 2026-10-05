from decimal import Decimal
from shop.models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get("cart", {}).copy()

    def save(self):
        self.session["cart"] = self.data
        self.session.modified = True

    def add(self, product, quantity=1, replace=False):
        key = str(product.pk)
        quantity = quantity if replace else self.data.get(key, 0) + quantity
        if not 1 <= quantity <= 99:
            raise ValueError("Choose between 1 and 99 per product.")
        if quantity > product.stock_quantity:
            raise ValueError(f"Only {product.stock_quantity} units of {product.name} are available.")
        self.data[key] = quantity
        self.save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self.save()

    def clear(self):
        self.data = {}
        self.save()

    def __iter__(self):
        products = Product.objects.filter(pk__in=self.data, active=True).prefetch_related("images")
        valid = {str(product.pk) for product in products}
        if set(self.data) != valid:
            self.data = {key: value for key, value in self.data.items() if key in valid}
            self.save()
        for product in products:
            quantity = self.data[str(product.pk)]
            yield {"product": product, "quantity": quantity,
                   "price": product.price, "total": product.price * quantity}

    def __len__(self):
        return sum(item["quantity"] for item in self)

    @property
    def total(self):
        return sum((item["total"] for item in self), Decimal("0.00"))

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    ingredients = models.TextField(blank=True)
    allergens = models.CharField(max_length=250, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.50"))])
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Units available to sell. Pending orders already reserve their units.")
    active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    is_gift_box = models.BooleanField(default=False)
    class Meta:
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=Decimal("0.50")), name="product_positive_price")]
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("shop:product_detail", args=[self.slug])

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200)
    position = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["position", "pk"]

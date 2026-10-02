from django.test import TestCase
from .models import Category, Product

class ShopTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Bars", slug="bars")
        self.product = Product.objects.create(category=category, name="Dark bar", slug="dark", price="8.50", description="Rich cocoa")

    def test_visible_and_searchable(self):
        self.assertContains(self.client.get("/shop/?q=dark"), "Dark bar")
        self.assertEqual(self.client.get("/shop/dark/").status_code, 200)

    def test_hidden_product(self):
        self.product.active = False
        self.product.save()
        self.assertEqual(self.client.get("/shop/dark/").status_code, 404)

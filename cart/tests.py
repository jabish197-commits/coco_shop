from django.test import TestCase, Client
from shop.models import Category, Product

class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Bars", slug="bars")
        self.product = Product.objects.create(category=category, name="Bar", slug="bar", price="8.50")
        self.url = f"/cart/add/{self.product.pk}/"

    def test_mutations_and_bounds(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.client.post(self.url, {"quantity": 2})
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 2)
        self.client.post(self.url, {"quantity": 99})
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 2)
        self.client.post(self.url, {"quantity": 3, "replace": "1"})
        self.assertContains(self.client.get("/cart/"), "25.50")
        self.client.post(f"/cart/remove/{self.product.pk}/")
        self.assertEqual(self.client.session["cart"], {})

    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.url, {"quantity": 1}).status_code, 403)

    def test_inactive_product_removed(self):
        self.client.post(self.url, {"quantity": 1})
        self.product.active = False
        self.product.save()
        self.client.get("/cart/")
        self.assertEqual(self.client.session["cart"], {})

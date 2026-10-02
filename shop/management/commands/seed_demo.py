from django.core.management.base import BaseCommand
from shop.models import Category, Product

class Command(BaseCommand):
    help = "Create optional sample products without overwriting existing products."
    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(slug="chocolate", defaults={"name": "Chocolate"})
        for name, slug, price, gift in [
            ("Dark Cocoa Bar", "dark-cocoa-bar", "8.50", False),
            ("Milk Chocolate Moments", "milk-chocolate-moments", "7.50", False),
            ("Hazelnut Delight", "hazelnut-delight", "9.00", False),
            ("The Bliss Gift Box", "bliss-gift-box", "28.00", True),
        ]:
            Product.objects.get_or_create(slug=slug, defaults={
                "category": category, "name": name, "price": price, "featured": True,
                "is_gift_box": gift, "description": "Sample product. Replace with your product description.",
                "ingredients": "Sample listing. Confirm ingredients with the shop before ordering.",
                "allergens": "Sample listing. Confirm allergens with the shop before ordering.",
            })
        self.stdout.write(self.style.SUCCESS("Sample catalog ready."))

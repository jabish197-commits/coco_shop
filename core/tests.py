from django.test import TestCase
from .models import ContactMessage

class CoreTests(TestCase):
    def test_pages(self):
        for url in ["/", "/about/", "/faq/", "/contact/"]:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_contact_saved(self):
        response = self.client.post("/contact/", {"name": "Ada", "email": "ada@example.com", "message": "Hello"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_honeypot(self):
        self.client.post("/contact/", {"name": "Bot", "email": "bot@example.com", "message": "Spam", "website": "spam"})
        self.assertFalse(ContactMessage.objects.exists())

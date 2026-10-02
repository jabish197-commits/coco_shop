from django.contrib.auth.models import User
from django.test import TestCase

class AccountTests(TestCase):
    def test_registration_and_post_logout(self):
        response = self.client.post("/accounts/register/", {
            "username": "chocofan", "email": "fan@example.com",
            "password1": "Cocoa-unusual-8432!", "password2": "Cocoa-unusual-8432!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="chocofan").exists())
        self.assertEqual(self.client.get("/accounts/logout/").status_code, 405)
        self.assertEqual(self.client.post("/accounts/logout/").status_code, 302)

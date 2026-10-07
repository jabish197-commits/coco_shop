from django.conf import settings
from django.db import models
from django.utils import timezone

class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(blank=True)
    code_hash = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField(null=True)
    verified = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True)
    window_start = models.DateTimeField(default=timezone.now)
    sends = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)

import re
import requests
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import PhoneVerification


def normalize_phone(value):
    number = re.sub(r'[\s()-]', '', value)
    if re.fullmatch(r'[6-9][0-9]{9}', number):
        number = '+91' + number
    if not re.fullmatch(r'\+91[6-9][0-9]{9}', number):
        raise ValueError('Enter a valid Indian mobile number, including +91.')
    return number


def verified_phone(user, key, phone):
    return PhoneVerification.objects.filter(user=user, checkout_key=key, phone=phone,
        verified_until__gt=timezone.now()).exists()


def twilio_request(action, data):
    sid = settings.TWILIO_VERIFY_SERVICE_SID
    if not re.fullmatch(r'VA[0-9a-fA-F]{32}', sid) or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_ACCOUNT_SID:
        raise ValueError('Phone verification is not configured yet. Please contact the store.')
    try:
        response = requests.post('https://verify.twilio.com/v2/Services/' + sid + '/' + action,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            data=data, timeout=(5, 10), allow_redirects=False)
        if response.status_code not in (200,201):
            raise ValueError('OTP request failed. Check the number and trial eligibility, or try again later.')
        return response.json().get('status')
    except (requests.RequestException, requests.exceptions.JSONDecodeError):
        raise ValueError('Phone verification is temporarily unavailable. Please try again.') from None


@login_required
@require_POST
def phone_otp(request):
    key = request.session.get('checkout_key')
    if not key or request.POST.get('checkout_key') != key:
        return JsonResponse({'message':'Reload checkout before requesting a code.'}, status=400)
    if not settings.PHONE_OTP_ENABLED:
        return JsonResponse({'message':'Phone verification is not enabled yet.'}, status=400)
    try:
        phone = normalize_phone(request.POST.get('phone',''))
        action = request.POST.get('action')
        if action not in ('send','verify'):
            raise ValueError('Invalid verification action.')
        now = timezone.now()
        # Database lock keeps limits consistent across workers and concurrent requests.
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            item, _ = PhoneVerification.objects.get_or_create(user=request.user)
            if item.window_start < now - timedelta(hours=1):
                item.sends = item.attempts = 0
                item.window_start = now
            if action == 'send':
                if item.sends >= 5 or (item.sent_at and item.sent_at > now-timedelta(seconds=60)):
                    raise ValueError('Please wait. Codes are limited to one per minute and five per hour.')
                item.phone, item.checkout_key = phone, key
                item.verified_until = None
                item.sent_at = now
                item.sends += 1
                item.save()
            else:
                code = request.POST.get('code','')
                if not re.fullmatch(r'[0-9]{4,10}',code):
                    raise ValueError('Enter the code from your SMS.')
                if item.phone != phone or str(item.checkout_key) != key or not item.sent_at or item.sent_at < now-timedelta(minutes=10):
                    raise ValueError('Request a new code for this phone number.')
                if item.attempts >= 5:
                    raise ValueError('Too many attempts. Try again in an hour.')
                item.attempts += 1
                item.save()
        # Network calls are outside the transaction; rejected attempts still consume limits.
        if action == 'send':
            status = twilio_request('Verifications', {'To':phone,'Channel':'sms'})
            if status != 'pending':
                raise ValueError('The code could not be sent. Please try later.')
            return JsonResponse({'message':'Code sent. Enter it below within 10 minutes.'})
        status = twilio_request('VerificationCheck', {'To':phone,'Code':code})
        if status != 'approved':
            raise ValueError('Incorrect or expired code.')
        updated = PhoneVerification.objects.filter(pk=item.pk, phone=phone, checkout_key=key, sent_at=item.sent_at).update(verified_until=now+timedelta(minutes=10))
        if not updated:
            raise ValueError('A newer code was requested. Please verify again.')
        return JsonResponse({'message':'Phone verified. You can save your order.', 'verified':True})
    except ValueError as error:
        return JsonResponse({'message':str(error)},status=400)

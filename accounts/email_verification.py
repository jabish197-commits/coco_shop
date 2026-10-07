import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import EmailVerification


def email_is_verified(user):
    return EmailVerification.objects.filter(user=user, email__iexact=user.email, verified=True).exists()


@require_http_methods(['GET','POST'])
def verify_email(request):
    uid = request.user.pk if request.user.is_authenticated else request.session.get('pending_email_user')
    user = get_user_model().objects.filter(pk=uid).first()
    if user is None:
        return redirect('accounts:register')
    if email_is_verified(user):
        return redirect('shop:product_list')
    message = ''
    if request.method == 'POST':
        now=timezone.now()
        action=request.POST.get('action')
        code_to_send=None
        approved=False
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=user.pk)
            item,_=EmailVerification.objects.get_or_create(user=user)
            if item.window_start < now-timedelta(hours=1):
                item.sends=item.attempts=0
                item.window_start=now
            if action=='send':
                if item.sends>=5 or (item.sent_at and item.sent_at>now-timedelta(seconds=60)):
                    message='Wait at least 60 seconds between codes. Maximum five sends per hour.'
                else:
                    code_to_send=f'{secrets.randbelow(1000000):06d}'
                    item.email=user.email
                    item.code_hash=make_password(code_to_send)
                    item.expires_at=now+timedelta(minutes=10)
                    item.verified=False
                    item.sent_at=now
                    item.sends+=1
            elif action=='verify':
                code=request.POST.get('code','').strip()
                if item.attempts>=5:
                    message='Too many attempts. Please try again in an hour.'
                elif not item.expires_at or item.expires_at<=now or item.email.casefold()!=user.email.casefold():
                    message='Request a new email code.'
                else:
                    item.attempts+=1
                    if len(code)==6 and code.isascii() and code.isdigit() and check_password(code,item.code_hash):
                        item.verified=True
                        item.code_hash=''
                        item.expires_at=None
                        # Only activate an account created by this registration session.
                        if not request.user.is_authenticated and request.session.get('pending_email_user')==user.pk:
                            user.is_active=True
                            user.save(update_fields=['is_active'])
                        approved=True
                    else:
                        message='Incorrect code. Please try again.'
            item.save()
        if approved:
            if not request.user.is_authenticated:
                login(request,user,backend='django.contrib.auth.backends.ModelBackend')
            request.session.pop('pending_email_user',None)
            return redirect('shop:product_list')
        if code_to_send:
            try:
                sent=send_mail('Verify your Cocoa Bliss email',
                    f'Your verification code is {code_to_send}. It expires in 10 minutes. Do not share it.',
                    settings.DEFAULT_FROM_EMAIL,[user.email],fail_silently=False)
                message='Code sent. Check your inbox and spam folder.' if sent else 'Email could not be sent. Please try again later.'
            except Exception:
                message='Email could not be sent. Please try again later.'
    return render(request,'accounts/verify_email.html',{'message':message})

from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from accounts.models import EmailVerification
from orders.models import PhoneVerification
from orders.phone_verification import verified_phone
import uuid

@override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
class OTPTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user('buyer','buyer@example.com','test-password')
  self.client.force_login(self.user)
  self.key=str(uuid.uuid4());s=self.client.session;s['checkout_key']=self.key;s.save()
 def test_email_code_is_hashed(self):
  with patch('accounts.email_verification.send_mail',return_value=1):
   self.client.post('/accounts/verify-email/',{'action':'send'})
  item=EmailVerification.objects.get(user=self.user)
  self.assertNotEqual(len(item.code_hash),6)
  self.assertFalse(item.verified)
 def test_email_expired_rejected(self):
  EmailVerification.objects.create(user=self.user,email=self.user.email,code_hash=make_password('123456'),expires_at=timezone.now()-timedelta(seconds=1))
  self.client.post('/accounts/verify-email/',{'action':'verify','code':'123456'})
  self.assertFalse(EmailVerification.objects.get(user=self.user).verified)
 def test_email_accept_and_replay(self):
  EmailVerification.objects.create(user=self.user,email=self.user.email,code_hash=make_password('123456'),expires_at=timezone.now()+timedelta(minutes=5))
  self.client.post('/accounts/verify-email/',{'action':'verify','code':'123456'})
  item=EmailVerification.objects.get(user=self.user);self.assertTrue(item.verified);self.assertEqual(item.code_hash,'')
 def test_phone_cooldown(self):
  with patch('orders.phone_verification.twilio_request',return_value='pending') as api:
   data={'checkout_key':self.key,'phone':'9876543210','action':'send'}
   self.assertEqual(self.client.post('/orders/phone-otp/',data).status_code,200)
   self.assertEqual(self.client.post('/orders/phone-otp/',data).status_code,400)
   self.assertEqual(api.call_count,1)
 def test_phone_bound_to_checkout_and_number(self):
  PhoneVerification.objects.create(user=self.user,phone='+919876543210',checkout_key=self.key,sent_at=timezone.now())
  with patch('orders.phone_verification.twilio_request',return_value='approved'):
   result=self.client.post('/orders/phone-otp/',{'checkout_key':self.key,'phone':'9876543210','action':'verify','code':'123456'})
  self.assertEqual(result.status_code,200)
  self.assertTrue(verified_phone(self.user,self.key,'+919876543210'))
  self.assertFalse(verified_phone(self.user,str(uuid.uuid4()),'+919876543210'))
  self.assertFalse(verified_phone(self.user,self.key,'+919876543211'))
 def test_phone_unknown_session_denied(self):
  result=self.client.post('/orders/phone-otp/',{'checkout_key':str(uuid.uuid4()),'phone':'9876543210','action':'send'})
  self.assertEqual(result.status_code,400)

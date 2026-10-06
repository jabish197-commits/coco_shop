from email.utils import parseaddr
from smtplib import SMTPException

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    """Send Django mail through Brevo HTTPS, without blocked SMTP ports."""

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                self._send(message)
            except SMTPException:
                if not self.fail_silently:
                    raise
            else:
                sent += 1
        return sent

    def _send(self, message):
        key = settings.BREVO_API_KEY
        if not key:
            raise SMTPException('Brevo API key is missing. Set BREVO_API_KEY.')
        # Validate Django headers before converting to the API payload.
        message.message()
        def address(value):
            name, email = parseaddr(value)
            return {'email': email, **({'name': name} if name else {})}
        payload = {'sender': address(message.from_email), 'subject': message.subject}
        for field in ('to', 'cc', 'bcc'):
            values = getattr(message, field)
            if values:
                payload[field] = [address(value) for value in values]
        if message.reply_to:
            payload['replyTo'] = address(message.reply_to[0])
        payload['htmlContent' if message.content_subtype == 'html' else 'textContent'] = message.body
        for alternative in getattr(message, 'alternatives', []):
            if alternative.mimetype == 'text/html':
                payload['htmlContent'] = alternative.content
        if message.attachments:
            raise SMTPException('Attachments are not supported by this email backend.')
        try:
            response = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={'api-key': key, 'accept': 'application/json'},
                json=payload, timeout=(5, 10), allow_redirects=False,
            )
        except requests.RequestException:
            raise SMTPException('Brevo connection failed or timed out.') from None
        if response.status_code != 201:
            # Never log response bodies, which may include addresses or secrets.
            hints = {400: 'Check the verified sender and email settings.',
                     401: 'Check BREVO_API_KEY.', 403: 'Check account activation and API access.',
                     429: 'Email quota or rate limit reached.'}
            hint = hints.get(response.status_code, 'Check Brevo service status and account logs.')
            raise SMTPException(f'Brevo rejected email (HTTP {response.status_code}). {hint}')

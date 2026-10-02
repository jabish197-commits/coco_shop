# Cocoa Bliss

Django 5.2 storefront with registration, session cart, immutable order line snapshots,
Stripe-hosted card checkout, signed webhooks, order history, and administration.

## Run locally (Python 3.10+)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set a random SECRET_KEY.
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/ and /admin/. On macOS/Linux use
`source .venv/bin/activate` and `cp .env.example .env`.
Generate a secret with `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
The included SQLite database has only schema migrations; no users or credentials.
Demo products are optional and explicitly sample data. Replace ingredients, allergens,
copy, images, and pricing with approved business information before selling.

## Stripe

Set STRIPE_SECRET_KEY to a test secret key. Use Stripe CLI:
`stripe listen --forward-to localhost:8000/orders/webhook/`.
Copy its signing secret to STRIPE_WEBHOOK_SECRET in .env, then restart Django.
Place an order and choose Continue to secure payment.
Use Stripe's test card 4242 4242 4242 4242 with a future expiry and any CVC.
Use test keys only during development.

Register your HTTPS /orders/webhook/ endpoint in Stripe for production and subscribe to
checkout.session.completed, checkout.session.async_payment_succeeded,
checkout.session.async_payment_failed, and checkout.session.expired.
Set the production endpoint's signing secret and live API key.
Paid status comes only from a valid signed webhook with matching order, session,
currency and amount. Returning to the success page alone never confirms payment.
Webhook retries are safe; a paid order cannot be downgraded by a delayed event.
Order pages are restricted to the account that created them.

The project uses USD, US delivery addresses, and delivery-inclusive final prices.
No inventory limits, shipping quotes, tax engine, fulfillment automation or automatic
refunds are implemented. Products are sold without stock tracking. Configure the
business's pricing/tax treatment, delivery and refund policies before accepting live sales.
Refunds can be handled through Stripe Dashboard; refund synchronization is not implemented.
Pending orders are durable: return through My orders to resume the existing Stripe
checkout session. Expired checkout sessions require a new order. Unlinked orders
older than 23 hours are blocked from payment retries and require operator reconciliation
in Stripe, because Stripe idempotency keys have a limited lifetime.

Contact submissions are saved in Django admin; they do not send email.
Review and remove submissions according to your retention policy.
Built-in Django admin handles product image uploads. The hero image is a procedural
illustration, not a product photograph.

## Verification

```powershell
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

Tests use mocked Stripe calls; live payment completion requires configured test keys
and a running Stripe webhook listener.
Verified locally with Django 5.2.12, Stripe 12.0.1, python-dotenv 1.1.0,
WhiteNoise 6.9.0 and Pillow 12.3.0. Requirements permit newer patch releases.

## Deployment

Set DEBUG=False, a unique strong SECRET_KEY, ALLOWED_HOSTS, and an HTTPS SITE_URL.
Run migrations, collectstatic and `python manage.py check --deploy`.
Serve config.wsgi:application or config.asgi:application using your platform's
production server. Never use runserver in production.
HTTPS is enforced when DEBUG=False. Configure proxy trust only for a trusted deployment
proxy. Serve uploaded media separately with non-executable content and back it up.
WhiteNoise serves collected static assets. SQLite is for local/single-instance use;
configure PostgreSQL and its driver for a multi-instance deployment.
Add platform-level rate limits to login, registration and contact endpoints.
No default admin account or production secrets are included.

References:
- [Django 5.2 documentation](https://docs.djangoproject.com/en/5.2/)
- [Stripe Checkout session API](https://docs.stripe.com/api/checkout/sessions/create?lang=python)
- [Stripe webhook signatures](https://docs.stripe.com/webhooks/signature)

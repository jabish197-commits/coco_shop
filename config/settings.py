import os
from pathlib import Path


from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# General
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Set SECRET_KEY in your .env file.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS", "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]


# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "shop",
    "cart",
    "orders",
]


# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# URLs and templates
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Database
import dj_database_url

if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {"timeout": 20},
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "shop:product_list"
LOGOUT_REDIRECT_URL = "accounts:logged_out"


# Language and time
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static and uploaded files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": ("core.media_storage.ProductImageStorage"
                    if os.getenv("CLOUDINARY_URL", "").strip()
                    else "django.core.files.storage.FileSystemStorage"),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedStaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Website
SITE_URL = os.getenv(
    "SITE_URL", "http://127.0.0.1:8002"
).rstrip("/")

CSRF_TRUSTED_ORIGINS = [SITE_URL]


# Payments
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Keep this consistent with your product prices and payment code.
CURRENCY = "inr"


# Email: Brevo HTTPS API works on Render Free (SMTP ports are blocked).
EMAIL_BACKEND = "core.email_backend.EmailBackend"
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "").strip()
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", os.getenv("EMAIL_HOST_USER", "")).strip()
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", DEFAULT_FROM_EMAIL)


# Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Twilio Verify trial: only pre-verified test recipients can receive SMS.
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID', '').strip()
PHONE_OTP_ENABLED = True

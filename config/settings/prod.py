from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

# Both are required in production: a missing value raises ImproperlyConfigured at startup.
SECRET_KEY = env.str("SECRET_KEY")  # noqa: F405
DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405

# The admin must not sit at the guessable /admin/. Set ADMIN_URL in the environment to something private.
if ADMIN_URL.lower() in ("", "admin/"):  # noqa: F405
    raise ImproperlyConfigured(
        'ADMIN_URL is missing or is "admin/". Set a private address in the environment, e.g. ADMIN_URL=staff-4f8k2/'
    )

# Static files are served by WhiteNoise with hashed names.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# HTTPS (the app runs behind a reverse proxy that sets X-Forwarded-Proto).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

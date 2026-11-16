"""Налаштування production: обов'язкові секрети, HTTPS, SMTP, журнали."""
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from config.jsonlog import logging_config

from .base import *  # noqa: F403

DEBUG = False

# Both are required in production: a missing value raises ImproperlyConfigured at startup.
SECRET_KEY = env.str("SECRET_KEY")  # noqa: F405
if (len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5
        or SECRET_KEY.startswith(("django-insecure-", "dev-insecure-"))):
    raise ImproperlyConfigured("SECRET_KEY must be a strong production secret (50+ characters), not a development key.")
# Old keys that are still accepted for verifying signatures (sessions, CSRF) while a new SECRET_KEY rolls out.
# Empty normally. See "Rotating SECRET_KEY" in docs/DEPLOY_NOTES.md.
SECRET_KEY_FALLBACKS = env.list("SECRET_KEY_FALLBACKS", default=[])  # noqa: F405

# Ban-evasion hash key: required, long, and not the SECRET_KEY. A missing value stops the start (see DEPLOY_NOTES).
BAN_HASH_KEY = env.str("BAN_HASH_KEY")  # noqa: F405
if len(BAN_HASH_KEY) < 32 or BAN_HASH_KEY == SECRET_KEY or BAN_HASH_KEY.startswith("dev-insecure-"):
    raise ImproperlyConfigured(
        "BAN_HASH_KEY must be at least 32 characters and different from SECRET_KEY. "
        'Generate one: python -c "import secrets; print(secrets.token_urlsafe(50))"'
    )

# PostgreSQL: DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME
# Connections stay open for 60 s between requests (saves a reconnect per request); a dead one is detected
# and replaced before use (e.g. after a database restart).
DATABASES = {"default": {**env.db("DATABASE_URL"), "CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True}}  # noqa: F405

# Canonical public address (embed snippets, Open Graph, canonical links). Must be https.
from config import branding  # noqa: E402

SITE_URL = (SITE_URL or f"https://{branding.SITE_DOMAIN}").rstrip("/")  # noqa: F405
if not SITE_URL.startswith("https://"):
    raise ImproperlyConfigured(f"SITE_URL must start with https:// in production (got {SITE_URL!r}).")

ALLOWED_HOSTS = list(dict.fromkeys(["shipmark.org", "www.shipmark.org", *ALLOWED_HOSTS]))  # noqa: F405
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys([
    "https://shipmark.org", "https://www.shipmark.org", *CSRF_TRUSTED_ORIGINS,  # noqa: F405
]))

# The admin must not sit at the guessable /admin/. Set ADMIN_URL in the environment to something private.
if ADMIN_URL.lower() in ("", "admin/"):  # noqa: F405
    raise ImproperlyConfigured(
        'ADMIN_URL is missing or is "admin/". Set a private address in the environment, e.g. ADMIN_URL=staff-4f8k2/'
    )

# Heroku's filesystem is temporary. Refuse startup without durable upload storage.
# Explicit credentials prevent boto3 from trying instance metadata or unrelated credential files.
_s3_required = ("AWS_STORAGE_BUCKET_NAME", "AWS_S3_REGION_NAME", "AWS_S3_ENDPOINT_URL",
                "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
_s3_values = {name: env.str(name, default="").strip() for name in _s3_required}  # noqa: F405
_s3_missing = [name for name, value in _s3_values.items() if not value]
if _s3_missing:
    raise ImproperlyConfigured("Production S3 storage requires: " + ", ".join(_s3_missing))
_s3_endpoint = urlsplit(_s3_values["AWS_S3_ENDPOINT_URL"])
if (_s3_endpoint.scheme != "https" or not _s3_endpoint.hostname
        or _s3_endpoint.username or _s3_endpoint.password or _s3_endpoint.query or _s3_endpoint.fragment
        or _s3_endpoint.path not in ("", "/") or any(char.isspace() for char in _s3_endpoint.netloc)):
    raise ImproperlyConfigured("AWS_S3_ENDPOINT_URL must be an HTTPS origin without credentials, path or query.")
_s3_options = {
    "bucket_name": _s3_values["AWS_STORAGE_BUCKET_NAME"],
    "region_name": _s3_values["AWS_S3_REGION_NAME"],
    "endpoint_url": _s3_values["AWS_S3_ENDPOINT_URL"].rstrip("/"),
    "access_key": _s3_values["AWS_ACCESS_KEY_ID"],
    "secret_key": _s3_values["AWS_SECRET_ACCESS_KEY"],
    "addressing_style": "path",  # one exact HTTPS origin in CSP, including S3-compatible providers
    "signature_version": "s3v4",
    "default_acl": None,  # private bucket, no public policy; also supports providers with ACLs disabled
    "querystring_auth": True,
    "querystring_expire": 3600,
    "file_overwrite": False,
}
# Media URLs are signed. The bucket and both prefixes must deny anonymous access.
STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": {**_s3_options, "location": "media"}},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "support": {"BACKEND": "support.s3_storage.PrivateS3Storage", "OPTIONS": {**_s3_options, "location": "support"}},
}
CONTENT_SECURITY_POLICY = CONTENT_SECURITY_POLICY.replace(  # noqa: F405
    "img-src 'self' data:", f"img-src 'self' data: https://{_s3_endpoint.netloc}",
)
# SMTP for the support notification (base.py reads EMAIL_HOST etc. from env); the console backend is dev only.
EMAIL_BACKEND = env.str("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")  # noqa: F405

# HTTPS (the app runs behind a reverse proxy that sets X-Forwarded-Proto).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# HSTS: start with a short time (default 1 hour), raise it to 31536000 (1 year) once everything works over HTTPS.
# Do not submit the domain to hstspreload.org before that: preload is very hard to undo.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)  # noqa: F405
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)  # noqa: F405

# Rate limits (config/ratelimit.py) count in the cache. The default per-process memory cache would give every
# gunicorn worker its own counters, so the real limit would be limit x workers. The database cache is shared.
# One-time setup: python manage.py createcachetable
# MAX_ENTRIES is high on purpose: when the table is full Django deletes entries, and a deleted counter is a reset limit.
CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.db.DatabaseCache",
    "LOCATION": "django_cache",
    "OPTIONS": {"MAX_ENTRIES": 1_000_000, "CULL_FREQUENCY": 10},
}}

# Logs: one JSON object per line on stdout (config/jsonlog.py). The process manager (systemd, Docker, ...)
# collects stdout. LOG_LEVEL=DEBUG for more detail. Django itself logs 4xx/5xx requests and unhandled exceptions here.
# The error files (errors.jsonl, notfound.jsonl) go to LOG_DIR (default <project>/logs); see docs/DEPLOY_NOTES.md.
LOGGING = logging_config(env.str("LOG_LEVEL", default="INFO").upper(), log_dir=LOG_DIR)  # noqa: F405

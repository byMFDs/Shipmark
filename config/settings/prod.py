from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from config.jsonlog import logging_config

from .base import *  # noqa: F403

DEBUG = False

# Both are required in production: a missing value raises ImproperlyConfigured at startup.
SECRET_KEY = env.str("SECRET_KEY")  # noqa: F405
# Old keys that are still accepted for verifying signatures (sessions, CSRF) while a new SECRET_KEY rolls out.
# Empty normally. See "Rotating SECRET_KEY" in docs/DEPLOY_NOTES.md.
SECRET_KEY_FALLBACKS = env.list("SECRET_KEY_FALLBACKS", default=[])  # noqa: F405

# Ban-evasion hash key: required, long, and not the SECRET_KEY. A missing value stops the start (see DEPLOY_NOTES).
BAN_HASH_KEY = env.str("BAN_HASH_KEY")  # noqa: F405
if len(BAN_HASH_KEY) < 32 or BAN_HASH_KEY == SECRET_KEY:
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

# The admin must not sit at the guessable /admin/. Set ADMIN_URL in the environment to something private.
if ADMIN_URL.lower() in ("", "admin/"):  # noqa: F405
    raise ImproperlyConfigured(
        'ADMIN_URL is missing or is "admin/". Set a private address in the environment, e.g. ADMIN_URL=staff-4f8k2/'
    )

# Static files: `collectstatic` copies them to STATIC_ROOT (staticfiles/) with a content hash in the name
# (app.3f2a1c.css) plus .gz/.br copies. WhiteNoise serves them from there with far-future caching.
# A template that references a static file that does not exist fails loudly, which is what we want.
#
# Uploaded files (project screenshots) are written to MEDIA_ROOT on the server's own disk. The reverse proxy
# must serve MEDIA_URL (/media/) from that folder, and the folder must be included in backups.
# Moving to S3-compatible storage later (Backblaze B2, Cloudflare R2, Hetzner, MinIO, ...):
#   1. Allowed-dependency check: this needs `django-storages[s3]`, which is NOT in the CLAUDE.md list; decide first.
#   2. Change only STORAGES["default"] below (BACKEND "storages.backends.s3.S3Storage" + bucket options from env).
#      The code reads files through Django's storage API (image.url, storage.delete in projects/signals.py),
#      so no model or view changes are needed.
#   3. Add the bucket/CDN host to img-src in CONTENT_SECURITY_POLICY (base.py), or screenshots will be blocked.
#   4. Copy the existing media/ folder into the bucket once (same paths), then remove the /media/ proxy rule.
MEDIA_ROOT = Path(env.str("MEDIA_ROOT", default=str(BASE_DIR / "media")))  # noqa: F405
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

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

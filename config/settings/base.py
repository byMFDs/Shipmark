"""Settings shared by all environments. Values come from .env vars (see .env.example)."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Load .env if present. Real environment variables win over the file.
environ.Env.read_env(BASE_DIR / ".env")

# Empty here on purpose: dev.py supplies an insecure key, prod.py requires a real one.
SECRET_KEY = env.str("SECRET_KEY", default="")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # GitHub sign-in (django-allauth). No "sites" app: the host comes from the request.
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    # Local apps
    "accounts",
    "projects",
    "verification",
    "social",
    "pages",
    "moderation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Needs request.user, so it sits after auth. Safe because URLs have no language prefix.
    "config.middleware.UserLocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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
                "config.context_processors.brand",
            ],
        },
    },
]

# SQLite by default (dev). prod.py makes DATABASE_URL required (PostgreSQL).
DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}

AUTH_USER_MODEL = "accounts.User"

# ModelBackend stays for the admin (staff accounts made with createsuperuser).
# Everyone else signs in with GitHub only.
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "pages:landing"
LOGOUT_REDIRECT_URL = "pages:landing"

# Bump when the Terms change. Saved on the user at signup (terms_version_accepted).
TERMS_VERSION = "2026-11-10"

# --- django-allauth: GitHub is the only login method ---
GITHUB_CLIENT_ID = env.str("GITHUB_CLIENT_ID", default="")
GITHUB_CLIENT_SECRET = env.str("GITHUB_CLIENT_SECRET", default="")
GITHUB_OAUTH_CONFIGURED = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)

SOCIALACCOUNT_PROVIDERS = {
    "github": {
        # Only these two scopes. Never "repo" (CLAUDE.md section 6).
        "SCOPE": ["read:user", "user:email"],
        "APPS": (
            [{"client_id": GITHUB_CLIENT_ID, "secret": GITHUB_CLIENT_SECRET}]
            if GITHUB_OAUTH_CONFIGURED
            else []
        ),
    },
}
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
SOCIALACCOUNT_FORMS = {"signup": "accounts.forms.SignupConfirmForm"}
SOCIALACCOUNT_AUTO_SIGNUP = False  # always show the "confirm username + accept Terms" step
SOCIALACCOUNT_QUERY_EMAIL = True  # ask GitHub for the email list (private, never shown)
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False  # never log in to an old account just by matching email
SOCIALACCOUNT_STORE_TOKENS = False  # we do not keep GitHub access tokens
SOCIALACCOUNT_LOGIN_ON_GET = False  # starting OAuth needs a POST (CSRF-protected)
# "email" is listed only because allauth's social form requires it; our form removes the field.
ACCOUNT_SIGNUP_FIELDS = ["username*", "email"]
ACCOUNT_EMAIL_VERIFICATION = "none"  # GitHub already verified it
ACCOUNT_USERNAME_MIN_LENGTH = 3

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# i18n: English is the source language. Never add Russian (see CLAUDE.md section 8).
LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("uk", "Українська")]
LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
CONTENT_DIR = BASE_DIR / "content"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

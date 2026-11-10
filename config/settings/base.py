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
    # Admin theme. Must come before django.contrib.admin so its templates win.
    "unfold",
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
    # Asks for the new Terms after TERMS_VERSION is bumped. Needs request.user.
    "config.middleware.TermsAcceptanceMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

# Admin address, from env. Leading "/" is dropped, a trailing "/" is added. prod.py refuses "admin/".
ADMIN_URL = env.str("ADMIN_URL", default="admin/").strip().lstrip("/") or "admin/"
if ADMIN_URL and not ADMIN_URL.endswith("/"):
    ADMIN_URL += "/"

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

# Bump when the Terms change (use the date of the change). Saved on the user at signup
# (terms_version_accepted). After a bump every signed-in user is asked to accept again on their next visit
# (config.middleware.TermsAcceptanceMiddleware). Also update the date at the top of content/*/terms.md.
TERMS_VERSION = "2026-11-10"

# --- django-allauth: GitHub is the only login method ---
GITHUB_CLIENT_ID = env.str("GITHUB_CLIENT_ID", default="")
GITHUB_CLIENT_SECRET = env.str("GITHUB_CLIENT_SECRET", default="")
GITHUB_OAUTH_CONFIGURED = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)
# Optional server token for the repo check (public data only, no scopes). Raises GitHub's API
# limit from 60/hour per server IP to 5000/hour. We do not store users' own tokens.
GITHUB_API_TOKEN = env.str("GITHUB_API_TOKEN", default="")

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
LANGUAGES = [
    ("en", "English"),
    ("uk", "Українська"),
    ("pl", "Polski"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("fr", "Français"),
    ("pt-br", "Português (Brasil)"),
]
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

# --- Admin look (django-unfold). Name, logo and colors come from branding.py and tokens.css. ---
from config import branding  # noqa: E402
from django.templatetags.static import static  # noqa: E402
from django.urls import reverse_lazy  # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

UNFOLD = {
    "SITE_TITLE": branding.SITE_NAME,
    "SITE_HEADER": branding.SITE_NAME,
    "SITE_SUBHEADER": _("Admin"),
    "SITE_URL": "/",
    "SITE_ICON": lambda request: static(branding.LOGO_MARK),
    "SITE_LOGO": lambda request: static(branding.LOGO),
    "SITE_FAVICONS": [{"rel": "icon", "sizes": "any", "type": "image/svg+xml", "href": lambda request: static(branding.FAVICON)}],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "BORDER_RADIUS": "8px",  # controls (tokens: plates 10, controls 8)
    # Hallmark ink (#2A3FCF) is the only accent: primary-600 is the light-mode ink, primary-400 the dark-mode ink.
    # Base grays lean to Graphite (#1E2126 = base-900) and Steel (#666C74 = base-500).
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .003 258)", "100": "oklch(96% .004 258)", "200": "oklch(92% .005 258)",
            "300": "oklch(87% .007 258)", "400": "oklch(70% .012 258)", "500": "oklch(52.9% .015 256)",
            "600": "oklch(44% .014 258)", "700": "oklch(37% .012 259)", "800": "oklch(30% .011 260)",
            "900": "oklch(24.7% .01 261)", "950": "oklch(20.4% .007 258)",
        },
        "primary": {
            "50": "oklch(97% .012 268.6)", "100": "oklch(94% .03 268.6)", "200": "oklch(88% .06 268.6)",
            "300": "oklch(82% .09 268.6)", "400": "oklch(74.1% .11 268.6)", "500": "oklch(60% .17 268.6)",
            "600": "oklch(45.8% .22 268.6)", "700": "oklch(40% .2 268.6)", "800": "oklch(34% .16 268.6)",
            "900": "oklch(29% .12 268.6)", "950": "oklch(22% .09 268.6)",
        },
    },
    "DASHBOARD_CALLBACK": "moderation.dashboard.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Users"),
                "items": [
                    {"title": _("Users"), "icon": "person", "link": reverse_lazy("admin:accounts_user_changelist")},
                ],
            },
            {
                "title": _("Projects"),
                "items": [
                    {"title": _("Projects"), "icon": "deployed_code", "link": reverse_lazy("admin:projects_project_changelist")},
                    {"title": _("Build log"), "icon": "history_edu", "link": reverse_lazy("admin:projects_buildlogentry_changelist")},
                    {"title": _("Tags"), "icon": "sell", "link": reverse_lazy("admin:projects_tag_changelist")},
                    {"title": _("Tools"), "icon": "build", "link": reverse_lazy("admin:projects_tool_changelist")},
                ],
            },
            {
                "title": _("Verification"),
                "items": [
                    {"title": _("Repositories"), "icon": "code", "link": reverse_lazy("admin:verification_repolink_changelist")},
                    {"title": _("Domains"), "icon": "dns", "link": reverse_lazy("admin:verification_domainverification_changelist")},
                    {"title": _("Uptime checks"), "icon": "monitor_heart", "link": reverse_lazy("admin:verification_uptimecheck_changelist")},
                ],
            },
            {
                "title": _("Moderation"),
                "items": [
                    {"title": _("Reports"), "icon": "flag", "link": reverse_lazy("admin:moderation_report_changelist"),
                     "badge": "moderation.dashboard.open_reports_badge"},
                    {"title": _("Follows"), "icon": "group_add", "link": reverse_lazy("admin:social_follow_changelist")},
                    {"title": _("Likes"), "icon": "favorite", "link": reverse_lazy("admin:social_like_changelist")},
                ],
            },
            {
                "title": _("Audit log"),
                "items": [
                    {"title": _("Audit log"), "icon": "receipt_long", "link": reverse_lazy("admin:moderation_auditlog_changelist")},
                ],
            },
        ],
    },
}

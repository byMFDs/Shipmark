"""Settings shared by all environments. Values come from .env vars (see .env.example)."""
import sys
import tempfile
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
# The public address of the site, used for everything shared outside it (embed snippets, Open Graph, canonical
# links, data export): config/site.py. Scheme + host, no trailing slash. dev.py and prod.py set the defaults.
SITE_URL = env.str("SITE_URL", default="").rstrip("/")

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
    "news",
]

MIDDLEWARE = [
    # First: every response gets an X-Request-ID, and every error log line carries the same id.
    "config.middleware.RequestIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Before sessions and CSRF: a flood of admin login attempts is refused early.
    "config.middleware.AdminLoginThrottleMiddleware",
    "config.middleware.SecurityHeadersMiddleware",
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

# --- Browser security headers (HSTS and secure cookies are in prod.py) ---
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
# Templates have no inline scripts, styles or event handlers, so nothing needs 'unsafe-inline'.
# GitHub avatars are not shown (CLAUDE.md: no remote images). If uploads move to a CDN, add its host to img-src.
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
])
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"

ROOT_URLCONF = "config.urls"
# Error pages (config/errors.py; handler400/403/404/500 are set in config/urls.py). Never Django's debug pages
# when DEBUG is off.
CSRF_FAILURE_VIEW = "config.errors.csrf_failure"

# Error log files (config/errorlog.py): errors.jsonl and notfound.jsonl, 5 MB x 5 each. Read with
# `python manage.py show_errors`. Tests write to a temporary folder, never to the project.
TESTING = sys.argv[1:2] == ["test"]
LOG_DIR = Path(tempfile.mkdtemp(prefix="shipmark-test-logs-")) if TESTING else Path(env.str("LOG_DIR", default=str(BASE_DIR / "logs")))
from config.jsonlog import logging_config  # noqa: E402

# Development: only the files (Django's own console output stays as it is). prod.py adds JSON on stdout.
LOGGING = logging_config("WARNING", log_dir=LOG_DIR, stdout=False)
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

# ---------- Proof rules (verification/) ----------
# Repo owner: when the oldest commit is this many days older than the repository on GitHub, the
# history was most likely made elsewhere and pushed (an import, or a copy). It is not refused, it
# waits for a manual review. Working locally for a while before the first push is common, hence
# the wide margin. Commit dates are written by the author, so this only catches careless copies.
TRUST_IMPORTED_HISTORY_DAYS = 90

# Repo owner is checked again (repo id, owner id, visibility, facts) when the last check is this old.
# reverify_repos runs daily from cron, so the work is spread over the week.
TRUST_REVERIFY_REPOS_DAYS = 7
# GitHub computes contributor statistics in the background (202). Ask again after this many hours.
TRUST_STATS_RETRY_HOURS = 20

# Live: bare addresses of hosting services where each user gets a subdomain. Nobody "controls"
# github.io itself, so it is refused with a clear message (yourname.github.io is fine).
# Compared without "www.". A Public Suffix List would be complete, but it is a new dependency.
TRUST_SHARED_HOST_APEXES = frozenset({
    "github.io", "githubusercontent.com", "gitlab.io", "vercel.app", "now.sh", "netlify.app", "netlify.com",
    "pages.dev", "workers.dev", "herokuapp.com", "onrender.com", "fly.dev", "railway.app", "glitch.me",
    "replit.app", "repl.co", "web.app", "firebaseapp.com", "azurewebsites.net", "appspot.com",
    "surge.sh", "deno.dev", "bitbucket.io", "codeberg.page", "neocities.org", "blogspot.com",
    "wordpress.com", "framer.website", "webflow.io", "carrd.co", "lovable.app", "bolt.new",
})

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
    "SITE_ICON": {
        "light": lambda request: static(branding.LOGO_MARK),
        "dark": lambda request: static(branding.LOGO_MARK_DARK),
    },
    "SITE_LOGO": {
        "light": lambda request: static(branding.LOGO),
        "dark": lambda request: static(branding.LOGO_DARK),
    },
    "SITE_FAVICONS": [{"rel": "icon", "sizes": "any", "type": "image/svg+xml", "href": lambda request: static(branding.FAVICON)}],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "BORDER_RADIUS": "0px",  # square corners, as on the site (tokens.css --radius)
    # Same palette as static/css/tokens.css. primary = the terracotta action color (600 in light mode,
    # 400 in dark mode); base = the warm paper / green-black text scale, 900 = text, 950 = dark page.
    "COLORS": {
        "base": {
            "50": "oklch(97.3% .005 95.1)", "100": "oklch(94.5% .009 100)", "200": "oklch(88.1% .011 100.8)",
            "300": "oklch(80% .015 115.1)", "400": "oklch(62.7% .015 124.7)", "500": "oklch(49.1% .015 141.8)",
            "600": "oklch(42.6% .014 145.3)", "700": "oklch(36.6% .015 145.3)", "800": "oklch(31.1% .017 148.7)",
            "900": "oklch(25.7% .013 140.5)", "950": "oklch(21% .011 163.7)",
        },
        "primary": {
            "50": "oklch(96.6% .016 52.6)", "100": "oklch(92.4% .034 50.2)", "200": "oklch(85.2% .068 48.9)",
            "300": "oklch(77% .104 45.2)", "400": "oklch(72.1% .163 47.2)", "500": "oklch(63.7% .164 41.7)",
            "600": "oklch(56% .155 37.5)", "700": "oklch(49.4% .14 37.8)", "800": "oklch(41.8% .116 37.6)",
            "900": "oklch(34.4% .091 36.7)", "950": "oklch(26.6% .065 37.7)",
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
                    {"title": _("Badges"), "icon": "verified", "link": reverse_lazy("admin:accounts_userbadge_changelist")},
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
                    {"title": _("Review queue"), "icon": "fact_check", "link": reverse_lazy("admin:verification_reporeview_changelist"),
                     "badge": "verification.review.review_queue_badge"},
                    {"title": _("Repositories"), "icon": "code", "link": reverse_lazy("admin:verification_repolink_changelist")},
                    {"title": _("Domains"), "icon": "dns", "link": reverse_lazy("admin:verification_domainverification_changelist")},
                    {"title": _("Uptime checks"), "icon": "monitor_heart", "link": reverse_lazy("admin:verification_uptimecheck_changelist")},
                    {"title": _("Blocked repos and domains"), "icon": "block", "link": reverse_lazy("admin:verification_block_changelist")},
                ],
            },
            {
                "title": _("Moderation"),
                "items": [
                    {"title": _("Reports"), "icon": "flag", "link": reverse_lazy("admin:moderation_report_changelist"),
                     "badge": "moderation.dashboard.open_reports_badge"},
                    {"title": _("Sanctions"), "icon": "gavel", "link": reverse_lazy("admin:moderation_sanction_changelist")},
                    {"title": _("Follows"), "icon": "group_add", "link": reverse_lazy("admin:social_follow_changelist")},
                    {"title": _("Likes"), "icon": "favorite", "link": reverse_lazy("admin:social_like_changelist")},
                ],
            },
            {
                "title": _("News"),
                "items": [
                    {"title": _("News posts"), "icon": "campaign", "link": reverse_lazy("admin:news_newspost_changelist")},
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

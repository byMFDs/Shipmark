"""Спільні налаштування всіх середовищ; значення з .env.

Settings shared by all environments. Values come from .env vars (see .env.example)."""
import sys
import tempfile
from datetime import timedelta
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
    # Always installed (its tables exist either way); COMMUNITY_ENABLED below decides whether anyone can reach it.
    "community",
    "support",
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
    # A ban ends the session and shows the ban page (expiry checked here, per request). Needs request.user.
    "moderation.middleware.BanMiddleware",
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
                "moderation.context_processors.account",
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
TERMS_VERSION = "2026-11-13"

# Moderation (/mod/). Moderators (moderator badge) stay within these limits; superusers have none and are the
# only ones who issue permanent sanctions, revoke, restore and purge. Every action needs a reason the user sees.
MODERATION_MAX_MUTE = timedelta(days=7)
MODERATION_MAX_BAN = timedelta(days=14)
MODERATION_ACTIONS_PER_HOUR = 30  # per moderator

# Community (/community/): threads, replies, images, upvotes. Off: every community route is a 404, no link is
# shown and no community code runs (data export and account deletion still cover rows that already exist).
# Off by default; dev.py turns it on. Production: leave it off until moderators are ready (docs/COMMUNITY_PLAN.md).
COMMUNITY_ENABLED = env.bool("COMMUNITY_ENABLED", default=False)

# "<n> people joined" in the header (pages/stats.py). Hidden while the number is not above PUBLIC_USER_COUNT_MIN,
# so a young site can wait until the number means something. Off in the test run (an extra query once a minute
# would make the exact query-count tests of other pages depend on the cache); the counter's own tests switch it on.
PUBLIC_USER_COUNT_MIN = env.int("PUBLIC_USER_COUNT_MIN", default=0)
PUBLIC_USER_COUNT_ENABLED = not TESTING

# Secret for the ban-evasion hash of a GitHub id (moderation/bans.py). Its own key, not SECRET_KEY, so rotating
# SECRET_KEY cannot free banned people. Production requires it (prod.py); dev.py fills in an insecure default.
# Never rotate it while a ban is active: the hashes cannot be recomputed (the GitHub ids are not stored).
BAN_HASH_KEY = env.str("BAN_HASH_KEY", default="")

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

# Support attachments: a PRIVATE folder, never under MEDIA_ROOT and never served by URL (support/storage.py).
# Staff download them through an authenticated view. To use a private S3 prefix instead, change only
# STORAGES["support"] (docs/DEPLOY_NOTES.md).
SUPPORT_ROOT = (Path(tempfile.mkdtemp(prefix="shipmark-test-support-")) if TESTING
                else Path(env.str("SUPPORT_ROOT", default=str(BASE_DIR / "private" / "support"))))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "support": {"BACKEND": "support.storage.PrivateStorage"},
}

# Email: only the notification to the support inbox is sent (support/notify.py); nobody else gets email.
# Development prints it in the terminal; production sets SMTP in .env (docs/DEPLOY_NOTES.md, Gmail steps).
EMAIL_BACKEND = env.str("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env.str("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="") or EMAIL_HOST_USER or "webmaster@localhost"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
# Where new support messages are announced. Empty: no email, messages wait in the admin inbox.
SUPPORT_INBOX_EMAIL = env.str("SUPPORT_INBOX_EMAIL", default="")
# The request header that holds the visitor's address as the reverse proxy sets it (for example HTTP_X_REAL_IP with
# nginx `proxy_set_header X-Real-IP $remote_addr;`). Empty: REMOTE_ADDR. Used only for the salted, cache-only hash
# of the support form's rate limit; never stored.
CLIENT_IP_HEADER = env.str("CLIENT_IP_HEADER", default="")

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
    # Palette-only admin styles; no behaviour or template changes.
    "STYLES": [lambda request: static("css/admin-palette.css")],
    "COLORS": {
        "base": {
            "50": "#F3F6F7",
            "100": "#F3F6F7",
            "200": "#F3F6F7",
            "300": "#B1B9BA",
            "400": "#B1B9BA",
            "500": "#20383A",
            "600": "#20383A",
            "700": "#20383A",
            "800": "#233638",
            "900": "#15292B",
            "950": "#071C1E",
        },
        "primary": {
            "50": "#C7F36B",
            "100": "#C7F36B",
            "200": "#79D9D2",
            "300": "#79D9D2",
            "400": "#79D9D2",
            "500": "#20383A",
            "600": "#20383A",
            "700": "#071C1E",
            "800": "#071C1E",
            "900": "#071C1E",
            "950": "#071C1E",
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
                    {"title": _("Removed projects"), "icon": "delete_sweep",
                     "link": reverse_lazy("admin:projects_project_changelist", query={"status__exact": "removed"})},
                    {"title": _("Notices"), "icon": "notifications", "link": reverse_lazy("admin:moderation_notice_changelist")},
                    {"title": _("Follows"), "icon": "group_add", "link": reverse_lazy("admin:social_follow_changelist")},
                    {"title": _("Likes"), "icon": "favorite", "link": reverse_lazy("admin:social_like_changelist")},
                ],
            },
            {
                "title": _("Community"),
                "items": [
                    {"title": _("Boards"), "icon": "forum", "link": reverse_lazy("admin:community_board_changelist")},
                    {"title": _("Threads"), "icon": "chat", "link": reverse_lazy("admin:community_thread_changelist")},
                    {"title": _("Replies"), "icon": "reply", "link": reverse_lazy("admin:community_reply_changelist")},
                    {"title": _("Images"), "icon": "image", "link": reverse_lazy("admin:community_communityimage_changelist")},
                ],
            },
            {
                "title": _("Support"),
                "items": [
                    {"title": _("Inbox"), "icon": "mail", "link": reverse_lazy("admin:support_supportmessage_changelist"),
                     "badge": "support.admin.unread_badge", "permission": "support.admin.can_view_inbox"},
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

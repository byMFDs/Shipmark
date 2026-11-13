from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from config.context_processors import brand


class SettingsTests(SimpleTestCase):
    def test_settings_load(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")
        self.assertEqual(settings.ROOT_URLCONF, "config.urls")
        self.assertEqual(settings.LANGUAGE_CODE, "en")
        self.assertNotIn("ru", [code for code, _ in settings.LANGUAGES])

    def test_all_local_apps_registered(self):
        for app in ("accounts", "projects", "verification", "social", "pages", "moderation"):
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_brand_context_processor(self):
        context = brand(RequestFactory().get("/"))
        self.assertEqual(context["brand"].SITE_NAME, "Shipmark")
        self.assertTrue(hasattr(context["brand"], "CONTACT_EMAIL"))


class UserModelTests(TestCase):
    def test_custom_user_has_profile_fields(self):
        user = get_user_model().objects.create_user("danylo", password="x" * 12)
        self.assertFalse(user.is_suspended)
        self.assertEqual(user.github_login, "")

    def test_github_login_unique_only_when_set(self):
        User = get_user_model()
        User.objects.create_user("a")
        User.objects.create_user("b")  # both empty: allowed
        User.objects.create_user("c", github_login="octocat")
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user("d", github_login="octocat")


# ---------- Security headers and production settings (task 19) ----------

import os
import re
import subprocess
import sys
from pathlib import Path

from django.core.cache import cache
from django.test import Client, override_settings
from django.urls import reverse

from accounts.models import User
from projects.models import Project


class SecurityHeadersTests(TestCase):
    def test_pages_send_csp_without_unsafe_inline(self):
        for url in ("/", "/explore/", "/login/", "/legal/privacy/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                policy = response["Content-Security-Policy"]
                self.assertIn("script-src 'self'", policy)
                self.assertIn("frame-ancestors 'none'", policy)
                self.assertNotIn("unsafe-inline", policy)
                self.assertNotIn("unsafe-eval", policy)
                self.assertIn("camera=()", response["Permissions-Policy"])
                self.assertEqual(response["X-Frame-Options"], "DENY")

    def test_pages_have_no_inline_scripts_styles_or_handlers(self):
        ana = User.objects.create(username="ana")
        Project.objects.create(owner=ana, name="Tool", slug="tool", tagline="t", status=Project.Status.PUBLISHED)
        self.client.force_login(ana)
        for url in ("/", "/explore/", "/login/", "/legal/privacy/", "/u/ana/", "/u/ana/tool/", "/u/ana/tool/edit/",
                    "/settings/", "/new/", "/feed/"):
            with self.subTest(url=url):
                html = self.client.get(url, follow=True).content.decode()
                self.assertFalse(re.search(r"<script(?![^>]*\ssrc=)", html), "inline <script>")
                self.assertNotIn("<style", html)
                self.assertFalse(re.search(r"\sstyle\s*=", html), "style attribute")
                self.assertFalse(re.search(r"\son[a-z]+\s*=", html, re.I), "inline event handler")
                self.assertNotIn("javascript:", html)

    def test_admin_is_not_given_the_page_csp(self):
        response = self.client.get(reverse("admin:login"))
        self.assertNotIn("Content-Security-Policy", response)

    def test_badge_keeps_its_own_stricter_csp(self):
        response = self.client.get("/badge/nobody.svg")
        self.assertIn("sandbox", response["Content-Security-Policy"])

    def test_no_email_address_in_public_html(self):
        User.objects.create(username="ana", email="ana-private@example.com")
        for url in ("/u/ana/", "/explore/", "/"):
            self.assertNotIn("ana-private@example.com", self.client.get(url).content.decode())


class AdminLoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_eleventh_attempt_in_the_window_is_refused(self):
        url = reverse("admin:login")
        for _attempt in range(10):
            self.assertNotEqual(self.client.post(url, {"username": "Boss", "password": "x"}).status_code, 429)
        self.assertEqual(self.client.post(url, {"username": "boss", "password": "x"}).status_code, 429)  # case ignored
        self.assertNotEqual(self.client.post(url, {"username": "other", "password": "x"}).status_code, 429)

    def test_only_login_posts_are_counted(self):
        url = reverse("admin:login")
        for _attempt in range(15):
            self.assertEqual(self.client.get(url).status_code, 200)


PROD_SECRET = "tést-only-" + "abcdefghijklmnopqrstuvwxyz0123456789" * 2  # module level: other test classes borrow _manage


class ProductionSettingsTests(SimpleTestCase):
    def _manage(self, *args, **extra):
        env = {k: v for k, v in os.environ.items() if k not in ("ADMIN_URL", "DEBUG")}
        env.update({"DJANGO_SETTINGS_MODULE": "config.settings.prod", "SECRET_KEY": PROD_SECRET,
                    "BAN_HASH_KEY": "ban-only-" + "zyxwvutsrqponmlkjihgfedcba9876543210" * 2,
                    "DATABASE_URL": "sqlite:////tmp/unused.sqlite3", "ADMIN_URL": "staff-4f8k2/",
                    "ALLOWED_HOSTS": "example.com", "LOG_DIR": str(settings.LOG_DIR), **extra})
        env = {k: v for k, v in env.items() if v is not None}  # a None value removes the variable
        return subprocess.run([sys.executable, "manage.py", *args], cwd=Path(settings.BASE_DIR), env=env,
                              capture_output=True, text=True)

    def test_check_deploy_has_no_warnings(self):
        result = self._manage("check", "--deploy")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no issues", result.stdout + result.stderr)

    def test_production_refuses_to_start_without_a_proper_ban_hash_key(self):
        cases = {"missing": None, "empty": "", "too short": "short-key", "same as SECRET_KEY": PROD_SECRET}
        for label, value in cases.items():
            result = self._manage("check", BAN_HASH_KEY=value)
            self.assertNotEqual(result.returncode, 0, label)
            self.assertIn("BAN_HASH_KEY", result.stderr, label)
        ok = self._manage("shell", "-c", "from django.conf import settings as s; print(len(s.BAN_HASH_KEY))")
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_debug_cannot_be_switched_on_in_production(self):
        result = self._manage("shell", "-c", "from django.conf import settings; print('DEBUG=%s' % settings.DEBUG)", DEBUG="true")
        self.assertIn("DEBUG=False", result.stdout)

    def test_rate_limits_use_a_cache_shared_between_workers(self):
        result = self._manage("shell", "-c", "from django.conf import settings; print(settings.CACHES['default']['BACKEND'])")
        self.assertIn("DatabaseCache", result.stdout)


class JsonLoggingTests(SimpleTestCase):
    def test_record_is_one_json_line_and_path_text_cannot_forge_fields(self):
        import json
        import logging

        from config.jsonlog import JsonFormatter

        evil = 'GET /x"}\n{"level": "CRITICAL", "message": "forged'
        record = logging.LogRecord("gunicorn.access", logging.INFO, "f.py", 1, "%s", (evil,), None)
        line = JsonFormatter().format(record)
        self.assertNotIn("\n", line)
        data = json.loads(line)
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], evil)

    def test_exception_is_included(self):
        import json
        import logging
        import sys

        from config.jsonlog import JsonFormatter

        try:
            1 / 0
        except ZeroDivisionError:
            record = logging.LogRecord("app", logging.ERROR, "f.py", 1, "boom", (), sys.exc_info())
        data = json.loads(JsonFormatter().format(record))
        self.assertIn("ZeroDivisionError", data["exception"])

    def test_production_logs_json_to_stdout_and_keeps_db_connections_open(self):
        result = ProductionSettingsTests._manage(
            self, "shell", "-c",
            "import logging.config; from django.conf import settings as s; "
            "print(s.LOGGING['handlers']['stdout']['stream'], s.DATABASES['default']['CONN_MAX_AGE'], s.DATABASES['default']['CONN_HEALTH_CHECKS'])",
        )
        self.assertIn("ext://sys.stdout 60 True", result.stdout, result.stderr)

    def test_secret_key_fallbacks_come_from_env(self):
        result = ProductionSettingsTests._manage(
            self, "shell", "-c", "from django.conf import settings as s; print(s.SECRET_KEY_FALLBACKS)",
            SECRET_KEY_FALLBACKS="old-one,older-one",
        )
        self.assertIn("['old-one', 'older-one']", result.stdout, result.stderr)


# ---------- Local development: one origin, no stale static files (redesign phase 1 fixes) ----------

class LocalhostRedirectTests(TestCase):
    def test_middleware_is_on_in_dev_settings(self):
        self.assertEqual(settings.MIDDLEWARE[0], "config.middleware.LocalhostRedirectMiddleware")

    @override_settings(DEBUG=True)
    def test_127_0_0_1_redirects_to_localhost_with_path_and_query(self):
        response = Client().get("/explore/?q=a%20b&sort=new", HTTP_HOST="127.0.0.1:8000")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://localhost:8000/explore/?q=a%20b&sort=new")

    @override_settings(DEBUG=True)
    def test_static_files_redirect_too(self):
        response = Client().get("/static/css/tokens.css", HTTP_HOST="127.0.0.1:8000")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://localhost:8000/static/css/tokens.css")

    @override_settings(DEBUG=True)
    def test_localhost_and_lookalike_hosts_are_not_redirected(self):
        for host in ("localhost:8000", "127.0.0.10:8000", "127.0.0.1.evil.test"):
            response = Client().get("/static/css/tokens.css", HTTP_HOST=host)
            self.assertNotEqual(response.status_code, 302, host)

    def test_no_redirect_when_debug_is_off(self):
        response = Client().get("/", HTTP_HOST="127.0.0.1:8000")
        self.assertNotEqual(response.status_code, 302)

    @override_settings(DEBUG=True)
    def test_static_files_are_not_cached_in_debug(self):
        response = Client().get("/static/css/tokens.css", HTTP_HOST="localhost:8000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-cache")

    def test_production_settings_have_neither(self):
        result = ProductionSettingsTests._manage(
            self, "shell", "-c",
            "from django.conf import settings as s; "
            "print('LR' in str(s.MIDDLEWARE).replace('LocalhostRedirect', 'LR'), 'runserver_nostatic' in s.INSTALLED_APPS, "
            "hasattr(s, 'WHITENOISE_ADD_HEADERS_FUNCTION'))",
        )
        self.assertIn("False False False", result.stdout, result.stderr)


class ErrorPageTests(TestCase):
    """The styled error pages render: 404 and 403 inside the site, 500, 400 and CSRF failure without any request context."""

    def test_404_is_the_styled_page(self):
        with override_settings(DEBUG=False):
            response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, 'class="site-header', status_code=404)

    def test_standalone_pages_need_no_context(self):
        for name in ("500", "400", "403_csrf"):
            html = render_to_string(f"{name}.html")
            self.assertIn("error-page", html, name)
            self.assertNotIn("<main id=", html, name)  # no site header, session or database needed

    def test_403_renders_in_the_site(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        html = render_to_string("403.html", request=request)
        self.assertIn("You cannot open this page", html)

"""Error pages, request ids and the JSON error log (config/errors.py, config/errorlog.py).

Runs with DEBUG=False, as in production. This module is also the URLconf of the tests (ROOT_URLCONF):
the real URLs plus a few views that fail on purpose.
"""
import io
import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import path

from config import urls as real_urls
from config.errorlog import ERRORS_FILE, NOTFOUND_FILE, NotFoundFilter, scrub

SECRET = "sk_live_7f3a9c2e5b1d4f8a6c0e9b2d7a5f3c1e"


def boom(request):
    raise RuntimeError(f"database password={SECRET} for alice@example.com from 203.0.113.9")


def forbidden(request):
    raise PermissionDenied


urlpatterns = [
    path("_test/boom/", boom, name="test_boom"),
    path("_test/forbidden/", forbidden, name="test_forbidden"),
    *real_urls.urlpatterns,
]
handler400 = real_urls.handler400
handler403 = real_urls.handler403
handler404 = real_urls.handler404
handler500 = real_urls.handler500

DEBUG_LEAKS = ("Traceback", "You're seeing this error", "DEBUG = True", "technical_500", "Django tried these URL patterns",
               "RuntimeError", SECRET, "settings.py", "Request Method")


def log_lines(name):
    file = settings.LOG_DIR / name
    if not file.is_file():
        return []
    return [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]


def clear_logs():
    for name in (ERRORS_FILE, NOTFOUND_FILE):
        file = settings.LOG_DIR / name
        if file.exists():
            file.write_text("")  # the handler appends, so it keeps writing at the new end
    NotFoundFilter.reset()


@override_settings(DEBUG=False, ROOT_URLCONF="config.test_errors")
class ErrorPagesTests(TestCase):
    def setUp(self):
        clear_logs()
        self.client = Client(raise_request_exception=False)

    def assertNoLeaks(self, response):
        html = response.content.decode()
        for text in DEBUG_LEAKS:
            self.assertNotIn(text, html)

    def test_500_is_the_custom_page_with_a_reference_and_no_debug_info(self):
        response = self.client.get("/_test/boom/?token=abc")
        self.assertEqual(response.status_code, 500)
        html = response.content.decode()
        self.assertIn("Something broke on our side", html)
        self.assertIn('class="error-page__code"', html)
        self.assertIn(f"Reference: <span class=\"numeric\">{response['X-Request-ID']}</span>", html)
        self.assertNotIn('class="site-header', html)  # standalone: no menu, no session, no database
        self.assertNotIn("{#", html)  # template comments never leak
        self.assertNoLeaks(response)

    def test_404_is_the_custom_page_not_the_url_list(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, 'class="site-header', status_code=404)
        self.assertNoLeaks(response)

    def test_403_shows_a_reference(self):
        response = self.client.get("/_test/forbidden/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You cannot open this page", status_code=403)
        self.assertContains(response, response["X-Request-ID"], status_code=403)
        self.assertNoLeaks(response)

    def test_csrf_failure_is_the_custom_page(self):
        response = Client(enforce_csrf_checks=True).post("/i18n/set-language/", {"language": "uk"})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "This form has expired", status_code=403)
        self.assertContains(response, response["X-Request-ID"], status_code=403)
        self.assertNotContains(response, "CSRF cookie", status_code=403)  # the reason is logged, not shown
        self.assertNoLeaks(response)

    def test_400_for_a_bad_host_is_the_custom_page(self):
        response = self.client.get("/", HTTP_HOST="evil.test")
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Something was wrong with that request", status_code=400)
        self.assertNotContains(response, "ALLOWED_HOSTS", status_code=400)

    def test_error_pages_are_translated(self):
        response = self.client.get("/no-such-page/", headers={"Accept-Language": "uk"})
        self.assertNotContains(response, "Page not found", status_code=404)
        response = self.client.get("/_test/boom/", headers={"Accept-Language": "uk"})
        self.assertIn('lang="uk"', response.content.decode())
        self.assertNotIn("Something broke on our side", response.content.decode())

    def test_back_link_only_to_this_site(self):
        html = self.client.get("/no-such-page/", HTTP_REFERER="http://testserver/explore/").content.decode()
        self.assertIn('href="http://testserver/explore/" data-back', html)
        html = self.client.get("/no-such-page/", HTTP_REFERER="https://evil.test/").content.decode()
        self.assertNotIn("evil.test", html)

    def test_every_response_has_a_short_random_request_id(self):
        first, second = self.client.get("/"), self.client.get("/")
        self.assertRegex(first["X-Request-ID"], r"^[0-9a-f]{8}$")
        self.assertNotEqual(first["X-Request-ID"], second["X-Request-ID"])

    def test_previews_exist_only_in_debug(self):
        self.assertEqual(self.client.get("/_dev/errors/500/").status_code, 404)
        with override_settings(DEBUG=True):
            for code, text in [("400", "Something was wrong with that request"), ("403", "You cannot open this page"), ("404", "Page not found"),
                               ("500", "Something broke"), ("csrf", "This form has expired")]:
                with self.subTest(code=code):
                    self.assertContains(self.client.get(f"/_dev/errors/{code}/"), text)
            self.assertContains(self.client.get("/styleguide/"), "/_dev/errors/csrf/")
        self.assertEqual(log_lines(ERRORS_FILE), [])  # previews are not errors


@override_settings(DEBUG=False, ROOT_URLCONF="config.test_errors")
class ErrorLogTests(TestCase):
    def setUp(self):
        clear_logs()
        self.client = Client(raise_request_exception=False)

    def test_unhandled_exception_is_one_json_line_with_the_listed_fields(self):
        response = self.client.get("/_test/boom/?token=abc")
        [line] = log_lines(ERRORS_FILE)
        self.assertEqual(set(line), {"timestamp", "level", "request_id", "method", "path", "status", "view",
                                     "exception", "message", "traceback"})
        self.assertEqual(line["request_id"], response["X-Request-ID"])
        self.assertEqual((line["level"], line["method"], line["path"], line["status"]), ("ERROR", "GET", "/_test/boom/", 500))
        self.assertEqual(line["view"], "test_boom")
        self.assertEqual(line["exception"], "RuntimeError")
        self.assertIn("in boom", line["traceback"])
        self.assertEqual(log_lines(NOTFOUND_FILE), [])

    def test_private_data_is_never_written(self):
        self.client.get(
            f"/_test/boom/?token={SECRET}&email=bob@example.com&code=oauthcode123",
            HTTP_USER_AGENT="SecretBrowser/9.9", REMOTE_ADDR="198.51.100.7", HTTP_COOKIE="sessionid=cookievalue42",
            HTTP_AUTHORIZATION=f"Bearer {SECRET}",
        )
        self.client.get(f"/missing/?token={SECRET}", REMOTE_ADDR="198.51.100.7", HTTP_USER_AGENT="SecretBrowser/9.9")
        written = "".join((settings.LOG_DIR / name).read_text() for name in (ERRORS_FILE, NOTFOUND_FILE))
        self.assertTrue(written)
        for private in (SECRET, "bob@example.com", "alice@example.com", "oauthcode123", "SecretBrowser", "198.51.100.7",
                        "203.0.113.9", "cookievalue42", "token=", "&email"):
            self.assertNotIn(private, written)
        self.assertIn("password=[redacted]", written)

    def test_usernames_in_paths_are_masked(self):
        self.client.get("/u/alice/secret-project/")
        [line] = log_lines(NOTFOUND_FILE)
        self.assertEqual(line["path"], "/u/[user]/secret-project/")

    def test_404s_go_to_their_own_file_once_per_minute_per_path(self):
        for _ in range(3):
            self.client.get("/wp-login.php")
        self.client.get("/.env")
        self.assertEqual([line["path"] for line in log_lines(NOTFOUND_FILE)], ["/wp-login.php", "/.env"])
        self.assertEqual(set(log_lines(NOTFOUND_FILE)[0]), {"timestamp", "level", "request_id", "method", "path", "status"})
        self.assertEqual(log_lines(ERRORS_FILE), [])

    def test_403_and_csrf_failures_are_logged(self):
        self.client.get("/_test/forbidden/")
        Client(enforce_csrf_checks=True).post("/i18n/set-language/", {"language": "uk"})
        lines = log_lines(ERRORS_FILE)
        self.assertEqual([line["status"] for line in lines], [403, 403])
        self.assertIn("CSRF", lines[1]["message"])

    def test_ordinary_responses_and_400s_are_not_logged(self):
        self.client.get("/")
        self.client.get("/", HTTP_HOST="evil.test")
        self.assertEqual(log_lines(ERRORS_FILE), [])

    def test_errors_outside_a_request_are_logged(self):
        logging.getLogger("verification").error("cron failed for https://x.test/?key=1")
        [line] = log_lines(ERRORS_FILE)
        self.assertEqual((line["request_id"], line["path"]), ("", ""))
        self.assertNotIn("key=1", line["message"])


class ScrubTests(SimpleTestCase):
    def test_scrub(self):
        cases = {
            "SECRET_KEY = 'abc123def'": "SECRET_KEY = '[redacted]'",
            "Authorization: Bearer abcdefghijklmnop": "Authorization: [redacted] [redacted]",
            "token ghp_abcdefghijklmnopqrstuvwxyz0123": "token [redacted]",
            "mail me@x.org now": "mail [email] now",
            "from 10.0.0.1 and 2001:db8::1": "from [ip] and [ip]",
            "GET /a/?q=x&page=2": "GET /a/?[query removed]",
            "opened /u/olena/app/": "opened /u/[user]/app/",
            "at 12:30:45 ok": "at 12:30:45 ok",
        }
        for raw, want in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(scrub(raw), want)


class ShowErrorsCommandTests(SimpleTestCase):
    def setUp(self):
        clear_logs()

    def write(self, name, records):
        with (settings.LOG_DIR / name).open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record) + "\n")

    def run_command(self, *args):
        out = io.StringIO()
        call_command("show_errors", *args, stdout=out, no_color=True)
        return out.getvalue()

    def test_groups_by_exception_and_summarises(self):
        base = {"level": "ERROR", "method": "GET", "status": 500, "view": "v", "message": "m", "traceback": "Traceback..."}
        self.write(ERRORS_FILE, [
            {**base, "timestamp": "2026-11-11T10:00:00", "path": "/a/", "exception": "KeyError", "request_id": "aaaa1111"},
            {**base, "timestamp": "2026-11-11T10:01:00", "path": "/b/", "exception": "ValueError", "request_id": "bbbb2222"},
            {**base, "timestamp": "2026-11-11T10:02:00", "path": "/a/", "exception": "KeyError", "request_id": "cccc3333"},
            "not a record",
        ])
        (settings.LOG_DIR / ERRORS_FILE).open("a").write("{broken json\n")
        recent = self.run_command("--last", "20")
        self.assertIn("KeyError  ×2", recent)
        self.assertIn("ref=cccc3333", recent)
        self.assertLess(recent.index("KeyError"), recent.index("ValueError"))  # newest group first
        summary = self.run_command("--summary")
        self.assertIn("2  KeyError", summary)
        self.assertIn("/a/ ×2", summary)
        self.assertIn("Traceback...", self.run_command("--full"))

    def test_empty_log_and_notfound(self):
        self.assertIn("No errors logged", self.run_command())
        self.write(NOTFOUND_FILE, [{"timestamp": "2026-11-11T10:00:00", "path": "/x/"}, {"timestamp": "2026-11-11T10:05:00", "path": "/x/"}])
        self.assertIn("2  /x/", self.run_command("--notfound"))


class ProductionErrorSettingsTests(SimpleTestCase):
    def test_production_forces_debug_off_and_uses_the_custom_views(self):
        from config.tests import ProductionSettingsTests

        result = ProductionSettingsTests._manage(
            self, "shell", "-c",
            "from django.conf import settings as s; from django.urls import get_resolver as r; "
            "print(s.DEBUG, s.CSRF_FAILURE_VIEW, [r().resolve_error_handler(c).__name__ for c in (400, 403, 404, 500)], "
            "sorted(s.LOGGING['handlers']))",
            DEBUG="1",
        )
        self.assertIn(
            "False config.errors.csrf_failure ['bad_request', 'permission_denied', 'page_not_found', 'server_error'] "
            "['errors_file', 'notfound_file', 'stdout']",
            result.stdout, result.stderr,
        )

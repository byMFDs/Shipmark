"""Регресії приватності журналів і CSRF для маршрутів із записом даних."""
import json
import logging
import sys

from django.conf import settings
from django.test import Client, RequestFactory, SimpleTestCase, TestCase

from accounts.models import User
from config.errorlog import ErrorJsonFormatter
from config.jsonlog import JsonFormatter


class LogPrivacyTests(SimpleTestCase):
    """IP, адреси, облікові ключі й імена в маршрутах не потрапляють у власні журнали."""

    def test_stdout_scrubs_access_messages_and_exceptions(self):
        secret = "sample-secret-value"
        text = f"GET /report/user/privateperson/ from 198.51.100.23 2001:db8::1 mail private@example.invalid token={secret}"
        try:
            raise ValueError(text)
        except ValueError:
            record = logging.LogRecord("gunicorn.access", logging.ERROR, "test.py", 1, "%s", (text,), sys.exc_info())
        data = json.loads(JsonFormatter().format(record))
        for private in ("privateperson", "198.51.100.23", "2001:db8::1", "private@example.invalid", secret):
            self.assertNotIn(private, data["message"])
            self.assertNotIn(private, data["exception"])
        self.assertIn("ValueError", data["exception"])

    def test_file_log_paths_are_scrubbed_for_every_username_route_and_raw_ip(self):
        for path in ("/follow/privateperson/", "/report/user/privateperson/", "/report/project/privateperson/app/",
                     "/report/log/privateperson/app/1/", "/mod/act/user/privateperson/", "/missing/198.51.100.23/"):
            with self.subTest(path=path):
                request = RequestFactory().get(path)
                record = logging.LogRecord("django.request", logging.WARNING, "test.py", 1, "Not Found: %s", (path,), None)
                record.request = request
                record.status_code = 404
                data = json.loads(ErrorJsonFormatter().format(record))
                self.assertNotIn("privateperson", data["path"])
                self.assertNotIn("198.51.100.23", data["path"])
                self.assertNotIn("privateperson", data["message"])


class WriteCsrfTests(TestCase):
    """POST без CSRF відхиляється до виконання кожної групи дій."""

    def test_write_endpoints_require_csrf_even_for_a_signed_in_user(self):
        user = User.objects.create_user("csrf-audit", terms_version_accepted=settings.TERMS_VERSION)
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        paths = ["/settings/", "/settings/export/", "/settings/delete/", "/terms/accept/", "/logout/",
                 "/i18n/set-language/", "/support/", "/new/", "/new/preview/", "/follow/another/",
                 "/unfollow/another/", "/like/another/app/", "/unlike/another/app/", "/signup/",
                 "/accounts/github/login/", "/report/project/another/app/", "/report/user/another/",
                 "/report/log/another/app/1/", "/report/thread/1/", "/report/reply/1/", "/community/new/",
                 "/notices/1/dismiss/", f"/{settings.ADMIN_URL}login/"]
        paths += [f"/u/another/app/{action}/" for action in (
            "edit", "publish", "unpublish", "delete", "repo/check", "domain/verify", "screenshots/add",
            "screenshots/1/delete", "screenshots/1/move", "log/add", "log/1/delete",
        )]
        paths += [f"/community/{kind}/1/{action}/" for kind, actions in (
            ("t", ("edit", "delete", "reply", "vote")), ("r", ("edit", "delete", "vote")),
        ) for action in actions]
        paths += [f"/mod/act/{kind}/1/" for kind in ("project", "log", "thread", "reply")]
        paths += ["/mod/act/user/another/", "/mod/reports/1/"]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(client.post(path, {}).status_code, 403)

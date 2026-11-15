"""Перевіряє Heroku startup, приватне S3 та незмінні dev-сховища без мережі."""
import json
import os
from pathlib import Path
import runpy
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.test import SimpleTestCase


class HerokuSettingsTests(SimpleTestCase):
    """Production вимагає стійке сховище, а локальна розробка лишається локальною."""

    def probe(self, code="from config.wsgi import application; print('ready')", **env):
        from config.tests import ProductionSettingsTests

        return ProductionSettingsTests._manage(self, "shell", "-c", code, **env)

    def test_every_s3_variable_is_required_without_a_disk_fallback(self):
        from config.tests import S3_ENV

        for name in S3_ENV:
            with self.subTest(variable=name):
                result = self.probe(**{name: ""})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(name, result.stderr)

    def test_storage_endpoint_must_be_one_https_origin(self):
        for endpoint in ("http://objects.example.invalid", "https://key:secret@objects.example.invalid",
                         "https://objects.example.invalid/path", "https://objects.example.invalid/?key=value"):
            result = self.probe(AWS_S3_ENDPOINT_URL=endpoint)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AWS_S3_ENDPOINT_URL", result.stderr)

    def test_production_media_is_signed_and_support_has_no_browser_url(self):
        result = self.probe(
            "import json; from django.core.files.storage import storages; "
            "media=storages['default']; support=storages['support']; "
            "print(json.dumps([media.url('screenshots/test.webp'), support.location, media.file_overwrite]))"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        url, prefix, overwrite = json.loads(result.stdout.splitlines()[-1])
        parsed = urlsplit(url)
        self.assertEqual((parsed.scheme, parsed.netloc), ("https", "objects.example.invalid"))
        self.assertEqual(parsed.path, "/test-bucket/media/screenshots/test.webp")
        self.assertIn("X-Amz-Signature", parse_qs(parsed.query))
        self.assertEqual(prefix, "support")
        self.assertFalse(overwrite)
        from support.s3_storage import PrivateS3Storage

        storage = PrivateS3Storage(bucket_name="test-bucket", access_key="test-only", secret_key="test-only")
        with self.assertRaisesMessage(ValueError, "no public URL"):
            storage.url("attachment.webp")

    def test_community_stays_disabled_in_production_and_canonical_hosts_work(self):
        result = self.probe(
            "import json; from django.conf import settings as s; "
            "print(json.dumps([s.COMMUNITY_ENABLED,s.ALLOWED_HOSTS,s.CSRF_TRUSTED_ORIGINS,s.SITE_URL,s.CONTENT_SECURITY_POLICY]))",
            COMMUNITY_ENABLED=None, ALLOWED_HOSTS="launch-test.herokuapp.com",
            CSRF_TRUSTED_ORIGINS="https://launch-test.herokuapp.com",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        community, hosts, origins, site_url, csp = json.loads(result.stdout.splitlines()[-1])
        self.assertFalse(community)
        for host in ("shipmark.me", "www.shipmark.me", "launch-test.herokuapp.com"):
            self.assertIn(host, hosts)
            self.assertIn("https://" + host, origins)
        self.assertEqual(site_url, "https://shipmark.me")
        self.assertIn("img-src 'self' data: https://objects.example.invalid", csp)
        self.assertNotIn("unsafe-inline", csp)

    def test_heroku_postgres_scheme_is_parsed_without_connecting(self):
        result = self.probe(
            "from django.conf import settings as s; d=s.DATABASES['default']; print(d['ENGINE'],d['NAME'],d['HOST'])",
            DATABASE_URL="postgres://test_user:test_password@localhost:5432/test_database",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("django.db.backends.postgresql test_database localhost", result.stdout)

    def test_dev_keeps_local_upload_and_private_storage(self):
        self.assertEqual(settings.STORAGES["default"]["BACKEND"], "django.core.files.storage.FileSystemStorage")
        self.assertEqual(settings.STORAGES["support"]["BACKEND"], "support.storage.PrivateStorage")

    def test_gunicorn_uses_heroku_port_and_local_loopback(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(runpy.run_path("gunicorn.conf.py")["bind"], "127.0.0.1:8000")
        with patch.dict(os.environ, {"PORT": "43210", "GUNICORN_BIND": "127.0.0.1:8000"}, clear=True):
            self.assertEqual(runpy.run_path("gunicorn.conf.py")["bind"], "0.0.0.0:43210")
        procfile = (Path(settings.BASE_DIR) / "Procfile").read_text()
        self.assertIn("web: gunicorn config.wsgi", procfile)
        self.assertIn("release: python manage.py migrate --noinput", procfile)

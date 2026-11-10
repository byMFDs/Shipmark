"""Domain verification (Live): both methods, uniqueness, re-verification. DNS and HTTP are mocked."""
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

import dns.resolver
import httpx
from django.core.cache import cache
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from moderation.models import AuditLog
from projects.forms import ProjectForm
from projects.proof import compute_hallmarks
from projects.tests import make_project, make_user

from . import domain
from .domain import DomainCheckError, check_dns, check_meta, domain_key, host_from_url, verification_for, verify
from .models import DomainVerification
from .net import BlockedURL, FetchError, FetchResult

V = DomainVerification


def txt(*values):
    """A fake dnspython TXT answer. A value given as a tuple is split into chunks, like long records."""
    return [SimpleNamespace(strings=tuple(p.encode() for p in (v if isinstance(v, tuple) else (v,)))) for v in values]


def fake_dns(records):
    """records: name -> list of TXT values, or an exception class to raise."""
    def resolve(self, name, rdtype, **kwargs):
        value = records.get(str(name), dns.resolver.NXDOMAIN)
        if isinstance(value, type) and issubclass(value, Exception):
            raise value()
        if not value:
            raise dns.resolver.NoAnswer()
        return txt(*value)
    return patch.object(dns.resolver.Resolver, "resolve", resolve)


def page(html, status=200, url="https://example.com/"):
    return FetchResult(url=url, status_code=status, headers=httpx.Headers({"content-type": "text/html"}),
                       content=html.encode())


def fake_fetch(result=None, error=None):
    def fetch(url, **kwargs):
        fetch.urls.append(url)
        if error:
            raise error
        return result
    fetch.urls = []
    return patch.object(domain, "safe_fetch", fetch), fetch


class HostTests(TestCase):
    def test_host_from_url(self):
        self.assertEqual(host_from_url("https://WWW.Example.com:8443/path?q=1"), "www.example.com")
        self.assertEqual(host_from_url("https://example.com./"), "example.com")
        self.assertEqual(host_from_url("https://bücher.de/"), "xn--bcher-kva.de")
        for bad in ("", "https://127.0.0.1/", "https://[::1]/", "https://localhost/", "https://box.local/", "https://intranet/"):
            self.assertIsNone(host_from_url(bad), bad)

    def test_www_is_ignored_for_comparison(self):
        self.assertEqual(domain_key("www.example.com"), "example.com")
        self.assertEqual(domain_key("example.com"), "example.com")
        self.assertEqual(domain_key("app.example.com"), "app.example.com")


class DomainTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = make_user("ann")
        self.project = make_project(self.owner, live_url="https://www.example.com/app")
        self.row = verification_for(self.project, create=True)

    def verified(self, project=None, days_ago=0, method=V.Method.DNS):
        row = verification_for(project or self.project, create=True)
        when = timezone.now() - timedelta(days=days_ago)
        row.status, row.method, row.verified_at, row.last_confirmed_at = V.Status.VERIFIED, method, when, when
        row.save()
        return row


class RowTests(DomainTestCase):
    def test_row_keeps_exact_host_and_comparison_key(self):
        self.assertEqual((self.row.domain, self.row.domain_key), ("www.example.com", "example.com"))
        self.assertEqual(len(self.row.token), 32)

    def test_tokens_are_per_project_and_domain(self):
        other = make_project(make_user("bob"), live_url="https://example.com/")
        other_row = verification_for(other, create=True)
        self.assertNotEqual(other_row.token, self.row.token)
        self.assertEqual(verification_for(self.project).token, self.row.token)  # stable for the same domain

        self.project.live_url = "https://another.dev/"
        self.project.save()
        self.assertNotEqual(verification_for(self.project, create=True).token, self.row.token)

    def test_changing_live_url_forgets_the_old_domain(self):
        self.verified()
        form = ProjectForm({"name": self.project.name, "tagline": "t", "live_url": "https://another.dev/",
                            "repo_full_name": "", "tags_text": ""}, instance=self.project)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(V.objects.filter(domain_key="example.com").exists())
        self.assertTrue(AuditLog.objects.filter(action="hallmark.live.removed", metadata__reason="live_url_changed").exists())

    def test_ip_address_gets_no_row(self):
        project = make_project(self.owner, name="Ip", live_url="https://203.0.113.5/")
        self.assertIsNone(verification_for(project, create=True))


class DnsMethodTests(DomainTestCase):
    def test_txt_record_on_the_exact_host(self):
        with fake_dns({"www.example.com": [f"shipmark-verify={self.row.token}"]}):
            self.assertTrue(verify(self.row, "dns", actor=self.owner))
        self.row.refresh_from_db()
        self.assertEqual(self.row.status, V.Status.VERIFIED)
        self.assertIsNotNone(self.row.verified_at)
        self.assertEqual(self.row.verified_at, self.row.last_confirmed_at)
        self.assertTrue(compute_hallmarks(self.project)["live"].earned)
        entry = AuditLog.objects.get(action="hallmark.live.earned")
        self.assertEqual((entry.actor, entry.metadata["method"]), (self.owner, "dns"))

    def test_record_on_bare_domain_counts_for_www(self):
        with fake_dns({"www.example.com": [], "example.com": ["v=spf1 -all", f"shipmark-verify={self.row.token}"]}):
            check_dns("www.example.com", self.row.token)

    def test_long_record_split_in_chunks_and_quotes(self):
        with fake_dns({"www.example.com": [("shipmark-verify=", self.row.token)]}):
            check_dns("www.example.com", self.row.token)
        with fake_dns({"www.example.com": [f'"shipmark-verify={self.row.token}"']}):
            check_dns("www.example.com", self.row.token)

    def test_failures_have_clear_codes(self):
        cases = {
            "dns_no_txt": {"www.example.com": [], "example.com": []},
            "dns_wrong_txt": {"www.example.com": ["shipmark-verify=wrong"], "example.com": []},
            "dns_nxdomain": {},
            "dns_unavailable": {"www.example.com": dns.exception.Timeout, "example.com": dns.exception.Timeout},
        }
        for code, records in cases.items():
            with self.subTest(code), fake_dns(records), self.assertRaises(DomainCheckError) as ctx:
                check_dns("www.example.com", self.row.token)
            self.assertEqual(ctx.exception.code, code)

    def test_failed_check_stores_the_error_and_earns_nothing(self):
        with fake_dns({"www.example.com": ["other"]}), self.assertRaises(DomainCheckError):
            verify(self.row, "dns")
        self.row.refresh_from_db()
        self.assertEqual((self.row.status, self.row.last_error), (V.Status.PENDING, "dns_wrong_txt"))
        self.assertFalse(compute_hallmarks(self.project)["live"].earned)

    def test_token_of_another_project_does_not_work(self):
        other = verification_for(make_project(make_user("bob"), live_url="https://other.dev/"), create=True)
        with fake_dns({"www.example.com": [f"shipmark-verify={other.token}"], "example.com": []}), \
                self.assertRaises(DomainCheckError):
            verify(self.row, "dns")


class MetaMethodTests(DomainTestCase):
    def test_meta_tag_on_the_homepage(self):
        html = f'<html><head><META name="Shipmark-Verify" content="{self.row.token}"/></head></html>'
        patcher, fetch = fake_fetch(page(html, url="https://www.example.com/"))
        with patcher:
            self.assertTrue(verify(self.row, "meta"))
        self.assertEqual(fetch.urls, ["https://www.example.com/"])  # the homepage, via safe_fetch
        self.row.refresh_from_db()
        self.assertEqual((self.row.status, self.row.method), (V.Status.VERIFIED, "meta"))

    def test_http_live_url_is_fetched_over_http(self):
        self.project.live_url = "http://www.example.com/"
        self.project.save()
        patcher, fetch = fake_fetch(page(f'<meta name="shipmark-verify" content="{self.row.token}">'))
        with patcher:
            check_meta(domain.homepage_url(self.project, "www.example.com"), "www.example.com", self.row.token)
        self.assertEqual(fetch.urls, ["http://www.example.com/"])

    def test_meta_failures(self):
        token = self.row.token
        cases = {
            "meta_missing": dict(result=page("<html><head></head></html>")),
            "meta_wrong": dict(result=page('<meta name="shipmark-verify" content="nope">')),
            "http_error": dict(result=page(f'<meta name="shipmark-verify" content="{token}">', status=403)),
            "server_error": dict(result=page("", status=503)),
            "other_host": dict(result=page(f'<meta name="shipmark-verify" content="{token}">', url="https://evil.dev/")),
            "blocked": dict(error=BlockedURL("private_ip")),
            "too_large": dict(error=FetchError("too_large")),
            "unreachable": dict(error=FetchError("timeout")),
        }
        for code, kwargs in cases.items():
            patcher, _fetch = fake_fetch(**kwargs)
            with self.subTest(code), patcher, self.assertRaises(DomainCheckError) as ctx:
                check_meta("https://www.example.com/", "www.example.com", token)
            self.assertEqual(ctx.exception.code, code)

    def test_redirect_within_the_same_domain_is_fine(self):
        patcher, _fetch = fake_fetch(page(f'<meta name="shipmark-verify" content="{self.row.token}">',
                                          url="https://example.com/home"))
        with patcher:
            check_meta("https://www.example.com/", "www.example.com", self.row.token)


class UniquenessTests(DomainTestCase):
    def setUp(self):
        super().setUp()
        self.other = make_project(make_user("bob"), name="Copy", live_url="https://example.com/")
        self.other_row = verification_for(self.other, create=True)

    def test_verified_domain_blocks_other_projects(self):
        self.verified()
        with fake_dns({"example.com": [f"shipmark-verify={self.other_row.token}"]}), \
                self.assertRaises(DomainCheckError) as ctx:
            verify(self.other_row, "dns")
        self.assertEqual(ctx.exception.code, "taken")
        self.assertFalse(compute_hallmarks(self.other)["live"].earned)

    def test_pending_rows_block_nobody(self):
        with fake_dns({"example.com": [f"shipmark-verify={self.other_row.token}"]}):
            verify(self.other_row, "dns")
        self.assertTrue(compute_hallmarks(self.other)["live"].earned)

    def test_database_refuses_two_verified_rows(self):
        self.verified()
        self.other_row.status = V.Status.VERIFIED
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.other_row.save()

    def test_domain_is_free_again_after_removal(self):
        self.verified(days_ago=31)
        with fake_dns({"www.example.com": [], "example.com": []}):
            self.assertEqual(domain.reverify(V.objects.get(pk=self.row.pk)), "removed")
            with fake_dns({"example.com": [f"shipmark-verify={self.other_row.token}"]}):
                verify(self.other_row, "dns")
        self.assertTrue(compute_hallmarks(self.other)["live"].earned)


class LiveRuleTests(DomainTestCase):
    def test_live_needs_confirmation_within_35_days(self):
        self.verified(days_ago=34)
        self.assertTrue(compute_hallmarks(self.project)["live"].earned)
        self.verified(days_ago=36)
        self.assertFalse(compute_hallmarks(self.project)["live"].earned)

    def test_live_needs_the_current_domain(self):
        self.verified()
        self.project.live_url = "https://another.dev/"  # saved without the form: row still there
        self.assertFalse(compute_hallmarks(self.project)["live"].earned)
        self.project.live_url = "https://example.com/"  # same domain without www
        self.assertTrue(compute_hallmarks(self.project)["live"].earned)

    def test_failed_manual_check_does_not_remove_live(self):
        """The owner may be trying the other method; only the scheduled re-check removes Live."""
        self.verified()
        patcher, _fetch = fake_fetch(page("<html></html>"))
        with patcher, self.assertRaises(DomainCheckError):
            verify(V.objects.get(pk=self.row.pk), "meta")
        self.assertTrue(compute_hallmarks(self.project)["live"].earned)


class ReverifyTests(DomainTestCase):
    def run_command(self):
        out = StringIO()
        call_command("reverify_domains", stdout=out)
        return out.getvalue()

    def test_success_confirms_again(self):
        row = self.verified(days_ago=31)
        old = row.last_confirmed_at
        with fake_dns({"www.example.com": [f"shipmark-verify={row.token}"]}):
            self.assertIn("Confirmed 1", self.run_command())
        row.refresh_from_db()
        self.assertGreater(row.last_confirmed_at, old)
        self.assertEqual(row.verified_at, old)  # first success stays
        self.assertTrue(compute_hallmarks(self.project)["live"].earned)

    def test_failure_removes_hallmark_and_logs(self):
        self.verified(days_ago=31)
        with fake_dns({"www.example.com": ["something else"], "example.com": []}):
            self.assertIn("removed 1", self.run_command())
        row = V.objects.get(pk=self.row.pk)
        self.assertEqual((row.status, row.last_error), (V.Status.FAILED, "dns_wrong_txt"))
        self.assertFalse(compute_hallmarks(self.project)["live"].earned)
        entry = AuditLog.objects.get(action="hallmark.live.removed")
        self.assertEqual((entry.target_id, entry.metadata["reason"], entry.actor), (str(self.project.pk), "dns_wrong_txt", None))

    def test_meta_rows_are_rechecked_with_meta(self):
        self.verified(days_ago=31, method=V.Method.META)
        patcher, fetch = fake_fetch(page("<html>tag removed</html>", url="https://www.example.com/"))
        with patcher:
            self.run_command()
        self.assertEqual(fetch.urls, ["https://www.example.com/"])
        self.assertEqual(V.objects.get(pk=self.row.pk).status, V.Status.FAILED)

    def test_temporary_problem_is_retried_until_35_days(self):
        self.verified(days_ago=31)
        down = {"www.example.com": dns.exception.Timeout, "example.com": dns.exception.Timeout}
        with fake_dns(down):
            self.assertIn("retry later 1", self.run_command())
        self.assertEqual(V.objects.get(pk=self.row.pk).status, V.Status.VERIFIED)
        self.assertFalse(AuditLog.objects.filter(action="hallmark.live.removed").exists())

        self.verified(days_ago=36)
        with fake_dns(down):
            self.assertIn("removed 1", self.run_command())
        self.assertEqual(V.objects.get(pk=self.row.pk).status, V.Status.FAILED)

    def test_recent_rows_are_not_checked(self):
        self.verified(days_ago=29)
        with patch.object(domain, "run_method") as run:
            self.assertIn("Confirmed 0", self.run_command())
        run.assert_not_called()


class ViewTests(DomainTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)
        self.url = reverse("projects:domain_verify", args=["ann", self.project.slug])
        self.good_dns = fake_dns({"www.example.com": [f"shipmark-verify={self.row.token}"]})

    def test_edit_page_shows_instructions(self):
        response = self.client.get(reverse("projects:edit", args=["ann", self.project.slug]))
        self.assertContains(response, f"shipmark-verify={self.row.token}")
        self.assertContains(response, f'&lt;meta name=&quot;shipmark-verify&quot; content=&quot;{self.row.token}&quot;&gt;')
        self.assertContains(response, "Verify now")

    def test_plain_post_redirects_with_message(self):
        with self.good_dns:
            response = self.client.post(self.url, {"method": "dns"}, follow=True)
        self.assertContains(response, "Verified. Live earned.")
        self.assertEqual(V.objects.get(pk=self.row.pk).status, V.Status.VERIFIED)

    def test_json_post_returns_status_html(self):
        with self.good_dns:
            response = self.client.post(self.url, {"method": "dns"}, HTTP_ACCEPT="application/json")
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertIn("Live earned", data["html"])

    def test_json_failure_message(self):
        with fake_dns({"www.example.com": [], "example.com": []}):
            data = self.client.post(self.url, {"method": "dns"}, HTTP_ACCEPT="application/json").json()
        self.assertFalse(data["ok"])
        self.assertIn("No TXT records", data["message"])

    def test_rate_limited(self):
        with fake_dns({"www.example.com": [], "example.com": []}):
            codes = [self.client.post(self.url, {"method": "dns"}, HTTP_ACCEPT="application/json").status_code
                     for _ in range(6)]
        self.assertEqual(codes, [200] * 5 + [429])

    def test_other_user_gets_404(self):
        self.client.force_login(make_user("eve"))
        with patch.object(domain, "run_method") as run:
            self.assertEqual(self.client.post(self.url, {"method": "dns"}).status_code, 404)
        run.assert_not_called()

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_suspended_user_cannot_verify(self):
        self.owner.is_suspended = True
        self.owner.save()
        self.assertEqual(self.client.post(self.url, {"method": "dns"}).status_code, 403)

    def test_live_shows_on_the_public_page(self):
        self.verified()
        self.client.logout()
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "hallmark--l is-earned", count=1)

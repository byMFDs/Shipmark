"""Uptime checks and Steady: throttle, pruning, percentage math, the Steady rule. HTTP is mocked."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import httpx
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from projects.models import Project
from projects.proof import compute_hallmarks
from projects.tests import make_project, make_user

from . import uptime
from .domain import verification_for
from .models import DomainVerification, UptimeCheck
from .net import BlockedURL, FetchError, FetchResult
from .uptime import percent, probe, steady_rule, uptime_summary, with_uptime

V = DomainVerification


def answer(status):
    return FetchResult(url="https://example.com/", status_code=status, headers=httpx.Headers(), content=b"")


def fake_fetch(*replies):
    """Each reply is a status code or an exception. The last one repeats. Records (url, method)."""
    def fetch(url, method="GET", **kwargs):
        fetch.calls.append((url, method))
        reply = replies[min(len(fetch.calls), len(replies)) - 1]
        if isinstance(reply, Exception):
            raise reply
        return answer(reply)
    fetch.calls = []
    return patch.object(uptime, "safe_fetch", fetch), fetch


class UptimeTestCase(TestCase):
    def setUp(self):
        self.owner = make_user("ann")
        self.project = self.live_project("https://example.com/")
        self.now = timezone.now()

    def live_project(self, url, owner=None, name="Tallyhook", confirmed_days_ago=0):
        project = make_project(owner or self.owner, name=name, live_url=url)
        row = verification_for(project, create=True)
        when = timezone.now() - timedelta(days=confirmed_days_ago)
        row.status, row.verified_at, row.last_confirmed_at = V.Status.VERIFIED, when, when
        row.save()
        return project

    def add_checks(self, ok, failed=0, project=None, days_ago=1):
        """`ok` good and `failed` bad checks around noon of the day `days_ago` days back (one strip cell)."""
        noon = timezone.localtime(self.now - timedelta(days=days_ago)).replace(hour=12, minute=0, second=0)
        UptimeCheck.objects.bulk_create(
            UptimeCheck(project=project or self.project, checked_at=noon - timedelta(seconds=i),
                        ok=i < ok, status_code=200 if i < ok else 500)
            for i in range(ok + failed)
        )

    def hallmarks(self, project=None):
        fresh = Project.objects.prefetch_related("domain_verifications").get(pk=(project or self.project).pk)
        return {h.kind: h.earned for h in compute_hallmarks(fresh)}


class ProbeTests(TestCase):
    def test_ok_is_status_below_400(self):
        for status, ok in ((200, True), (301, True), (399, True), (400, False), (503, False)):
            mock, _fetch = fake_fetch(status)
            with self.subTest(status=status), mock:
                result = probe("https://example.com/")
            self.assertEqual((result.ok, result.status_code), (ok, status))

    def test_head_first_without_body(self):
        mock, fetch = fake_fetch(200)
        with mock:
            probe("https://example.com/")
        self.assertEqual(fetch.calls, [("https://example.com/", "HEAD")])

    def test_falls_back_to_get_when_head_is_refused(self):
        mock, fetch = fake_fetch(405, 200)
        with mock:
            result = probe("https://example.com/")
        self.assertEqual([m for _u, m in fetch.calls], ["HEAD", "GET"])
        self.assertTrue(result.ok)

    def test_falls_back_to_get_when_head_breaks(self):
        mock, fetch = fake_fetch(FetchError("connect"), 200)
        with mock:
            self.assertTrue(probe("https://example.com/").ok)
        self.assertEqual(len(fetch.calls), 2)

    def test_no_retry_for_blocked_or_timeout(self):
        for error in (BlockedURL("private_ip"), FetchError("timeout")):
            mock, fetch = fake_fetch(error, 200)
            with self.subTest(error=error.code), mock:
                result = probe("https://example.com/")
            self.assertEqual(len(fetch.calls), 1)
            self.assertEqual((result.ok, result.status_code, result.error), (False, None, error.code))


class ThrottleTests(UptimeTestCase):
    def test_second_check_within_3_hours_is_skipped(self):
        UptimeCheck.objects.create(project=self.project, checked_at=self.now - timedelta(hours=2, minutes=59), ok=True)
        mock, fetch = fake_fetch(200)
        with mock:
            self.assertIsNone(uptime.check_project(self.project, now=self.now))
        self.assertEqual(fetch.calls, [])
        self.assertEqual(UptimeCheck.objects.count(), 1)

    def test_check_after_3_hours_runs(self):
        UptimeCheck.objects.create(project=self.project, checked_at=self.now - timedelta(hours=3), ok=True)
        mock, _fetch = fake_fetch(200)
        with mock:
            check = uptime.check_project(self.project, now=self.now)
        self.assertTrue(check.ok)
        self.assertEqual(UptimeCheck.objects.count(), 2)

    def test_command_twice_stores_one_check(self):
        mock, fetch = fake_fetch(200)
        with mock:
            call_command("check_uptime", stdout=StringIO())
            call_command("check_uptime", stdout=StringIO())
        self.assertEqual(len(fetch.calls), 1)
        self.assertEqual(UptimeCheck.objects.filter(project=self.project).count(), 1)


class CommandTests(UptimeTestCase):
    def run_command(self, *replies, **options):
        mock, fetch = fake_fetch(*replies)
        out = StringIO()
        with mock:
            call_command("check_uptime", stdout=out, **options)
        return fetch, out.getvalue()

    def test_only_live_projects_are_checked(self):
        pending = make_project(self.owner, name="Pending", live_url="https://pending.dev/")
        verification_for(pending, create=True)
        self.live_project("https://stale.dev/", name="Stale", confirmed_days_ago=36)
        self.live_project("https://banned.dev/", owner=make_user("bob", is_suspended=True), name="Banned")
        moved = self.live_project("https://moved.dev/", name="Moved")
        Project.objects.filter(pk=moved.pk).update(live_url="https://elsewhere.dev/")  # verified domain is old

        fetch, out = self.run_command(200)
        self.assertEqual([u for u, _m in fetch.calls], ["https://example.com/"])
        self.assertIn("Up 1, down 0, skipped 1", out)

    def test_failed_site_is_stored_as_down(self):
        self.run_command(FetchError("timeout"))
        check = UptimeCheck.objects.get()
        self.assertEqual((check.ok, check.status_code, check.error), (False, None, "timeout"))

    def test_one_broken_site_does_not_stop_the_run(self):
        second = self.live_project("https://second.dev/", name="Second")
        real = uptime.probe

        def probe_or_crash(url, **kwargs):
            if url == "https://example.com/":
                raise RuntimeError("bug")
            return real(url)

        with patch.object(uptime, "probe", probe_or_crash), self.assertLogs("verification", "ERROR"):
            _fetch, out = self.run_command(200, batch_size=1)
        self.assertTrue(UptimeCheck.objects.get(project=second).ok)
        self.assertIn("errors 1", out)


class PruneTests(UptimeTestCase):
    def test_checks_older_than_90_days_are_deleted(self):
        for days in (91, 90.1, 89, 1):
            UptimeCheck.objects.create(project=self.project, checked_at=self.now - timedelta(days=days), ok=True)
        self.assertEqual(uptime.prune(now=self.now), 2)
        self.assertEqual(UptimeCheck.objects.count(), 2)

    def test_command_prunes(self):
        UptimeCheck.objects.create(project=self.project, checked_at=self.now - timedelta(days=100), ok=True)
        mock, _fetch = fake_fetch(200)
        with mock:
            call_command("check_uptime", stdout=StringIO())
        self.assertFalse(UptimeCheck.objects.filter(checked_at__lt=self.now - timedelta(days=90)).exists())


class PercentTests(UptimeTestCase):
    def test_math(self):
        self.assertIsNone(percent(0, 0))
        self.assertEqual(percent(40, 40), 100.0)
        self.assertEqual(percent(39, 40), 97.5)
        self.assertEqual(percent(2, 3), 66.6)  # rounded down
        self.assertEqual(percent(999, 1000), 99.9)
        self.assertEqual(percent(1999, 2000), 99.9)  # never shows 100 with a failed check
        self.assertEqual(percent(0, 5), 0.0)

    def test_summary_counts_only_last_30_days(self):
        self.add_checks(ok=3, failed=1, days_ago=2)
        self.add_checks(ok=0, failed=5, days_ago=31)  # outside the window
        summary = uptime_summary(self.project, now=self.now)
        self.assertEqual((summary.ok, summary.total, summary.percent), (3, 4, 75.0))
        self.assertEqual(len(summary.days), 30)
        self.assertEqual(summary.days[-1].date, timezone.localdate(self.now))
        states = {day.state for day in summary.days}
        self.assertEqual(states, {"none", "partial"})

    def test_day_states(self):
        self.add_checks(ok=2, days_ago=1)
        self.add_checks(ok=0, failed=2, days_ago=3)
        days = {d.date: d.state for d in uptime_summary(self.project, now=self.now).days}
        today = timezone.localdate(self.now)
        self.assertEqual(days[timezone.localdate(self.now - timedelta(days=1))], "up")
        self.assertEqual(days[timezone.localdate(self.now - timedelta(days=3))], "down")
        self.assertEqual(days[today], "none")

    def test_last_check_shown_even_when_older_than_30_days(self):
        self.add_checks(ok=1, days_ago=40)
        summary = uptime_summary(self.project, now=self.now)
        self.assertEqual(summary.total, 0)
        self.assertIsNotNone(summary.last_checked_at)


class SteadyTests(UptimeTestCase):
    def test_rule_boundaries(self):
        self.assertTrue(steady_rule(38, 40))  # exactly 95%
        self.assertFalse(steady_rule(37, 40))  # 92.5%
        self.assertFalse(steady_rule(39, 39))  # 100% but fewer than 40 checks
        self.assertTrue(steady_rule(95, 100))
        self.assertFalse(steady_rule(94, 100))

    def test_live_with_enough_good_checks_is_steady(self):
        self.add_checks(ok=38, failed=2)
        self.assertEqual(self.hallmarks(), {"authored": False, "live": True, "steady": True})

    def test_too_many_failures_is_not_steady(self):
        self.add_checks(ok=37, failed=3)
        self.assertFalse(self.hallmarks()["steady"])

    def test_too_few_checks_is_not_steady(self):
        self.add_checks(ok=39)
        self.assertFalse(self.hallmarks()["steady"])

    def test_old_checks_do_not_count(self):
        self.add_checks(ok=20, days_ago=1)
        self.add_checks(ok=20, days_ago=31)
        self.assertFalse(self.hallmarks()["steady"])

    def test_steady_needs_live(self):
        self.add_checks(ok=40)
        V.objects.filter(project=self.project).update(last_confirmed_at=self.now - timedelta(days=36))
        self.assertEqual(self.hallmarks(), {"authored": False, "live": False, "steady": False})

    def test_annotation_gives_same_answer_without_extra_queries(self):
        self.add_checks(ok=40)
        other = self.live_project("https://other.dev/", name="Other")
        self.add_checks(ok=10, project=other)
        projects = list(with_uptime(Project.objects.prefetch_related("domain_verifications").select_related("repo_link"))
                        .order_by("pk"))
        with self.assertNumQueries(0):
            results = [compute_hallmarks(p)["steady"].earned for p in projects]
        self.assertEqual(results, [True, False])


class ProjectPageTests(UptimeTestCase):
    def url(self, project=None):
        project = project or self.project
        return reverse("projects:detail", args=[project.owner.username, project.slug])

    def test_shows_percentage_and_strip(self):
        self.add_checks(ok=39, failed=1)
        response = self.client.get(self.url())
        self.assertContains(response, "97.5%")
        self.assertContains(response, "of 40 checks in the last 30 days")
        self.assertContains(response, "Last checked")
        self.assertContains(response, 'class="uptime-strip__day is-partial"')
        self.assertContains(response, "39 of 40 checks up")

    def test_live_without_checks_says_so(self):
        response = self.client.get(self.url())
        self.assertContains(response, "No checks in the last 30 days yet.")

    def test_hidden_when_not_live_and_never_checked(self):
        project = make_project(self.owner, name="Plain", live_url="https://plain.dev/")
        response = self.client.get(self.url(project))
        self.assertNotContains(response, 'class="uptime"')


class FinalHostTests(UptimeTestCase):
    """A check counts only when the answer comes from the verified domain, after all redirects."""

    def fetch_to(self, final_url, status=200):
        def fetch(url, method="GET", **kwargs):
            return FetchResult(url=final_url, status_code=status, headers=httpx.Headers(), content=b"",
                               redirects=[final_url] if final_url != url else [])
        return patch.object(uptime, "safe_fetch", fetch)

    def test_redirect_to_another_domain_is_down(self):
        with self.fetch_to("https://someone-else.com/landing"):
            check = uptime.check_project(self.project)
        self.assertFalse(check.ok)
        self.assertEqual(check.error, uptime.OTHER_HOST)
        self.assertEqual(check.status_code, 200)

    def test_redirects_within_the_domain_are_fine(self):
        for final in ("https://www.example.com/app", "https://example.com/en/"):
            UptimeCheck.objects.all().delete()
            with self.subTest(final=final), self.fetch_to(final):
                self.assertTrue(uptime.check_project(self.project).ok)

    def test_subdomain_is_another_host(self):
        with self.fetch_to("https://app.example.com/"):
            self.assertFalse(uptime.check_project(self.project).ok)

    def test_probe_without_expected_domain_keeps_old_behaviour(self):
        with self.fetch_to("https://elsewhere.com/"):
            self.assertTrue(probe("https://example.com/").ok)

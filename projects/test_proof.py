"""Hallmark rules (CLAUDE.md section 2): every row of the table, losing marks, caching, pages."""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.profile import profile_projects, profile_stats
from moderation.models import AuditLog
from verification import domain
from verification.domain import DomainCheckError, verification_for
from verification.models import DomainVerification, RepoLink, UptimeCheck

from .models import Project
from .proof import HallmarkSet, compute_hallmarks
from .tests import make_project, make_user

V = DomainVerification


class ProofTestCase(TestCase):
    """Спільні дані й помічники для тестів марок."""
    def setUp(self):
        self.now = timezone.now()
        self.owner = make_user("ann")
        self.project = make_project(self.owner, live_url="https://example.com/", repo_full_name="ann/tally")

    def fresh(self, project=None):
        """A new instance with the prefetches list views use, so nothing is cached between steps."""
        return (Project.objects.select_related("repo_link").prefetch_related("domain_verifications")
                .get(pk=(project or self.project).pk))

    def marks(self, project=None):
        return compute_hallmarks(self.fresh(project))

    def link(self, project=None, **extra):
        project = project or self.project
        values = {"repo_full_name": project.repo_full_name, "github_repo_id": project.pk,
                  "checked_at": self.now, "earned_at": self.now - timedelta(days=3)}
        return RepoLink.objects.create(project=project, **{**values, **extra})

    def verify(self, project=None, confirmed_days_ago=0, status=V.Status.VERIFIED):
        row = verification_for(project or self.project, create=True)
        when = self.now - timedelta(days=confirmed_days_ago)
        row.status, row.verified_at, row.last_confirmed_at = status, when - timedelta(days=1), when
        row.save()
        return row

    def checks(self, ok, failed=0, project=None):
        UptimeCheck.objects.bulk_create(
            UptimeCheck(project=project or self.project, checked_at=self.now - timedelta(hours=3 * i + 1), ok=i < ok)
            for i in range(ok + failed)
        )


class ShapeTests(ProofTestCase):
    """Форма результату compute_hallmarks."""
    def test_three_marks_in_order_with_lookup_by_kind(self):
        marks = self.marks()
        self.assertIsInstance(marks, HallmarkSet)
        self.assertEqual([m.kind for m in marks], ["authored", "live", "steady"])
        self.assertIs(marks["live"], marks[1])
        self.assertEqual(marks.earned_count, 0)
        for mark in marks:
            self.assertTrue(mark.reason)
            self.assertTrue(str(mark.rule))
            self.assertIsNone(mark.earned_at)
        with self.assertRaises(KeyError):
            marks["used"]  # post-MVP: never computed, never shown

    def test_cached_on_the_instance(self):
        project = self.fresh()
        first = project.hallmarks
        with self.assertNumQueries(0):
            self.assertIs(project.hallmarks, first)


class AuthoredTests(ProofTestCase):
    """Марка «Repo owner»."""
    def test_no_repository(self):
        self.project.repo_full_name = ""
        self.project.save()
        mark = self.marks()["authored"]
        self.assertFalse(mark.earned)
        self.assertEqual(mark.reason, "No repository linked.")

    def test_repository_not_checked(self):
        self.assertFalse(self.marks()["authored"].earned)

    def test_owner_of_the_repository(self):
        link = self.link(is_owner=True, user_commit_count=0)
        mark = self.marks()["authored"]
        self.assertTrue(mark.earned)
        self.assertEqual(mark.earned_at, link.earned_at)
        self.assertIn("ann/tally", mark.reason)

    def test_commit_count_alone_never_earns(self):
        self.link(is_owner=False, user_commit_count=500)
        self.assertFalse(self.marks()["authored"].earned)

    def test_review_states(self):
        link = self.link(is_owner=True, review_state=RepoLink.Review.NEEDS_REVIEW, review_reasons=["imported_history"])
        mark = self.marks()["authored"]
        self.assertFalse(mark.earned)
        self.assertEqual(mark.reason, "The repository is waiting for a routine manual review.")
        self.assertNotIn("import", mark.reason)  # the public reason never names the suspicion
        link.review_state = RepoLink.Review.APPROVED
        link.save()
        self.assertTrue(self.marks()["authored"].earned)
        link.review_state = RepoLink.Review.NEEDS_RECHECK
        link.save()
        self.assertFalse(self.marks()["authored"].earned)

    def test_link_for_another_repository_does_not_count(self):
        self.link(is_owner=True)
        self.project.repo_full_name = "ann/other"
        self.project.save()
        self.assertFalse(self.marks()["authored"].earned)

    def test_name_case_does_not_matter(self):
        self.link(is_owner=True, repo_full_name="Ann/Tally")
        self.assertTrue(self.marks()["authored"].earned)


class LiveTests(ProofTestCase):
    """Марка «Domain verified»."""
    def test_verified_and_recently_confirmed(self):
        row = self.verify(confirmed_days_ago=34)
        mark = self.marks()["live"]
        self.assertTrue(mark.earned)
        self.assertEqual(mark.earned_at, row.verified_at)
        self.assertIn("example.com", mark.reason)

    def test_not_confirmed_in_35_days(self):
        self.verify(confirmed_days_ago=36)
        mark = self.marks()["live"]
        self.assertFalse(mark.earned)
        self.assertIn("35 days", mark.reason)

    def test_pending_and_missing(self):
        self.assertEqual(self.marks()["live"].reason, "The domain has not been verified yet.")
        self.verify(status=V.Status.PENDING)
        self.assertFalse(self.marks()["live"].earned)
        self.project.live_url = ""
        self.project.save()
        self.assertEqual(self.marks()["live"].reason, "No live URL.")

    def test_ip_address_cannot_be_live(self):
        self.project.live_url = "http://203.0.113.5/"
        self.project.save()
        self.assertFalse(self.marks()["live"].earned)

    def test_moving_to_another_domain_drops_live(self):
        self.verify()
        self.project.live_url = "https://other.example.org/"
        self.project.save()
        self.assertFalse(self.marks()["live"].earned)

    def test_www_counts_as_the_same_domain(self):
        self.verify()
        self.project.live_url = "https://www.example.com/app"
        self.project.save()
        self.assertTrue(self.marks()["live"].earned)

    def test_lost_after_failed_reverification_and_logged(self):
        row = self.verify(confirmed_days_ago=31)
        self.assertTrue(self.marks()["live"].earned)
        with patch.object(domain, "run_method", side_effect=DomainCheckError("dns_wrong_txt")):
            self.assertEqual(domain.reverify(V.objects.get(pk=row.pk)), "removed")
        mark = self.marks()["live"]
        self.assertFalse(mark.earned)
        self.assertIn("failed re-verification", mark.reason)
        self.assertTrue(AuditLog.objects.filter(action="hallmark.live.removed", target_id=str(self.project.pk)).exists())

    def test_temporary_failure_keeps_live(self):
        row = self.verify(confirmed_days_ago=31)
        with patch.object(domain, "run_method", side_effect=DomainCheckError("dns_unavailable")):
            self.assertEqual(domain.reverify(V.objects.get(pk=row.pk)), "kept")
        self.assertTrue(self.marks()["live"].earned)


class SteadyTests(ProofTestCase):
    """Марка «Steady»."""
    def test_live_with_40_checks_at_95_percent(self):
        self.verify()
        self.checks(ok=38, failed=2)
        mark = self.marks()["steady"]
        self.assertTrue(mark.earned)
        self.assertIsNone(mark.earned_at)  # a rolling 30-day window has no single start date
        self.assertIn("95%", mark.reason)

    def test_below_95_percent(self):
        self.verify()
        self.checks(ok=37, failed=3)
        mark = self.marks()["steady"]
        self.assertFalse(mark.earned)
        self.assertIn("92.5%", mark.reason)

    def test_fewer_than_40_checks(self):
        self.verify()
        self.checks(ok=39)
        mark = self.marks()["steady"]
        self.assertFalse(mark.earned)
        self.assertEqual(mark.reason, "39 of 40 uptime checks so far.")

    def test_old_checks_do_not_count(self):
        self.verify()
        UptimeCheck.objects.bulk_create(
            UptimeCheck(project=self.project, checked_at=self.now - timedelta(days=31, hours=i), ok=True)
            for i in range(50)
        )
        self.assertFalse(self.marks()["steady"].earned)

    def test_requires_live(self):
        self.checks(ok=60)  # perfect uptime, but the domain was never verified
        mark = self.marks()["steady"]
        self.assertFalse(mark.earned)
        self.assertEqual(mark.reason, "Needs Domain verified first.")
        self.verify(confirmed_days_ago=36)  # verified once, but not confirmed in time
        self.assertFalse(self.marks()["steady"].earned)

    def test_lost_together_with_live(self):
        row = self.verify(confirmed_days_ago=31)
        self.checks(ok=60)
        self.assertEqual(self.marks().earned_count, 2)
        with patch.object(domain, "run_method", side_effect=DomainCheckError("meta_missing")):
            domain.reverify(V.objects.get(pk=row.pk))
        marks = self.marks()
        self.assertFalse(marks["live"].earned)
        self.assertFalse(marks["steady"].earned)


class ListTests(ProofTestCase):
    """Марки в списках."""
    def test_profile_counts_without_extra_queries_per_project(self):
        self.link(is_owner=True)
        self.verify()
        self.checks(ok=40)
        for i in range(3):
            make_project(self.owner, name=f"Other {i}", repo_full_name=f"ann/o{i}")
        projects = profile_projects(self.owner)
        with self.assertNumQueries(1):  # only the follower count; hallmarks need nothing per project
            stats = profile_stats(self.owner, projects)
        self.assertEqual(stats["hallmarks"], 3)

    def test_profile_rows_show_small_marks(self):
        self.link(is_owner=True)
        html = self.client.get(reverse("accounts:profile", args=[self.owner.username])).content.decode()
        self.assertIn("hallmark--s is-earned", html)
        self.assertEqual(html.count("hallmark--s is-unearned"), 2)


class PageTests(ProofTestCase):
    """Марки на сторінці проєкту."""
    def test_project_page_explains_each_mark(self):
        self.link(is_owner=True)
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, 'class="hallmark-info"', count=3)
        self.assertContains(response, "ann/tally is owned by the author&#x27;s GitHub account.")
        self.assertContains(response, "Needs Domain verified first.")
        self.assertContains(response, "needs write access to the repository")  # the rule
        self.assertContains(response, 'href="/how-proof-works/#live"')

    def test_how_proof_works_in_english_and_ukrainian(self):
        en = self.client.get("/how-proof-works/", headers={"Accept-Language": "en"})
        self.assertContains(en, "<h1>How proof works</h1>", html=True)
        for anchor in ("authored", "live", "steady", "self-declared"):
            self.assertContains(en, f'id="{anchor}"')
        self.assertNotContains(en, "{#")
        uk = self.client.get("/how-proof-works/", headers={"Accept-Language": "uk"})
        self.assertContains(uk, "Як працюють підтвердження")
        self.assertContains(uk, 'id="steady"')


class UnverifiedRepoLinkTests(ProofTestCase):
    """Неперевірене посилання на репозиторій не дає марки."""
    def test_repo_without_the_mark_is_labelled(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "https://github.com/ann/tally")
        self.assertContains(response, "Unverified link")

    def test_repo_with_the_mark_is_not_labelled(self):
        self.link(is_owner=True)
        self.assertNotContains(self.client.get(self.project.get_absolute_url()), "Unverified link")


class RepoDomainLinkTests(ProofTestCase):
    """Факт зв'язку репозиторію з доменом."""
    def test_homepage_on_the_verified_domain(self):
        from .proof import repo_domain_link

        self.verify()
        link = self.link(is_owner=True, homepage="https://www.example.com/docs")
        self.assertEqual(repo_domain_link(self.fresh()), "homepage")
        link.homepage = "https://elsewhere.com/"
        link.save()
        self.assertIsNone(repo_domain_link(self.fresh()))

    def test_soft_rule_never_changes_the_marks(self):
        from .proof import repo_domain_link

        self.verify()
        self.link(is_owner=True, homepage="")
        self.assertIsNone(repo_domain_link(self.fresh()))
        marks = self.marks()
        self.assertTrue(marks["authored"].earned)
        self.assertTrue(marks["live"].earned)


class WhatWasCheckedTests(ProofTestCase):
    """Панель «Що перевірено»."""
    def texts(self):
        from .proof import checked_facts

        return [fact.text for fact in checked_facts(self.fresh())]

    def test_verified_repo_and_domain_facts_with_dates(self):
        self.verify()
        self.link(is_owner=True, user_commit_count=12, first_commit_at=self.now - timedelta(days=90),
                  last_commit_at=self.now, repo_created_at=self.now - timedelta(days=100),
                  root_commit_at=self.now - timedelta(days=99), root_commit_sha="d" * 40, active_weeks=7,
                  homepage="https://example.com/")
        joined = " | ".join(self.texts())
        for part in ("matched by account id", "Not a fork.", "Repository created on GitHub", "First commit in its history",
                     "Commits by the author: 12", "Weeks with code changes by the author: 7",
                     "No other project here has the same history", "proven with a DNS record",
                     "website field on GitHub points to example.com"):
            self.assertIn(part, joined)
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "What was checked")
        self.assertContains(response, "We cannot check who wrote the code.")

    def test_unverified_link_and_review_never_name_the_reason(self):
        self.assertEqual(self.texts(), ["ann/tally is not verified. It is the author's own link."])
        self.link(is_owner=True, review_state=RepoLink.Review.NEEDS_REVIEW, review_reasons=["imported_history"])
        joined = " ".join(self.texts())
        self.assertIn("routine manual review", joined)
        self.assertNotIn("import", joined)

    def test_shared_history_is_not_claimed_unique(self):
        other = make_project(make_user("bob"), name="Copy", repo_full_name="bob/copy")
        RepoLink.objects.create(project=other, repo_full_name="bob/copy", github_repo_id=999, is_owner=True,
                                root_commit_sha="e" * 40, checked_at=self.now)
        self.link(is_owner=True, root_commit_sha="e" * 40)
        self.assertNotIn("No other project here has the same history.", self.texts())

    def test_nothing_to_show_hides_the_panel(self):
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="", live_url="")
        self.assertNotContains(self.client.get(self.project.get_absolute_url()), "What was checked")

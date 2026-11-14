"""Weekly repo re-verification (reverify_repos) and the admin review queue. GitHub is mocked."""
from datetime import timedelta
from io import StringIO

import httpx
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from moderation.models import AuditLog
from projects.models import Project
from projects.proof import compute_hallmarks
from projects.tests import make_project, make_user

from . import review
from .domain import DomainCheckError, reverify, verification_for, verify
from .models import Block, DomainVerification, RepoLink
from .repo import RepoCheckError, due_links, reverify_link, run_check
from .test_domain import fake_dns
from .tests import ME, RepoCheckTestCase, commit, mock_github, person, repo_json

LIMITED = {"/repositories/77": lambda r: httpx.Response(
    403, json={"message": "API rate limit exceeded"}, headers={"x-ratelimit-remaining": "0"})}


class ReverifyRepoTests(RepoCheckTestCase):
    """Повторна перевірка репозиторіїв."""
    def setUp(self):
        super().setUp()
        self.check(contributors=[[person()]])
        self.link = RepoLink.objects.get()
        RepoLink.objects.update(checked_at=timezone.now() - timedelta(days=8))
        self.link.refresh_from_db()

    def reverify(self, **mock_args):
        patcher, seen = mock_github(**mock_args)
        with patcher:
            outcome = reverify_link(RepoLink.objects.select_related("project__owner").get(pk=self.link.pk)
                                    if RepoLink.objects.filter(pk=self.link.pk).exists() else self.link)
        return outcome, seen

    def earned(self):
        return compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned

    def removed_reason(self):
        return AuditLog.objects.filter(action="hallmark.authored.removed").latest("pk").metadata["reason"]

    def test_still_owned_is_confirmed_by_repo_id_first(self):
        outcome, seen = self.reverify(contributors=[[person()]])
        self.assertEqual(outcome, "confirmed")
        self.assertEqual(seen[0], "/repositories/77")
        self.assertGreater(RepoLink.objects.get().checked_at, timezone.now() - timedelta(minutes=1))
        self.assertTrue(self.earned())

    def assertRemoved(self, reason, **mock_args):
        outcome, _seen = self.reverify(contributors=[[person()]], **mock_args)
        self.assertEqual(outcome, "removed")
        self.assertFalse(RepoLink.objects.exists())
        self.assertFalse(self.earned())
        self.assertEqual(self.removed_reason(), reason)

    def test_deleted_or_private_by_id_removes_the_mark(self):
        self.assertRemoved("gone", extra={"/repositories/77": lambda r: httpx.Response(404, json={})})

    def test_transferred_removes_the_mark(self):
        self.assertRemoved("transferred", repo=repo_json(owner_id=5))

    def test_made_private_removes_the_mark(self):
        self.assertRemoved("private", repo=repo_json(private=True))

    def test_rename_is_followed_and_logged(self):
        outcome, _seen = self.reverify(repo=repo_json(name="me/tool-2"), contributors=[[person()]])
        self.assertEqual(outcome, "confirmed")
        self.project.refresh_from_db()
        self.assertEqual(self.project.repo_full_name, "me/tool-2")
        self.assertTrue(AuditLog.objects.filter(action="repo.renamed").exists())
        self.assertTrue(self.earned())

    def test_github_trouble_keeps_everything(self):
        for extra in ({"/repositories/77": lambda r: httpx.Response(502)},
                      {"/repos/me/tool": lambda r: httpx.Response(503)},
                      {"/repositories/77": lambda r: (_ for _ in ()).throw(httpx.ConnectTimeout("slow"))}):
            with self.subTest(extra=list(extra)):
                outcome, _seen = self.reverify(extra=extra)
                self.assertEqual(outcome, "kept")
                self.assertTrue(self.earned())
                self.assertEqual(RepoLink.objects.get().checked_at, self.link.checked_at)

    def test_rate_limit_is_raised_and_changes_nothing(self):
        with self.assertRaises(RepoCheckError) as ctx:
            self.reverify(extra=LIMITED)
        self.assertEqual(ctx.exception.code, "rate_limited")
        self.assertTrue(self.earned())

    def test_new_review_facts_set_needs_review(self):
        outcome, _seen = self.reverify(repo=repo_json(created_at="2025-06-01T00:00:00Z"), contributors=[[person()]],
                                       root=[commit("2018-01-01T00:00:00Z")])
        self.assertEqual(outcome, "review")
        self.assertFalse(self.earned())
        self.assertTrue(AuditLog.objects.filter(action="hallmark.authored.needs_review").exists())

    def test_old_contributor_link_is_resolved(self):
        RepoLink.objects.update(is_owner=False, github_owner_id=5, review_state=RepoLink.Review.NEEDS_RECHECK)
        outcome, _seen = self.reverify(repo=repo_json(owner_id=5, owner_type="Organization"), contributors=[[person()]])
        self.assertEqual(outcome, "removed")
        self.assertEqual(self.removed_reason(), "not_owner")

    def test_due_links(self):
        fresh = make_project(self.user, name="Fresh", repo_full_name="me/fresh")
        RepoLink.objects.create(project=fresh, repo_full_name="me/fresh", github_repo_id=88, is_owner=True,
                                active_weeks=3, checked_at=timezone.now())
        pending = make_project(self.user, name="Pending", repo_full_name="me/pending")
        RepoLink.objects.create(project=pending, repo_full_name="me/pending", github_repo_id=89, is_owner=True,
                                checked_at=timezone.now() - timedelta(days=1))  # statistics never arrived
        names = set(due_links().values_list("repo_full_name", flat=True))
        self.assertEqual(names, {"me/tool", "me/pending"})

    def test_command_counts_and_stops_on_rate_limit(self):
        out = StringIO()
        patcher, _seen = mock_github(contributors=[[person()]])
        with patcher:
            call_command("reverify_repos", stdout=out)
        self.assertIn("Confirmed 1", out.getvalue())
        RepoLink.objects.update(checked_at=timezone.now() - timedelta(days=8))
        out = StringIO()
        patcher, _seen = mock_github(extra=LIMITED)
        with patcher:
            call_command("reverify_repos", stdout=out)
        self.assertIn("Rate limited, stopped", out.getvalue())
        self.assertTrue(self.earned())


class ReviewQueueTests(RepoCheckTestCase):
    """Черга розгляду."""
    def setUp(self):
        super().setUp()
        self.staff = make_user("staff", is_staff=True, is_superuser=True)
        self.check(contributors=[[]])  # no commits by the owner -> needs review
        self.link = RepoLink.objects.get()

    def earned(self):
        return compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned

    def test_approve(self):
        self.assertFalse(self.earned())
        self.assertTrue(review.approve(self.link, self.staff))
        self.assertTrue(self.earned())
        self.assertEqual(AuditLog.objects.get(action="moderation.repo.approved").actor, self.staff)
        self.assertFalse(review.review_queue().exists())

    def test_revoke(self):
        review.approve(self.link, self.staff)
        review.revoke_repo(RepoLink.objects.get(), self.staff)
        self.assertFalse(self.earned())
        self.assertEqual(AuditLog.objects.filter(action="hallmark.authored.removed").get().metadata["reason"],
                         "revoked_by_staff")

    def test_block_repo_stops_every_project_even_after_rename(self):
        review.block_repo(self.link, self.staff)
        self.assertFalse(RepoLink.objects.exists())
        self.assertTrue(AuditLog.objects.filter(action="moderation.repo.blocked").exists())
        other = make_project(self.user, name="Again", repo_full_name="me/renamed")
        patcher, _seen = mock_github(repo=repo_json(name="me/renamed"), contributors=[[person()]])
        with patcher, self.assertRaises(RepoCheckError) as ctx:
            run_check(other, ME)
        self.assertEqual(ctx.exception.code, "blocked")
        self.assertNotIn("block", ctx.exception.message.split(".")[0].lower().replace("cannot be linked", ""))

    def test_admin_queue_and_actions(self):
        self.client.force_login(self.staff)
        url = reverse("admin:verification_reporeview_changelist")
        self.assertContains(self.client.get(url), "me/tool")
        response = self.client.post(url, {"action": "approve", "_selected_action": [self.link.pk]}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.earned())
        self.assertNotContains(self.client.get(url), "me/tool")  # left the queue
        self.assertEqual(self.client.get(reverse("admin:verification_block_changelist")).status_code, 200)

    def test_view_only_staff_cannot_approve(self):
        viewer = make_user("viewer", is_staff=True)
        from django.contrib.auth.models import Permission

        viewer.user_permissions.add(Permission.objects.get(codename="view_repolink"),
                                    Permission.objects.get(codename="view_reporeview"))
        self.client.force_login(viewer)
        url = reverse("admin:verification_reporeview_changelist")
        self.client.post(url, {"action": "approve", "_selected_action": [self.link.pk]})
        self.assertFalse(self.earned())


class DomainBlockTests(TestCase):
    """Блокування доменів."""
    def setUp(self):
        self.owner = make_user("ann")
        self.staff = make_user("staff", is_staff=True, is_superuser=True)
        self.project = make_project(self.owner, live_url="https://www.example.com/")
        self.row = verification_for(self.project, create=True)
        self.row.status, self.row.verified_at, self.row.last_confirmed_at = (
            DomainVerification.Status.VERIFIED, timezone.now(), timezone.now() - timedelta(days=31))
        self.row.save()

    def test_block_domain_revokes_live_and_refuses_it_again(self):
        review.block_domain(self.row, self.staff)
        self.row.refresh_from_db()
        self.assertEqual(self.row.status, DomainVerification.Status.FAILED)
        self.assertFalse(compute_hallmarks(Project.objects.get(pk=self.project.pk))["live"].earned)
        self.assertTrue(Block.domain_blocked("example.com"))
        other = make_project(make_user("bob"), name="Other", live_url="https://example.com/")
        row = verification_for(other, create=True)
        with fake_dns({"example.com": [f"shipmark-verify={row.token}"]}), self.assertRaises(DomainCheckError) as ctx:
            verify(row, "dns")
        self.assertEqual(ctx.exception.code, "blocked_domain")

    def test_reverify_removes_a_blocked_domain(self):
        Block.objects.create(kind=Block.Kind.DOMAIN, value="example.com")
        with fake_dns({"www.example.com": [f"shipmark-verify={self.row.token}"]}):
            self.assertEqual(reverify(self.row), "removed")

    def test_revoke_live_from_the_admin(self):
        self.client.force_login(self.staff)
        url = reverse("admin:verification_domainverification_changelist")
        self.client.post(url, {"action": "revoke_live", "_selected_action": [self.row.pk]})
        self.row.refresh_from_db()
        self.assertEqual(self.row.status, DomainVerification.Status.FAILED)
        self.assertEqual(AuditLog.objects.get(action="hallmark.live.removed").actor, self.staff)

"""Regression tests for the attacks in docs/TRUST_AUDIT.md (scenarios a..l). GitHub, DNS and HTTP are mocked.

Each test is named after the attack. Most end BLOCKED (no mark) or in "needs review" (mark withheld).
A few are honest limits (named `..._limit`): nobody can tell a copied repository with fresh or
rewritten history from an original. There the test pins what we do instead: the mark claims only
ownership, the facts are shown with dates, and the page says we cannot check who wrote the code.
"""
from datetime import timedelta
from unittest.mock import patch

import httpx
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts import github
from projects.models import Project
from projects.proof import checked_facts, compute_hallmarks, repo_domain_link
from projects.tests import make_project, make_user

from . import domain, uptime
from .domain import DomainCheckError, verification_for, verify
from .models import DomainVerification, RepoLink, UptimeCheck
from .net import FetchResult
from .repo import AUTHORED, FORK, NOT_YOURS, RepoCheckError, reverify_link, run_check
from .test_domain import fake_dns
from .tests import ME, RepoCheckTestCase, commit, mock_github, person, repo_json, stats_entry

V = DomainVerification
VICTIM = 5


def fresh(project):
    return (Project.objects.select_related("repo_link").prefetch_related("domain_verifications")
            .get(pk=project.pk))


class RepoAttackTests(RepoCheckTestCase):
    """Спроби обдурити перевірку репозиторію."""
    def marks(self):
        return compute_hallmarks(fresh(self.project))

    def link_state(self):
        link = RepoLink.objects.filter(project=self.project).first()
        return link.review_state if link else None

    # a. Link someone else's repository (even with many merged commits in it).
    def test_a_someone_elses_repo_is_refused(self):
        self.project.repo_full_name = "victim/app"
        self.project.save()
        result = self.check(repo=repo_json(owner_id=VICTIM, name="victim/app"),
                            contributors=[[person(user_id=VICTIM, commits=900), person(commits=40)]])
        self.assertEqual(result.outcome, NOT_YOURS)
        self.assertIsNone(self.link_state())
        self.assertFalse(self.marks()["authored"].earned)

    # b. Fork of someone's repository, with or without own commits on top.
    def test_b_fork_is_refused(self):
        result = self.check(repo=repo_json(fork=True), contributors=[[person(user_id=VICTIM, commits=400), person(commits=10)]])
        self.assertEqual(result.outcome, FORK)
        self.assertIsNone(self.link_state())

    # c. Someone else's code from a zip pushed as a new repository with one commit.
    def test_c_zip_copy_with_fresh_history_limit(self):
        result = self.check(repo=repo_json(created_at="2026-10-01T00:00:00Z"), contributors=[[person(commits=1)]],
                            root=[commit("2026-10-01T01:00:00Z", "1" * 40)], stats=[stats_entry(weeks=[(1, 9000, 0)])])
        self.assertEqual(result.outcome, AUTHORED)  # the user really owns this repository: that is all the mark says
        texts = " ".join(f.text for f in checked_facts(fresh(self.project)))
        self.assertIn("Commits by the author: 1", texts)  # the thin history is visible to every reader
        self.assertIn("Weeks with code changes by the author: 1", texts)
        self.assertNotIn("wrote", str(self.marks()["authored"].reason))

    # d. Copy with full history pushed to an own repository.
    def test_d_copy_with_full_history_needs_review(self):
        self.check(repo=repo_json(created_at="2026-10-01T00:00:00Z"), contributors=[[person(commits=2)]],
                   root=[commit("2021-03-01T00:00:00Z", "2" * 40)])
        self.assertEqual(self.link_state(), RepoLink.Review.NEEDS_REVIEW)
        self.assertFalse(self.marks()["authored"].earned)

    def test_d_same_copy_by_two_accounts_needs_review(self):
        other = make_project(make_user("first"), name="Original", repo_full_name="first/app")
        RepoLink.objects.create(project=other, repo_full_name="first/app", github_repo_id=500, is_owner=True,
                                root_commit_sha="3" * 40, checked_at=timezone.now())
        self.check(contributors=[[person()]], root=[commit("2026-01-01T00:00:00Z", "3" * 40)])
        self.assertEqual(RepoLink.objects.get(project=self.project).review_reasons, ["duplicate_history"])

    # e. Own repository with no commits of the owner, or trivial commits all on one day.
    def test_e_empty_or_foreign_commits_need_review(self):
        self.check(contributors=[[person(user_id=VICTIM, commits=50)]])
        self.assertEqual(self.link_state(), RepoLink.Review.NEEDS_REVIEW)

    def test_e_trivial_commits_in_one_day_limit(self):
        self.check(contributors=[[person(commits=30)]], stats=[stats_entry(weeks=[(30, 0, 0), (0, 0, 0)])])
        link = RepoLink.objects.get()
        self.assertTrue(link.is_verified)  # owned, so the mark stands; the fact below tells the rest
        self.assertEqual(link.active_weeks, 1)

    # f. GitHub login renamed, then the old login is taken by another account.
    def test_f_reused_login_cannot_claim_the_repo(self):
        result = self.check(repo=repo_json(owner_id=999, name="me/tool"), contributors=[[person(user_id=999, login="me")]])
        self.assertEqual(result.outcome, NOT_YOURS)  # owner compared by numeric id, never by login

    def test_f_stale_login_is_released_not_duplicated(self):
        self.user.github_login = "shared"
        self.user.save()
        newcomer = make_user("newcomer")
        SocialAccount.objects.create(user=newcomer, provider="github", uid="999")
        github.refresh_login(newcomer, {"login": "shared"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_login, "")
        self.assertEqual(get_user_model().objects.filter(github_login="shared").count(), 1)

    # g. Repository deleted and recreated by someone else; transferred; made private afterwards.
    def reverified(self, **mock_args):
        self.check(contributors=[[person()]])
        patcher, _seen = mock_github(**mock_args)
        with patcher:
            return reverify_link(RepoLink.objects.select_related("project__owner").get())

    def test_g_deleted_and_recreated_is_removed(self):
        outcome = self.reverified(extra={"/repositories/77": lambda r: httpx.Response(404, json={})},
                                  repo=repo_json(repo_id=4242, owner_id=VICTIM))
        self.assertEqual(outcome, "removed")
        self.assertFalse(self.marks()["authored"].earned)

    def test_g_transferred_is_removed(self):
        self.assertEqual(self.reverified(repo=repo_json(owner_id=VICTIM), contributors=[[person()]]), "removed")

    def test_g_made_private_is_removed(self):
        self.assertEqual(self.reverified(repo=repo_json(private=True)), "removed")

    def test_g_manual_check_of_a_recreated_name_is_a_new_repository(self):
        self.check(contributors=[[person()]])
        result = self.check(repo=repo_json(repo_id=4242, owner_id=VICTIM), contributors=[[person()]])
        self.assertEqual(result.outcome, NOT_YOURS)
        self.assertFalse(RepoLink.objects.exists())

    # j. Two users claiming the same repository; a contributor squatting someone's repository.
    def test_j_second_claim_of_a_repo_is_refused(self):
        self.check(contributors=[[person()]])
        thief = make_user("thief")
        stolen = make_project(thief, name="Stolen", repo_full_name="me/tool")
        patcher, _seen = mock_github(contributors=[[person()]])
        with patcher, self.assertRaises(RepoCheckError) as ctx:
            run_check(stolen, ME)
        self.assertEqual(ctx.exception.code, "taken")

    def test_j_contributor_cannot_squat(self):
        self.project.repo_full_name = "team/app"
        self.project.save()
        self.check(repo=repo_json(owner_id=VICTIM, owner_type="Organization", name="team/app"),
                   contributors=[[person(commits=300)]])
        self.assertFalse(RepoLink.objects.exists())  # nothing stored, so nothing blocks the real team

    # k. Bot-only commits; spoofed author emails in an own copy.
    def test_k_bot_only_commits_need_review(self):
        bot = {"id": 49699333, "login": "dependabot[bot]", "contributions": 300, "type": "Bot"}
        self.check(contributors=[[bot]], stats=[stats_entry(user_id=49699333, user_type="Bot", weeks=[(5, 50, 5)] * 9)])
        link = RepoLink.objects.get()
        self.assertEqual(link.review_state, RepoLink.Review.NEEDS_REVIEW)
        self.assertEqual(link.active_weeks, 0)

    def test_k_rewritten_history_with_kept_dates_needs_review(self):
        # Author emails rewritten to the user's own, original dates kept: the history predates the repository.
        self.check(repo=repo_json(created_at="2026-09-01T00:00:00Z"), contributors=[[person(commits=700)]],
                   root=[commit("2020-02-02T00:00:00Z")])
        self.assertEqual(self.link_state(), RepoLink.Review.NEEDS_REVIEW)


class DomainAttackTests(TestCase):
    """Спроби обдурити перевірку домену."""
    def setUp(self):
        self.owner = make_user("ann")

    def live(self, project, days_ago=0):
        row = verification_for(project, create=True)
        when = timezone.now() - timedelta(days=days_ago)
        row.status, row.verified_at, row.last_confirmed_at = V.Status.VERIFIED, when, when
        row.save()
        return row

    # h. Someone else's repository plus an unrelated own domain.
    def test_h_foreign_repo_with_own_domain_is_an_unverified_link(self):
        project = make_project(self.owner, live_url="https://ann-site.com/", repo_full_name="victim/app")
        self.live(project)
        marks = compute_hallmarks(fresh(project))
        self.assertTrue(marks["live"].earned)  # Live is about the domain only
        self.assertFalse(marks["authored"].earned)
        self.assertIsNone(repo_domain_link(fresh(project)))
        response = self.client.get(project.get_absolute_url())
        self.assertContains(response, "Unverified link")
        self.assertContains(response, "victim/app is not verified. It is the author&#x27;s own link.")

    # i. Verified domain later redirects to another host; shared-host apex domains.
    def test_i_redirect_to_another_host_counts_as_down(self):
        project = make_project(self.owner, live_url="https://ann-site.com/")
        self.live(project)
        moved = FetchResult(url="https://someone-else.com/", status_code=200, headers=httpx.Headers(), content=b"")
        with patch.object(uptime, "safe_fetch", return_value=moved):
            check = uptime.check_project(project)
        self.assertFalse(check.ok)
        self.assertEqual(check.error, uptime.OTHER_HOST)

    def test_i_shared_host_apex_is_refused(self):
        for apex in ("github.io", "vercel.app", "netlify.app", "pages.dev", "herokuapp.com"):
            project = make_project(self.owner, name=apex, live_url=f"https://{apex}/")
            row = verification_for(project, create=True)
            with self.subTest(apex=apex), fake_dns({apex: [f"shipmark-verify={row.token}"]}), \
                    self.assertRaises(DomainCheckError) as ctx:
                verify(row, "dns")
            self.assertEqual(ctx.exception.code, "shared_host")

    # j. One token reused across projects or users; two users claiming the same domain.
    def test_j_token_of_another_project_does_not_verify(self):
        first = make_project(self.owner, name="One", live_url="https://ann-site.com/")
        first_row = verification_for(first, create=True)
        second = make_project(self.owner, name="Two", live_url="https://ann-other.com/")
        row = verification_for(second, create=True)
        with fake_dns({"ann-other.com": [f"shipmark-verify={first_row.token}"]}), self.assertRaises(DomainCheckError):
            verify(row, "dns")

    def test_j_second_user_cannot_verify_a_verified_domain(self):
        self.live(make_project(self.owner, live_url="https://ann-site.com/"))
        bob_project = make_project(make_user("bob"), name="Bob", live_url="https://www.ann-site.com/")
        row = verification_for(bob_project, create=True)
        with fake_dns({"www.ann-site.com": [f"shipmark-verify={row.token}"]}), self.assertRaises(DomainCheckError) as ctx:
            verify(row, "dns")
        self.assertEqual(ctx.exception.code, "taken")

    # l. Uptime counting a parking page or a redirect as up.
    def test_l_parking_redirect_counts_as_down(self):
        project = make_project(self.owner, live_url="https://ann-site.com/")
        self.live(project)
        parked = FetchResult(url="https://parking-service.example/ann-site.com", status_code=200,
                             headers=httpx.Headers(), content=b"")
        with patch.object(uptime, "safe_fetch", return_value=parked):
            self.assertFalse(uptime.check_project(project).ok)

    def test_l_expired_domain_loses_live_at_reverification(self):
        project = make_project(self.owner, live_url="https://ann-site.com/")
        row = self.live(project, days_ago=31)
        with fake_dns({"ann-site.com": ["parked-by-registrar"]}):
            self.assertEqual(domain.reverify(row), "removed")
        self.assertFalse(compute_hallmarks(fresh(project))["live"].earned)

    def test_l_parking_page_on_the_same_host_limit(self):
        # A parking page served from the verified domain itself answers 200: it counts as up. Live still needs
        # the token, which a registrar's parking page does not have, so Live (and Steady) end at re-verification.
        project = make_project(self.owner, live_url="https://ann-site.com/")
        self.live(project)
        same = FetchResult(url="https://ann-site.com/", status_code=200, headers=httpx.Headers(), content=b"")
        with patch.object(uptime, "safe_fetch", return_value=same):
            self.assertTrue(uptime.check_project(project).ok)
        self.assertEqual(UptimeCheck.objects.count(), 1)

import base64
from io import StringIO
from unittest.mock import patch

import httpx
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from moderation.models import AuditLog
from projects.forms import ProjectForm
from projects.models import Project
from projects.proof import compute_hallmarks
from projects.tests import make_project, make_user

from .models import RepoLink
from .repo import AUTHORED, FORK, NOT_YOURS, RepoCheckError, repo_token_for, run_check

User = get_user_model()
REAL_CLIENT = httpx.Client
ME = 1001  # the signed-in user's GitHub id in these tests


def repo_json(owner_id=ME, owner_type="User", private=False, fork=False, name="me/tool", repo_id=77, created_at=None):
    login = name.split("/")[0]
    return {"id": repo_id, "full_name": name, "private": private, "fork": fork, "created_at": created_at,
            "owner": {"id": owner_id, "login": login, "type": owner_type}}


def commit(date, sha=""):
    return {"sha": sha, "commit": {"author": {"date": date}}}


def stats_entry(user_id=ME, weeks=(), user_type="User"):
    """GitHub /stats/contributors entry. weeks: (commits, additions, deletions) per week."""
    return {"author": {"id": user_id, "type": user_type}, "total": sum(c for c, _a, _d in weeks),
            "weeks": [{"w": 1700000000 + i * 604800, "c": c, "a": a, "d": d} for i, (c, a, d) in enumerate(weeks)]}


def mock_github(repo=None, repo_status=200, contributors=None, commits=None, last_page=None, extra=None,
                root=None, stats=None):
    """Patch httpx.Client so GitHub is answered from memory. Returns the list of requested paths.

    root: the commit list for the whole branch (no author filter); stats: /stats/contributors body, or 202.
    """
    seen = []
    contributors = contributors if contributors is not None else []
    commits = commits or [commit("2024-05-01T10:00:00Z")]

    def handler(request):
        path, params = request.url.path, dict(request.url.params)
        seen.append(path + ("?" + str(request.url.query, "ascii") if request.url.query else ""))
        if extra and path in extra:
            return extra[path](request)
        if path.endswith("/stats/contributors"):
            return httpx.Response(202, json={}) if stats == 202 else httpx.Response(200, json=stats or [])
        if path.endswith("/commits") and "author" not in params and root is not None:
            return httpx.Response(200, json=root)
        if path.endswith("/contributors"):
            page = int(params.get("page", 1))
            return httpx.Response(200, json=contributors[page - 1] if page <= len(contributors) else [])
        if path.endswith("/commits"):
            headers = {}
            if last_page and params.get("page") is None:
                headers["Link"] = f'<https://api.github.com/x/commits?author=a&per_page=1&page={last_page}>; rel="last"'
            body = commits if params.get("page") is None else [commit("2023-01-02T00:00:00Z")]
            return httpx.Response(200, json=body, headers=headers)
        return httpx.Response(repo_status, json=repo if repo is not None else repo_json())

    def factory(**kwargs):
        return REAL_CLIENT(transport=httpx.MockTransport(handler), **kwargs)

    return patch("verification.repo.httpx.Client", side_effect=factory), seen


def person(user_id=ME, commits=3, login="me"):
    return {"id": user_id, "login": login, "contributions": commits}


class RepoCheckTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user("me")
        SocialAccount.objects.create(user=self.user, provider="github", uid=str(ME))
        self.project = make_project(self.user, repo_full_name="me/tool")

    def check(self, **mock_args):
        patcher, seen = mock_github(**mock_args)
        with patcher:
            return run_check(self.project, ME)


class AuthorshipRuleTests(RepoCheckTestCase):
    def test_owner_is_authored(self):
        result = self.check(contributors=[[person()]])
        self.assertEqual(result.outcome, AUTHORED)
        link = RepoLink.objects.get(project=self.project)
        self.assertTrue(link.is_owner)
        self.assertTrue(link.is_verified)
        self.assertTrue(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)
        self.assertTrue(AuditLog.objects.filter(action="hallmark.authored.earned").exists())

    def test_owner_gets_commit_count_and_dates(self):
        result = self.check(contributors=[[person(commits=25)]], last_page=25)
        self.assertEqual(result.outcome, AUTHORED)
        link = RepoLink.objects.get(project=self.project)
        self.assertEqual(link.user_commit_count, 25)
        self.assertEqual(link.last_commit_at.year, 2024)
        self.assertEqual(link.first_commit_at.year, 2023)

    def test_commits_in_someone_elses_repo_are_not_enough(self):
        self.project.repo_full_name = "acme/lib"
        result = self.check(repo=repo_json(owner_id=5, owner_type="Organization", name="acme/lib"),
                            contributors=[[person(user_id=5, commits=900, login="boss"), person(commits=500)]])
        self.assertEqual(result.outcome, NOT_YOURS)
        self.assertFalse(RepoLink.objects.exists())
        self.assertFalse(compute_hallmarks(self.project)["authored"].earned)

    def test_organisation_repo_is_not_owned_by_a_person(self):
        result = self.check(repo=repo_json(owner_id=ME, owner_type="Organization"), contributors=[[person()]])
        self.assertEqual(result.outcome, NOT_YOURS)

    def test_someone_elses_repo_with_no_commits(self):
        result = self.check(repo=repo_json(owner_id=5, name="acme/lib"), contributors=[[person(user_id=5)]])
        self.assertEqual(result.outcome, NOT_YOURS)
        self.assertFalse(RepoLink.objects.exists())

    def test_fork_is_refused_even_with_own_commits(self):
        result = self.check(repo=repo_json(fork=True), contributors=[[person(user_id=5), person(commits=50)]])
        self.assertEqual(result.outcome, FORK)
        self.assertFalse(RepoLink.objects.exists())

    def test_user_found_on_second_contributors_page(self):
        first_page = [person(user_id=2000 + i, commits=50) for i in range(100)]
        result = self.check(contributors=[first_page, [person(commits=12)]])
        self.assertEqual(result.outcome, AUTHORED)
        self.assertEqual(result.facts.commit_count, 12)

    def test_failed_recheck_removes_the_old_link(self):
        self.check(contributors=[[person(commits=3)]])
        self.assertTrue(RepoLink.objects.exists())
        self.check(repo=repo_json(owner_id=5), contributors=[[person(commits=3)]])  # transferred away
        self.assertFalse(RepoLink.objects.exists())


class ErrorTests(RepoCheckTestCase):
    def assertCode(self, code, **mock_args):
        with self.assertRaises(RepoCheckError) as ctx:
            self.check(**mock_args)
        self.assertEqual(ctx.exception.code, code)
        return ctx.exception

    def test_private_repo(self):
        self.assertCode("private", repo=repo_json(private=True))
        self.assertFalse(RepoLink.objects.exists())

    def test_not_found(self):
        self.assertCode("not_found", repo_status=404, repo={"message": "Not Found"})

    def test_renamed_repo_redirect(self):
        self.assertCode("moved", repo_status=301, repo={})

    def test_rate_limit_is_reported_not_raised_as_crash(self):
        def limited(request):
            return httpx.Response(403, json={"message": "API rate limit exceeded"},
                                  headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(timezone.now().timestamp()) + 600)})
        error = self.assertCode("rate_limited", extra={"/repos/me/tool": limited})
        self.assertIn("min", error.message)

    def test_github_error_keeps_existing_link(self):
        self.check(contributors=[[person()]])
        self.assertCode("unavailable", extra={"/repos/me/tool": lambda r: httpx.Response(502)})
        self.assertTrue(RepoLink.objects.exists())

    def test_network_failure(self):
        def boom(request):
            raise httpx.ConnectTimeout("slow")
        self.assertCode("unavailable", extra={"/repos/me/tool": boom})

    def test_garbage_json(self):
        self.assertCode("unavailable", extra={"/repos/me/tool": lambda r: httpx.Response(200, text="<html>")})

    def test_bad_name_never_reaches_github(self):
        self.project.repo_full_name = "../../orgs/x"
        patcher, seen = mock_github()
        with patcher, self.assertRaises(RepoCheckError) as ctx:
            run_check(self.project, ME)
        self.assertEqual(ctx.exception.code, "invalid")
        self.assertEqual(seen, [])

    def test_repo_linked_to_another_project_is_rejected(self):
        other_user = make_user("other")
        other = make_project(other_user, name="Other")
        RepoLink.objects.create(project=other, repo_full_name="Me/Tool", github_repo_id=77, is_owner=True,
                                checked_at=timezone.now())
        error = self.assertCode("taken", contributors=[[person()]])
        self.assertIn("another project", error.message)
        self.assertFalse(RepoLink.objects.filter(project=self.project).exists())

    def test_same_repo_renamed_is_still_the_same_repo(self):
        other = make_project(make_user("other"), name="Other")
        RepoLink.objects.create(project=other, repo_full_name="me/old-name", github_repo_id=77, is_owner=True,
                                checked_at=timezone.now())
        self.assertCode("taken", contributors=[[person()]])  # same GitHub id, new name

    def test_rechecking_own_repo_is_fine(self):
        self.check(contributors=[[person()]])
        self.assertEqual(self.check(contributors=[[person()]]).outcome, AUTHORED)


class RepoCheckViewTests(RepoCheckTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("projects:repo_check", args=["me", self.project.slug])
        self.client.force_login(self.user)

    def post(self, **mock_args):
        patcher, _seen = mock_github(**mock_args)
        with patcher:
            return self.client.post(self.url, follow=True)

    def test_success_message_and_hallmark(self):
        response = self.post(contributors=[[person()]])
        self.assertContains(response, "Repo owner earned")
        self.assertTrue(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_not_owner_message(self):
        response = self.post(repo=repo_json(owner_id=5), contributors=[[person(commits=90)]])
        self.assertContains(response, "not owned by your personal GitHub account")

    def test_fork_message(self):
        self.assertContains(self.post(repo=repo_json(fork=True)), "Forks cannot earn Repo owner")

    def test_review_message_is_neutral(self):
        response = self.post(contributors=[[]])  # no commits by the owner
        self.assertContains(response, "after a short manual review")
        self.assertFalse(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_limited_to_one_per_ten_minutes(self):
        self.post(contributors=[[person()]])
        patcher, seen = mock_github(contributors=[[person()]])
        with patcher:
            response = self.client.post(self.url, follow=True)
        self.assertEqual(seen, [])  # GitHub was not called
        self.assertContains(response, "10 minutes")

    def test_no_repo_set_does_not_use_up_the_limit(self):
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="")
        self.assertContains(self.client.post(self.url, follow=True), "Add a GitHub repository")
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="me/tool")
        self.assertContains(self.post(contributors=[[person()]]), "Repo owner earned")

    def test_user_without_github_account(self):
        SocialAccount.objects.all().delete()
        self.assertContains(self.client.post(self.url, follow=True), "Sign in with GitHub")

    def test_other_users_get_404_and_anonymous_is_redirected(self):
        self.client.force_login(make_user("intruder"))
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_suspended_user_cannot_check(self):
        User.objects.filter(pk=self.user.pk).update(is_suspended=True)
        self.client.force_login(User.objects.get(pk=self.user.pk))
        self.assertEqual(self.client.post(self.url).status_code, 403)


class StaleLinkTests(RepoCheckTestCase):
    def test_changing_the_repo_name_removes_the_hallmark(self):
        self.check(contributors=[[person()]])
        project = Project.objects.get(pk=self.project.pk)
        data = {"name": project.name, "tagline": project.tagline, "description": "", "live_url": "",
                "repo_full_name": "me/other-tool", "tags_text": ""}
        form = ProjectForm(data, instance=project)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(RepoLink.objects.exists())
        self.assertFalse(compute_hallmarks(Project.objects.get(pk=project.pk))["authored"].earned)

    def test_link_for_a_different_name_does_not_count(self):
        self.check(contributors=[[person()]])
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="someone/else")
        self.assertFalse(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_name_match_ignores_case(self):
        self.check(contributors=[[person()]])
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="ME/Tool")
        self.assertTrue(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)


class RepoIdentityTests(RepoCheckTestCase):
    """Repositories are compared by GitHub ids (repo id, owner id), never by names."""

    def test_owner_id_is_stored(self):
        self.check(contributors=[[person(commits=3)]])
        self.assertEqual(RepoLink.objects.get().github_owner_id, ME)

    def test_renamed_repo_is_followed_by_id_and_project_name_updated(self):
        self.check(contributors=[[person(commits=3)]])
        moved = {"/repos/me/tool": lambda request: httpx.Response(
            301, headers={"location": "https://api.github.com/repositories/77"})}
        patcher, seen = mock_github(repo=repo_json(name="me/tool-v2"), contributors=[[person(commits=3)]], extra=moved)
        with patcher:
            result = run_check(self.project, ME)
        self.assertEqual(result.outcome, AUTHORED)
        self.assertIn("/repositories/77", seen)
        self.project.refresh_from_db()
        self.assertEqual(self.project.repo_full_name, "me/tool-v2")
        self.assertEqual(RepoLink.objects.get().repo_full_name, "me/tool-v2")
        self.assertTrue(AuditLog.objects.filter(action="repo.renamed").exists())
        self.assertTrue(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_deleted_and_recreated_repo_is_a_new_repository(self):
        self.check(contributors=[[person(commits=3)]])
        self.check(repo=repo_json(repo_id=999), contributors=[[person(commits=3)]])
        entry = AuditLog.objects.get(action="hallmark.authored.removed")
        self.assertEqual(entry.metadata["reason"], "recreated")
        self.assertEqual(RepoLink.objects.get().github_repo_id, 999)

    def test_repo_transferred_away_removes_the_mark_and_logs(self):
        self.check(contributors=[[person(commits=3)]])
        result = self.check(repo=repo_json(owner_id=5), contributors=[[person(commits=3)]])
        self.assertEqual(result.outcome, NOT_YOURS)
        self.assertFalse(RepoLink.objects.exists())
        reasons = [e.metadata["reason"] for e in AuditLog.objects.filter(action="hallmark.authored.removed")]
        self.assertEqual(reasons, ["transferred"])

    def test_every_removal_is_logged(self):
        self.check(contributors=[[person(commits=3)]])
        with self.assertRaises(RepoCheckError):
            self.check(repo=repo_json(private=True))
        entry = AuditLog.objects.get(action="hallmark.authored.removed")
        self.assertEqual(entry.metadata["reason"], "private")
        self.assertEqual(entry.metadata["repo_id"], 77)

    def test_changing_the_repo_in_the_form_logs_the_removal(self):
        self.check(contributors=[[person(commits=3)]])
        form = ProjectForm({"name": "Tallyhook", "tagline": "A tagline", "repo_full_name": "me/other"},
                           instance=self.project)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(RepoLink.objects.exists())
        self.assertEqual(AuditLog.objects.get(action="hallmark.authored.removed").metadata["reason"], "repo_changed")


class BackfillRepoFactsTests(RepoCheckTestCase):
    def run_command(self, *args, **mock_args):
        out = StringIO()
        patcher, seen = mock_github(**mock_args)
        with patcher:
            call_command("backfill_repo_facts", *args, stdout=out)
        return out.getvalue(), seen

    def old_link(self, is_owner=True, **extra):
        return RepoLink.objects.create(project=self.project, repo_full_name="me/tool", github_repo_id=77,
                                       is_owner=is_owner, checked_at=timezone.now(), **extra)

    def earned(self):
        return compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned

    def test_fills_facts_and_keeps_the_mark(self):
        link = self.old_link()
        output, _seen = self.run_command(repo=repo_json(created_at="2024-04-01T00:00:00Z"), contributors=[[person()]],
                                         root=[commit("2024-04-02T00:00:00Z", "a" * 40)],
                                         stats=[stats_entry(weeks=[(2, 10, 1), (1, 3, 0)])])
        link.refresh_from_db()
        self.assertEqual(link.github_owner_id, ME)
        self.assertEqual(link.root_commit_sha, "a" * 40)
        self.assertEqual(link.active_weeks, 2)
        self.assertEqual(link.repo_created_at.year, 2024)
        self.assertIn("Filled 1", output)
        self.assertTrue(self.earned())
        self.assertIn("Filled 0", self.run_command()[0])  # done links are skipped

    def test_review_facts_set_needs_review_and_log(self):
        self.old_link()
        output, _seen = self.run_command(repo=repo_json(created_at="2025-01-01T00:00:00Z"), contributors=[[person()]],
                                         root=[commit("2019-01-01T00:00:00Z", "b" * 40)])
        link = RepoLink.objects.get()
        self.assertEqual(link.review_state, RepoLink.Review.NEEDS_REVIEW)
        self.assertEqual(link.review_reasons, ["imported_history"])
        self.assertIn("needs review 1", output)
        self.assertTrue(AuditLog.objects.filter(action="hallmark.authored.needs_review").exists())
        self.assertFalse(self.earned())

    def test_changed_repo_needs_recheck_and_is_not_deleted(self):
        self.old_link()
        output, _seen = self.run_command(repo=repo_json(owner_id=5), contributors=[[person()]])
        link = RepoLink.objects.get()
        self.assertEqual(link.review_state, RepoLink.Review.NEEDS_RECHECK)
        self.assertIn("not_owner", output)
        self.assertEqual(AuditLog.objects.get(action="hallmark.authored.needs_recheck").metadata["reason"], "not_owner")

    def test_gone_repo_needs_recheck(self):
        self.old_link()
        self.run_command(repo_status=404, repo={"message": "Not Found"})
        self.assertEqual(RepoLink.objects.get().review_state, RepoLink.Review.NEEDS_RECHECK)

    def test_rename_is_followed(self):
        self.old_link()
        self.run_command(repo=repo_json(name="me/renamed"), contributors=[[person()]])
        self.project.refresh_from_db()
        self.assertEqual(self.project.repo_full_name, "me/renamed")
        self.assertTrue(self.earned())

    def test_rate_limit_and_errors_change_nothing(self):
        link = self.old_link()
        limited = {"/repos/me/tool": lambda r: httpx.Response(
            403, json={"message": "API rate limit exceeded"}, headers={"x-ratelimit-remaining": "0"})}
        self.assertIn("Rate limited", self.run_command(extra=limited)[0])
        self.run_command(extra={"/repos/me/tool": lambda r: httpx.Response(502)})
        link.refresh_from_db()
        self.assertIsNone(link.github_owner_id)
        self.assertEqual(link.review_state, "")
        self.assertTrue(self.earned())

    def test_dry_run_writes_nothing(self):
        link = self.old_link()
        self.run_command("--dry-run", repo=repo_json(owner_id=5), contributors=[[person()]])
        link.refresh_from_db()
        self.assertEqual(link.review_state, "")
        self.assertIsNone(link.github_owner_id)


class ReviewRuleTests(RepoCheckTestCase):
    """Facts that send a link to a manual review instead of earning Repo owner at once."""

    def test_no_commits_by_the_owner(self):
        result = self.check(contributors=[[person(user_id=5, commits=40)]])
        self.assertEqual(result.facts.review_reasons, ["no_owner_commits"])
        self.assertEqual(RepoLink.objects.get().review_state, RepoLink.Review.NEEDS_REVIEW)
        mark = compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"]
        self.assertFalse(mark.earned)
        self.assertIn("routine manual review", mark.reason)

    def test_imported_history(self):
        self.check(repo=repo_json(created_at="2025-06-01T00:00:00Z"), contributors=[[person()]],
                   root=[commit("2024-01-01T00:00:00Z")])
        self.assertEqual(RepoLink.objects.get().review_reasons, ["imported_history"])

    def test_history_a_few_weeks_older_than_the_repo_is_normal(self):
        self.check(repo=repo_json(created_at="2025-06-01T00:00:00Z"), contributors=[[person()]],
                   root=[commit("2025-04-15T00:00:00Z")])
        link = RepoLink.objects.get()
        self.assertEqual(link.review_reasons, [])
        self.assertTrue(link.is_verified)

    def test_duplicate_history(self):
        other = make_project(make_user("other"), name="Other")
        RepoLink.objects.create(project=other, repo_full_name="other/copy", github_repo_id=5, is_owner=True,
                                root_commit_sha="c" * 40, checked_at=timezone.now())
        self.check(contributors=[[person()]], root=[commit("2024-05-01T00:00:00Z", "c" * 40)])
        self.assertEqual(RepoLink.objects.get(project=self.project).review_reasons, ["duplicate_history"])

    def test_approval_survives_the_same_reasons_but_not_new_ones(self):
        self.check(contributors=[[]])
        RepoLink.objects.update(review_state=RepoLink.Review.APPROVED)
        self.check(contributors=[[]])
        self.assertEqual(RepoLink.objects.get().review_state, RepoLink.Review.APPROVED)
        self.check(repo=repo_json(created_at="2025-06-01T00:00:00Z"), contributors=[[]],
                   root=[commit("2020-01-01T00:00:00Z")])
        self.assertEqual(RepoLink.objects.get().review_state, RepoLink.Review.NEEDS_REVIEW)

    def test_reasons_gone_clears_the_review(self):
        self.check(contributors=[[]])
        self.check(contributors=[[person()]])
        link = RepoLink.objects.get()
        self.assertTrue(link.is_verified)
        self.assertTrue(AuditLog.objects.filter(action="hallmark.authored.earned").exists())

    def test_recheck_state_is_resolved_by_a_full_check(self):
        RepoLink.objects.create(project=self.project, repo_full_name="me/tool", github_repo_id=77, is_owner=False,
                                user_commit_count=12, review_state=RepoLink.Review.NEEDS_RECHECK, checked_at=timezone.now())
        self.assertIn("checked again", compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].reason)
        self.check(contributors=[[person()]])
        self.assertTrue(RepoLink.objects.get().is_verified)


class ActivityFactTests(RepoCheckTestCase):
    def weeks(self, stats):
        return self.check(contributors=[[person()]], stats=stats).facts.active_weeks

    def test_counts_weeks_with_changed_lines_only(self):
        self.assertEqual(self.weeks([stats_entry(weeks=[(3, 40, 2), (1, 0, 0), (0, 0, 0), (2, 1, 1)])]), 2)

    def test_bots_and_other_people_do_not_count(self):
        stats = [stats_entry(user_id=5, weeks=[(9, 9, 9)] * 5), stats_entry(user_id=ME, user_type="Bot", weeks=[(1, 1, 1)])]
        self.assertEqual(self.weeks(stats), 0)

    def test_still_computing_is_pending_and_keeps_the_last_number(self):
        self.weeks([stats_entry(weeks=[(1, 5, 0)] * 3)])
        self.assertIsNone(self.weeks(202))
        self.assertEqual(RepoLink.objects.get().active_weeks, 3)  # pending never wipes a known fact
        self.assertTrue(RepoLink.objects.get().is_verified)  # and never blocks the mark

    def test_huge_repository_without_line_counts(self):
        self.assertEqual(self.weeks([stats_entry(weeks=[(5, 0, 0), (2, 0, 0)])]), 2)

    def test_empty_repository(self):
        empty = {"/repos/me/tool/commits": lambda r: httpx.Response(409, json={"message": "Git Repository is empty."})}
        result = self.check(extra=empty, contributors=[[]])
        self.assertEqual(result.outcome, AUTHORED)
        self.assertEqual(result.facts.root_commit_sha, "")
        self.assertEqual(RepoLink.objects.get().review_reasons, ["no_owner_commits"])


class TokenFileTests(RepoCheckTestCase):
    """Organisation and team repositories: the project's .shipmark-verify file proves write access."""

    def setUp(self):
        super().setUp()
        self.project.repo_full_name = "acme/app"
        self.project.save()
        self.token = repo_token_for(self.project)
        self.org_repo = repo_json(owner_id=5, owner_type="Organization", name="acme/app")

    def file(self, text=None, status=200, size=None):
        body = text if text is not None else self.token
        payload = {"type": "file", "encoding": "base64", "size": size if size is not None else len(body),
                   "content": base64.b64encode(body.encode()).decode()}
        return {"/repos/acme/app/contents/.shipmark-verify": lambda r: httpx.Response(status, json=payload)}

    def test_org_repo_with_the_token_file_earns(self):
        result = self.check(repo=self.org_repo, contributors=[[person()]], extra=self.file(f"  {self.token}\n"))
        self.assertEqual(result.outcome, AUTHORED)
        link = RepoLink.objects.get()
        self.assertTrue(link.token_file_found)
        self.assertFalse(link.is_owner)
        mark = compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"]
        self.assertTrue(mark.earned)
        self.assertIn("verification file", mark.reason)

    def test_wrong_or_missing_file_is_not_yours_and_stores_nothing(self):
        for extra in (self.file("0" * 32), self.file(status=404), self.file(size=5000), {}):
            with self.subTest(extra=bool(extra)):
                self.assertEqual(self.check(repo=self.org_repo, contributors=[[person()]], extra=extra).outcome, NOT_YOURS)
                self.assertFalse(RepoLink.objects.exists())

    def test_another_projects_token_does_not_work(self):
        other = make_project(make_user("other"), name="Other", repo_full_name="acme/app")
        other_token = repo_token_for(other)
        self.assertNotEqual(other_token, self.token)
        result = self.check(repo=self.org_repo, contributors=[[person()]], extra=self.file(other_token))
        self.assertEqual(result.outcome, NOT_YOURS)

    def test_fork_with_the_token_file_is_still_refused(self):
        fork = repo_json(owner_id=ME, fork=True, name="acme/app")
        self.assertEqual(self.check(repo=fork, contributors=[[person()]], extra=self.file()).outcome, FORK)

    def test_contributor_without_the_file_cannot_squat(self):
        self.check(repo=self.org_repo, contributors=[[person(commits=400)]])
        self.assertFalse(RepoLink.objects.exists())  # nothing stored, so the real team can still link it

    def test_tokens_are_random_unique_and_kept(self):
        self.assertRegex(self.token, r"^[0-9a-f]{32}$")
        self.assertEqual(repo_token_for(Project.objects.get(pk=self.project.pk)), self.token)
        tokens = {repo_token_for(make_project(self.user, name=f"P{i}")) for i in range(20)}
        self.assertEqual(len(tokens), 20)
        self.assertNotIn(self.token, tokens)

    def test_owner_without_a_token_spends_no_extra_request(self):
        project = make_project(self.user, name="Mine", repo_full_name="me/tool")
        patcher, seen = mock_github(contributors=[[person()]])
        with patcher:
            run_check(project, ME)
        self.assertFalse(any("contents" in path for path in seen))

    def test_edit_page_shows_the_file_and_token(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("projects:edit", args=["me", self.project.slug]))
        self.assertContains(response, ".shipmark-verify")
        self.assertContains(response, self.token)


class TokenFileRecheckTests(RepoCheckTestCase):
    def setUp(self):
        super().setUp()
        self.project.repo_full_name = "acme/app"
        self.project.save()
        self.token = repo_token_for(self.project)
        self.org = repo_json(owner_id=5, owner_type="Organization", name="acme/app")
        payload = {"type": "file", "encoding": "base64", "size": 32, "content": base64.b64encode(self.token.encode()).decode()}
        self.with_file = {"/repos/acme/app/contents/.shipmark-verify": lambda r: httpx.Response(200, json=payload)}
        self.check(repo=self.org, contributors=[[person()]], extra=self.with_file)
        self.assertTrue(RepoLink.objects.get().is_verified)

    def reverify(self, extra):
        from .repo import reverify_link

        patcher, _seen = mock_github(repo=self.org, contributors=[[person()]], extra=extra)
        with patcher:
            return reverify_link(RepoLink.objects.select_related("project__owner").get())

    def test_file_still_there_is_confirmed(self):
        self.assertEqual(self.reverify(self.with_file), "confirmed")

    def test_file_removed_removes_the_mark_with_auditlog(self):
        gone = {"/repos/acme/app/contents/.shipmark-verify": lambda r: httpx.Response(404, json={})}
        self.assertEqual(self.reverify(gone), "removed")
        self.assertEqual(AuditLog.objects.filter(action="hallmark.authored.removed").get().metadata["reason"],
                         "token_file_missing")

    def test_github_error_on_the_file_keeps_the_mark(self):
        broken = {"/repos/acme/app/contents/.shipmark-verify": lambda r: httpx.Response(502)}
        self.assertEqual(self.reverify(broken), "kept")
        self.assertTrue(RepoLink.objects.get().is_verified)

    def test_panel_says_verification_file(self):
        from projects.proof import checked_facts

        project = Project.objects.select_related("repo_link").get(pk=self.project.pk)
        self.assertIn("verification file", checked_facts(project)[0].text)

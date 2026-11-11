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
from .repo import AUTHORED, NOT_YOURS, TOO_FEW, RepoCheckError, run_check

User = get_user_model()
REAL_CLIENT = httpx.Client
ME = 1001  # the signed-in user's GitHub id in these tests


def repo_json(owner_id=ME, owner_type="User", private=False, fork=False, name="me/tool", repo_id=77):
    login = name.split("/")[0]
    return {"id": repo_id, "full_name": name, "private": private, "fork": fork,
            "owner": {"id": owner_id, "login": login, "type": owner_type}}


def mock_github(repo=None, repo_status=200, contributors=None, commits=None, last_page=None, extra=None):
    """Patch httpx.Client so GitHub is answered from memory. Returns the list of requested paths."""
    seen = []
    contributors = contributors if contributors is not None else []
    commits = commits or [{"commit": {"author": {"date": "2024-05-01T10:00:00Z"}}}]

    def handler(request):
        path, params = request.url.path, dict(request.url.params)
        seen.append(path + ("?" + str(request.url.query, "ascii") if request.url.query else ""))
        if extra and path in extra:
            return extra[path](request)
        if path.endswith("/contributors"):
            page = int(params.get("page", 1))
            return httpx.Response(200, json=contributors[page - 1] if page <= len(contributors) else [])
        if path.endswith("/commits"):
            headers = {}
            if last_page and params.get("page") is None:
                headers["Link"] = f'<https://api.github.com/x/commits?author=a&per_page=1&page={last_page}>; rel="last"'
            body = commits if params.get("page") is None else [{"commit": {"author": {"date": "2023-01-02T00:00:00Z"}}}]
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
    def test_owner_is_authored_without_commits(self):
        result = self.check(contributors=[[]])
        self.assertEqual(result.outcome, AUTHORED)
        link = RepoLink.objects.get(project=self.project)
        self.assertTrue(link.is_owner)
        self.assertTrue(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_owner_gets_commit_count_and_dates(self):
        result = self.check(contributors=[[person(commits=25)]], last_page=25)
        self.assertEqual(result.outcome, AUTHORED)
        link = RepoLink.objects.get(project=self.project)
        self.assertEqual(link.user_commit_count, 25)
        self.assertEqual(link.last_commit_at.year, 2024)
        self.assertEqual(link.first_commit_at.year, 2023)

    def test_contributor_with_ten_commits_is_authored(self):
        self.project.repo_full_name = "acme/lib"
        result = self.check(repo=repo_json(owner_id=5, owner_type="Organization", name="acme/lib"),
                            contributors=[[person(user_id=5, commits=900, login="boss"), person(commits=10)]])
        self.assertEqual(result.outcome, AUTHORED)
        link = RepoLink.objects.get(project=self.project)
        self.assertFalse(link.is_owner)
        self.assertEqual(link.user_commit_count, 10)

    def test_nine_commits_is_not_authored_and_not_stored(self):
        result = self.check(repo=repo_json(owner_id=5, name="acme/lib"), contributors=[[person(commits=9)]])
        self.assertEqual(result.outcome, TOO_FEW)
        self.assertEqual(result.facts.commit_count, 9)
        self.assertFalse(RepoLink.objects.exists())
        self.assertFalse(compute_hallmarks(self.project)["authored"].earned)

    def test_someone_elses_repo_with_no_commits(self):
        result = self.check(repo=repo_json(owner_id=5, name="acme/lib"), contributors=[[person(user_id=5)]])
        self.assertEqual(result.outcome, NOT_YOURS)
        self.assertFalse(RepoLink.objects.exists())

    def test_fork_does_not_count_as_owned(self):
        result = self.check(repo=repo_json(fork=True), contributors=[[person(user_id=5)]])
        self.assertEqual(result.outcome, NOT_YOURS)

    def test_user_found_on_second_contributors_page(self):
        first_page = [person(user_id=1000 + i, commits=50) for i in range(100)]
        result = self.check(repo=repo_json(owner_id=5), contributors=[first_page, [person(commits=12)]])
        self.assertEqual(result.outcome, AUTHORED)

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
        error = self.assertCode("taken", contributors=[[]])
        self.assertIn("another project", error.message)
        self.assertFalse(RepoLink.objects.filter(project=self.project).exists())

    def test_same_repo_renamed_is_still_the_same_repo(self):
        other = make_project(make_user("other"), name="Other")
        RepoLink.objects.create(project=other, repo_full_name="me/old-name", github_repo_id=77, is_owner=True,
                                checked_at=timezone.now())
        self.assertCode("taken", contributors=[[]])  # same GitHub id, new name

    def test_rechecking_own_repo_is_fine(self):
        self.check(contributors=[[]])
        self.assertEqual(self.check(contributors=[[]]).outcome, AUTHORED)


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
        response = self.post(contributors=[[]])
        self.assertContains(response, "Repo owner earned")
        self.assertTrue(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_too_few_commits_message(self):
        response = self.post(repo=repo_json(owner_id=5), contributors=[[person(commits=9)]])
        self.assertContains(response, "You have 9 commits")

    def test_limited_to_one_per_ten_minutes(self):
        self.post(contributors=[[]])
        patcher, seen = mock_github(contributors=[[]])
        with patcher:
            response = self.client.post(self.url, follow=True)
        self.assertEqual(seen, [])  # GitHub was not called
        self.assertContains(response, "10 minutes")

    def test_no_repo_set_does_not_use_up_the_limit(self):
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="")
        self.assertContains(self.client.post(self.url, follow=True), "Add a GitHub repository")
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="me/tool")
        self.assertContains(self.post(contributors=[[]]), "Repo owner earned")

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
        self.check(contributors=[[]])
        project = Project.objects.get(pk=self.project.pk)
        data = {"name": project.name, "tagline": project.tagline, "description": "", "live_url": "",
                "repo_full_name": "me/other-tool", "tags_text": ""}
        form = ProjectForm(data, instance=project)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(RepoLink.objects.exists())
        self.assertFalse(compute_hallmarks(Project.objects.get(pk=project.pk))["authored"].earned)

    def test_link_for_a_different_name_does_not_count(self):
        self.check(contributors=[[]])
        Project.objects.filter(pk=self.project.pk).update(repo_full_name="someone/else")
        self.assertFalse(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_name_match_ignores_case(self):
        self.check(contributors=[[]])
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
        self.assertEqual(result.outcome, TOO_FEW)
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
    def run_command(self, **mock_args):
        out = StringIO()
        patcher, seen = mock_github(**mock_args)
        with patcher:
            call_command("backfill_repo_facts", stdout=out)
        return out.getvalue(), seen

    def old_link(self, is_owner=True):
        return RepoLink.objects.create(project=self.project, repo_full_name="me/tool", github_repo_id=77,
                                       is_owner=is_owner, checked_at=timezone.now())

    def test_fills_owner_id_by_repo_id(self):
        link = self.old_link()
        output, seen = self.run_command(extra={"/repositories/77": lambda r: httpx.Response(200, json=repo_json())})
        link.refresh_from_db()
        self.assertEqual(link.github_owner_id, ME)
        self.assertIn("Filled 1", output)
        self.assertEqual(seen, ["/repositories/77"])

    def test_owner_changed_is_left_alone_and_nothing_removed(self):
        link = self.old_link()
        output, _seen = self.run_command(extra={"/repositories/77": lambda r: httpx.Response(200, json=repo_json(owner_id=5))})
        link.refresh_from_db()
        self.assertIsNone(link.github_owner_id)
        self.assertIn("owner changed", output)
        self.assertTrue(compute_hallmarks(Project.objects.get(pk=self.project.pk))["authored"].earned)

    def test_gone_and_rate_limit_change_nothing(self):
        link = self.old_link()
        self.run_command(extra={"/repositories/77": lambda r: httpx.Response(404, json={})})
        output, _seen = self.run_command(extra={"/repositories/77": lambda r: httpx.Response(
            403, json={"message": "API rate limit exceeded"}, headers={"x-ratelimit-remaining": "0"})})
        self.assertIn("Rate limited", output)
        link.refresh_from_db()
        self.assertIsNone(link.github_owner_id)
        self.assertTrue(RepoLink.objects.filter(pk=link.pk).exists())

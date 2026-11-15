import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from projects.models import Project
from projects.tests import make_project, make_user
from social.models import Follow, Like
from verification.models import DomainVerification

from . import actions
from .models import AuditLog, Report
from .views import REPORT_LIMIT


class ModerationTestCase(TestCase):
    """Спільні дані для тестів модерації."""
    def setUp(self):
        cache.clear()
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")
        self.ana = make_user("ana")
        self.project = make_project(self.ana, name="Quillbox")
        self.visitor = make_user("visitor")


# ---------- Access ----------

class AdminAccessTests(ModerationTestCase):
    """Доступ до адмінки."""
    def test_anonymous_is_sent_to_the_admin_login(self):
        for url in (reverse("admin:index"), reverse("admin:accounts_user_changelist"),
                    reverse("admin:moderation_report_changelist")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("admin:login"), response["Location"])

    def test_signed_in_non_staff_cannot_open_the_admin(self):
        self.client.force_login(self.visitor)
        for url in (reverse("admin:index"), reverse("admin:projects_project_changelist"),
                    reverse("admin:moderation_auditlog_changelist")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("admin:login"), response["Location"])

    def test_non_staff_cannot_run_an_admin_action(self):
        self.client.force_login(self.visitor)
        response = self.client.post(reverse("admin:accounts_user_changelist"),
                                    {"action": "suspend", "_selected_action": [self.ana.pk]})
        self.assertEqual(response.status_code, 302)
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_suspended)

    def test_staff_without_permissions_gets_403_on_models(self):
        staff = make_user("clerk", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:accounts_user_changelist")).status_code, 403)

    def test_every_model_page_renders_for_a_superuser(self):
        # Rows for every model, so list_display, filters and the dashboard run on real data.
        Report.objects.create(reporter=self.visitor, project=self.project, target_repr=str(self.project),
                              reason=Report.Reason.SPAM)
        Follow.objects.create(follower=self.visitor, following=self.ana)
        Like.objects.create(user=self.visitor, project=self.project)
        DomainVerification.objects.create(project=self.project, domain="example.com", domain_key="example.com",
                                          token="t" * 32)
        actions.hide_project(self.project, self.boss)
        self.client.force_login(self.boss)
        names = ["accounts_user", "projects_project", "projects_buildlogentry", "projects_tag", "projects_tool",
                 "verification_repolink", "verification_domainverification", "verification_uptimecheck",
                 "moderation_report", "moderation_auditlog", "social_follow", "social_like",
                 "accounts_userbadge", "moderation_sanction", "news_newspost"]
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        for name in names:
            with self.subTest(model=name):
                response = self.client.get(reverse(f"admin:{name}_changelist"))
                self.assertEqual(response.status_code, 200)
                response = self.client.get(reverse(f"admin:{name}_changelist") + "?q=ana")
                self.assertEqual(response.status_code, 200)
        from accounts.models import UserBadge
        from news.models import NewsPost
        from .models import Sanction
        sanction = Sanction.objects.create(user=self.visitor, kind="mute", reason="x")
        post = NewsPost.objects.create(title="Hello", slug="hello", body="**Hi**")
        for name, obj in (("accounts_user", self.ana), ("projects_project", self.project),
                          ("moderation_report", Report.objects.get()), ("moderation_auditlog", AuditLog.objects.get()),
                          ("accounts_userbadge", UserBadge.objects.first()), ("moderation_sanction", sanction),
                          ("news_newspost", post)):
            with self.subTest(change=name):
                self.assertEqual(self.client.get(reverse(f"admin:{name}_change", args=[obj.pk])).status_code, 200)

    def test_dashboard_shows_the_numbers(self):
        Report.objects.create(reporter=self.visitor, project=self.project, target_repr="x", reason=Report.Reason.SPAM)
        self.client.force_login(self.boss)
        response = self.client.get(reverse("admin:index"))
        stats = {str(item["label"]): item["value"] for item in response.context["stats"]}
        self.assertEqual(stats["Users"], 3)
        self.assertEqual(stats["Published projects"], 1)
        self.assertEqual(stats["Signups, last 7 days"], 3)
        self.assertEqual(stats["Open reports"], 1)
        self.assertEqual(len(response.context["hallmark_stats"]), 3)

    def test_dashboard_does_not_count_projects_of_suspended_users(self):
        actions.suspend_user(self.ana, self.boss)
        self.client.force_login(self.boss)
        stats = {str(i["label"]): i["value"] for i in self.client.get(reverse("admin:index")).context["stats"]}
        self.assertEqual(stats["Published projects"], 0)


class AdminUrlTests(TestCase):
    """Адреса адмінки з ADMIN_URL."""
    def test_admin_lives_at_the_configured_address(self):
        self.assertEqual(reverse("admin:index"), "/" + settings.ADMIN_URL)

    def _import_prod(self, admin_url):
        from config.tests import S3_ENV

        env = {k: v for k, v in os.environ.items() if k != "ADMIN_URL"}
        env.update({"DJANGO_SETTINGS_MODULE": "config.settings.prod", "SECRET_KEY": "admin-test-only-" + "abcdefghijklmnopqrstuvwxyz0123456789" * 2,
                    "BAN_HASH_KEY": "b" * 50, "DATABASE_URL": "sqlite:////tmp/unused.sqlite3", **S3_ENV})
        if admin_url is not None:
            env["ADMIN_URL"] = admin_url
        return subprocess.run(
            [sys.executable, "-c", "import django.conf; django.conf.settings.ADMIN_URL"],
            cwd=Path(settings.BASE_DIR), env=env, capture_output=True, text=True,
        )

    def test_production_refuses_the_default_address(self):
        for value in (None, "admin/", "/admin", "Admin/", ""):
            with self.subTest(value=value):
                result = self._import_prod(value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ADMIN_URL", result.stderr)

    def test_production_accepts_a_private_address(self):
        result = self._import_prod("staff-4f8k2")
        self.assertEqual(result.returncode, 0, result.stderr)


# ---------- Suspend hides content ----------

class SuspendTests(ModerationTestCase):
    """Призупинення."""
    def setUp(self):
        super().setUp()
        self.public_urls = [
            reverse("accounts:profile", args=["ana"]),
            self.project.get_absolute_url(),
        ]

    def test_visible_before_suspension(self):
        for url in self.public_urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get(reverse("social:feed") + "?tab=latest"), "Quillbox")
        self.assertContains(self.client.get(reverse("pages:explore")), "Quillbox")
        self.assertContains(self.client.get(reverse("pages:landing")), "Quillbox")

    def test_suspending_through_the_admin_hides_everything(self):
        self.client.force_login(self.boss)
        self.client.post(reverse("admin:accounts_user_changelist"),
                         {"action": "suspend", "_selected_action": [self.ana.pk]})
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.is_suspended)

        self.client.logout()
        for url in self.public_urls:
            self.assertEqual(self.client.get(url).status_code, 404, url)
        self.assertNotContains(self.client.get(reverse("social:feed") + "?tab=latest"), "Quillbox")
        self.assertNotContains(self.client.get(reverse("pages:explore")), "Quillbox")
        self.assertNotContains(self.client.get(reverse("pages:landing")), "Quillbox")
        self.assertNotContains(self.client.get(reverse("pages:explore") + "?q=ana"), "Quillbox")
        self.client.force_login(self.visitor)
        Follow.objects.create(follower=self.visitor, following=self.ana)
        self.assertNotContains(self.client.get(reverse("social:feed") + "?tab=following"), "Quillbox")

    def test_badges_of_a_suspended_user_look_like_unknown_ones(self):
        actions.suspend_user(self.ana, self.boss)
        unknown_profile = self.client.get(reverse("projects:badge_profile", args=["nobody"])).content
        unknown_project = self.client.get(reverse("projects:badge_project", args=["nobody", "nothing"])).content
        profile = self.client.get(reverse("projects:badge_profile", args=["ana"]))
        project = self.client.get(reverse("projects:badge_project", args=["ana", self.project.slug]))
        self.assertEqual(profile.content, unknown_profile)
        self.assertEqual(project.content, unknown_project)

    def test_suspended_user_cannot_like_or_report(self):
        actions.suspend_user(self.visitor, self.boss)
        self.client.force_login(self.visitor)
        other = make_project(make_user("bo"), name="Other")
        response = self.client.post(reverse("social:like", args=["bo", other.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Like.objects.exists())
        response = self.client.post(reverse("moderation:report_project", args=["bo", other.slug]),
                                    {"reason": "spam"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Report.objects.exists())

    def test_unsuspending_brings_the_content_back(self):
        actions.suspend_user(self.ana, self.boss)
        actions.unsuspend_user(self.ana, self.boss)
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 200)

    def test_hidden_project_is_a_404_for_the_public_but_not_the_owner(self):
        actions.hide_project(self.project, self.boss)
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 404)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 200)
        # The owner cannot undo the decision.
        self.client.post(reverse("projects:publish", args=["ana", self.project.slug]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.HIDDEN)


# ---------- Actions are logged ----------

class AuditTests(ModerationTestCase):
    """Записи в AuditLog."""
    def logged(self, action):
        return AuditLog.objects.filter(action=action, actor=self.boss)

    def run_action(self, model, name, objs):
        self.client.force_login(self.boss)
        response = self.client.post(reverse(f"admin:{model}_changelist"),
                                    {"action": name, "_selected_action": [o.pk for o in objs]}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_hide_and_unhide_project(self):
        self.run_action("projects_project", "hide", [self.project])
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.HIDDEN)
        entry = self.logged("moderation.project.hidden").get()
        self.assertEqual(entry.target_id, str(self.project.pk))
        self.assertEqual(entry.metadata["previous_status"], "published")

        self.run_action("projects_project", "unhide", [self.project])
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PUBLISHED)
        self.assertEqual(self.logged("moderation.project.unhidden").count(), 1)

    def test_unhiding_a_never_launched_project_gives_a_draft(self):
        draft = make_project(self.ana, name="Draft", status=Project.Status.HIDDEN)
        actions.unhide_project(draft, self.boss)
        draft.refresh_from_db()
        self.assertEqual(draft.status, Project.Status.DRAFT)

    def test_suspend_and_unsuspend_user(self):
        self.run_action("accounts_user", "suspend", [self.ana])
        self.assertEqual(self.logged("moderation.user.suspended").count(), 1)
        self.run_action("accounts_user", "unsuspend", [self.ana])
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_suspended)
        self.assertEqual(self.logged("moderation.user.unsuspended").count(), 1)

    def test_a_repeated_action_is_not_logged_twice(self):
        self.run_action("accounts_user", "suspend", [self.ana])
        self.run_action("accounts_user", "suspend", [self.ana])
        self.assertEqual(self.logged("moderation.user.suspended").count(), 1)

    def test_staff_cannot_suspend_themselves_or_a_superuser(self):
        self.run_action("accounts_user", "suspend", [self.boss])
        self.boss.refresh_from_db()
        self.assertFalse(self.boss.is_suspended)
        self.assertFalse(AuditLog.objects.filter(action="moderation.user.suspended").exists())

    def test_resolve_report(self):
        report = Report.objects.create(reporter=self.visitor, project=self.project, target_repr="x",
                                       reason=Report.Reason.SPAM)
        self.run_action("moderation_report", "resolve", [report])
        report.refresh_from_db()
        self.assertEqual(report.status, Report.Status.RESOLVED)
        self.assertEqual(report.handled_by, self.boss)
        self.assertIsNotNone(report.handled_at)
        self.assertEqual(self.logged("moderation.report.resolved").count(), 1)

    def test_rerun_verification_is_logged(self):
        row = DomainVerification.objects.create(
            project=self.project, domain="example.com", domain_key="example.com", token="t" * 32,
            status=DomainVerification.Status.VERIFIED,
        )
        pending = DomainVerification.objects.create(
            project=self.project, domain="other.com", domain_key="other.com", token="u" * 32,
        )
        with mock.patch("verification.admin.reverify", return_value="confirmed") as fake:
            self.run_action("verification_domainverification", "rerun", [row, pending])
        fake.assert_called_once()  # the pending row is skipped
        entry = self.logged("moderation.verification.rerun").get()
        self.assertEqual(entry.metadata, {"domain": "example.com", "outcome": "confirmed"})

    def test_editing_the_status_in_the_form_is_logged_too(self):
        self.client.force_login(self.boss)
        url = reverse("admin:projects_project_change", args=[self.project.pk])
        form = {
            "owner": self.ana.pk, "name": "Quillbox", "slug": self.project.slug, "tagline": "A tagline",
            "status": "hidden", "description": "", "live_url": "", "repo_full_name": "",
            "screenshots-TOTAL_FORMS": 0, "screenshots-INITIAL_FORMS": 0,
            "screenshots-MIN_NUM_FORMS": 0, "screenshots-MAX_NUM_FORMS": 1000,
        }
        response = self.client.post(url, form)
        self.assertEqual(response.status_code, 302, getattr(response, "context_data", None) and response.context_data["adminform"].form.errors)
        entry = self.logged("moderation.project.status_changed").get()
        self.assertEqual((entry.metadata["previous_status"], entry.metadata["new_status"]), ("published", "hidden"))

    def test_audit_log_cannot_be_edited_or_deleted(self):
        actions.suspend_user(self.ana, self.boss)
        entry = AuditLog.objects.get()
        self.client.force_login(self.boss)
        self.assertEqual(self.client.get(reverse("admin:moderation_auditlog_delete", args=[entry.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("admin:moderation_auditlog_change", args=[entry.pk]), {"action": "x"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:moderation_auditlog_add")).status_code, 403)

    def test_deleting_in_the_admin_is_logged(self):
        self.client.force_login(self.boss)
        self.client.post(reverse("admin:projects_project_delete", args=[self.project.pk]), {"post": "yes"})
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertEqual(self.logged("admin.deleted").get().target_id, str(self.project.pk))


# ---------- Reporting ----------

class ReportTests(ModerationTestCase):
    """Скарги."""
    def project_url(self, project=None):
        project = project or self.project
        return reverse("moderation:report_project", args=[project.owner.username, project.slug])

    def user_url(self, user=None):
        return reverse("moderation:report_user", args=[(user or self.ana).username])

    def test_signed_out_is_sent_to_sign_in(self):
        for url in (self.project_url(), self.user_url()):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("login", response["Location"])
            self.assertEqual(self.client.post(url, {"reason": "spam"}).status_code, 302)
        self.assertFalse(Report.objects.exists())

    def test_report_a_project(self):
        self.client.force_login(self.visitor)
        self.assertContains(self.client.get(self.project_url()), "Choose a reason")
        response = self.client.post(self.project_url(), {"reason": "spam", "details": " Sells pills "})
        self.assertRedirects(response, self.project.get_absolute_url())
        report = Report.objects.get()
        self.assertEqual((report.reporter, report.project, report.target_user), (self.visitor, self.project, None))
        self.assertEqual((report.reason, report.details, report.status), ("spam", "Sells pills", "open"))

    def test_report_a_profile(self):
        self.client.force_login(self.visitor)
        response = self.client.post(self.user_url(), {"reason": "impersonation"})
        self.assertRedirects(response, reverse("accounts:profile", args=["ana"]))
        report = Report.objects.get()
        self.assertEqual((report.target_user, report.project), (self.ana, None))

    def test_reason_is_required_and_other_needs_details(self):
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.post(self.project_url(), {"reason": ""}).status_code, 200)
        self.assertEqual(self.client.post(self.project_url(), {"reason": "bogus"}).status_code, 200)
        self.assertEqual(self.client.post(self.project_url(), {"reason": "other", "details": "  "}).status_code, 200)
        self.assertFalse(Report.objects.exists())

    def test_details_are_limited(self):
        self.client.force_login(self.visitor)
        self.client.post(self.project_url(), {"reason": "spam", "details": "x" * 1001})
        self.assertFalse(Report.objects.exists())

    def test_the_same_report_twice_is_stored_once(self):
        self.client.force_login(self.visitor)
        self.client.post(self.project_url(), {"reason": "spam"})
        self.client.post(self.project_url(), {"reason": "fake_proof"})
        self.assertEqual(Report.objects.count(), 1)

    def test_a_new_report_is_possible_after_the_old_one_was_resolved(self):
        self.client.force_login(self.visitor)
        self.client.post(self.project_url(), {"reason": "spam"})
        actions.resolve_report(Report.objects.get(), self.boss)
        self.client.post(self.project_url(), {"reason": "spam"})
        self.assertEqual(Report.objects.count(), 2)

    def test_you_cannot_report_yourself(self):
        self.client.force_login(self.ana)
        self.client.post(self.project_url(), {"reason": "spam"})
        self.client.post(self.user_url(), {"reason": "spam"})
        self.assertFalse(Report.objects.exists())

    def test_unreachable_targets_are_404(self):
        self.client.force_login(self.visitor)
        draft = make_project(self.ana, name="Draft", status=Project.Status.DRAFT)
        hidden = make_project(self.ana, name="Hidden", status=Project.Status.HIDDEN)
        for project in (draft, hidden):
            self.assertEqual(self.client.get(self.project_url(project)).status_code, 404)
        actions.suspend_user(self.ana, self.boss)
        self.assertEqual(self.client.get(self.project_url()).status_code, 404)
        self.assertEqual(self.client.get(self.user_url()).status_code, 404)
        self.assertEqual(self.client.get(reverse("moderation:report_user", args=["nobody"])).status_code, 404)

    def test_reports_are_rate_limited(self):
        self.client.force_login(self.visitor)
        limit = REPORT_LIMIT[0]
        projects = [make_project(make_user(f"p{i}"), name=f"P{i}") for i in range(limit + 1)]
        for project in projects:
            self.client.post(self.project_url(project), {"reason": "spam"})
        self.assertEqual(Report.objects.count(), limit)

    def test_csrf_is_enforced(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.visitor)
        self.assertEqual(strict.post(self.project_url(), {"reason": "spam"}).status_code, 403)
        self.assertFalse(Report.objects.exists())

    def test_report_survives_the_reporter_and_the_target(self):
        self.client.force_login(self.visitor)
        self.client.post(self.project_url(), {"reason": "spam"})
        self.visitor.delete()
        self.project.delete()
        report = Report.objects.get()
        self.assertIsNone(report.reporter)
        self.assertIsNone(report.project)
        self.assertIn("ana", report.target_repr)

    def test_report_links_are_shown_to_others_only(self):
        self.client.force_login(self.visitor)
        self.assertContains(self.client.get(self.project.get_absolute_url()), self.project_url())
        self.assertContains(self.client.get(reverse("accounts:profile", args=["ana"])), self.user_url())
        self.client.force_login(self.ana)
        self.assertNotContains(self.client.get(self.project.get_absolute_url()), self.project_url())
        self.assertNotContains(self.client.get(reverse("accounts:profile", args=["ana"])), self.user_url())

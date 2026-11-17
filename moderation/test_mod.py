"""Stage 2: /mod/, decisions, mute and ban enforcement, ban evasion and the abuse cases."""
import hashlib
import hmac
import json
from datetime import timedelta
from io import StringIO

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import connection
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac

from accounts import badges
from accounts.adapters import SocialAccountAdapter
from accounts.deletion import delete_account
from accounts.models import ProfileLink, User
from accounts.system import system_user
from config import branding
from projects.models import BuildLogEntry, Project
from projects.tests import image_file, make_project, make_user
from social.models import Follow

from . import bans, decisions, sanctions
from .models import AuditLog, BannedIdentity, Notice, Report, Sanction

REASON = "Spam links in every update, against the rules."


class ModTestCase(TestCase):
    """Спільні дані для тестів /mod/."""
    def setUp(self):
        cache.clear()
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")
        self.mira = make_user("mira")  # moderator
        badges.grant(self.mira, "moderator")
        self.ana = make_user("ana", headline="Ana's headline", about="Ana's about")
        ProfileLink.objects.create(user=self.ana, kind="website", url="https://ana.example")
        self.bob = make_user("bob")  # reporter
        self.project = make_project(self.ana, name="Quillbox")
        self.report = Report.objects.create(
            reporter=self.bob, project=self.project, target_owner=self.ana, target_repr=str(self.project),
            reason=Report.Reason.SPAM, details="Only ads.",
        )

    def act(self, data, report=None, as_user=None):
        self.client.force_login(as_user or self.mira)
        url = reverse("moderation:report_detail", args=[(report or self.report).pk])
        return self.client.post(url, data)

    def mute_data(self, length=7, unit="days", **extra):
        return {"action": "mute", "reason": REASON, "length": length, "unit": unit, **extra}

    def fresh(self, user):
        return User.objects.get(pk=user.pk)


# ---------- Access ----------

class AccessTests(ModTestCase):
    """Хто бачить /mod/."""
    def test_only_moderators_and_superusers_see_mod(self):
        urls = [reverse("moderation:queue"), reverse("moderation:report_detail", args=[self.report.pk]),
                reverse("moderation:act_project", args=[self.project.pk]), reverse("moderation:act_user", args=["ana"])]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # sign in first
        staff = make_user("clerk", is_staff=True)
        for person in (self.bob, staff):
            self.client.force_login(person)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 404, (person, url))
        for person in (self.mira, self.boss):
            self.client.force_login(person)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 200, (person, url))

    def test_account_menu_shows_the_open_count_to_moderators_only(self):
        self.client.force_login(self.mira)
        response = self.client.get(reverse("pages:explore"))
        self.assertContains(response, reverse("moderation:queue"))
        self.assertContains(response, '<span class="mod-count mono">1<span class="visually-hidden"> open reports</span></span>', html=True)
        self.client.force_login(self.bob)
        self.assertNotContains(self.client.get(reverse("pages:explore")), reverse("moderation:queue"))

    def test_opening_a_report_marks_it_in_review(self):
        self.client.force_login(self.mira)
        self.client.get(reverse("moderation:report_detail", args=[self.report.pk]))
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, Report.Status.IN_REVIEW)
        self.assertTrue(AuditLog.objects.filter(action="moderation.report.in_review", actor=self.mira).exists())

    def test_queue_filters_and_constant_queries(self):
        self.client.force_login(self.mira)

        def count(params):
            with CaptureQueriesContext(connection) as ctx:
                response = self.client.get(reverse("moderation:queue"), params)
            self.assertEqual(response.status_code, 200)
            return len(ctx), response

        few, response = count({})
        self.assertContains(response, str(self.project))
        for n in range(8):
            Report.objects.create(reporter=self.bob, target_user=make_user(f"u{n}"), target_repr=f"u{n}", reason="spam")
        self.assertEqual(count({})[0], few)
        _n, response = count({"kind": "project"})
        self.assertNotContains(response, "u3")
        _n, response = count({"status": "dismissed"})
        self.assertNotContains(response, str(self.project))


# ---------- Decisions ----------

class DecisionTests(ModTestCase):
    """Рішення модератора."""
    def test_every_decision_needs_a_written_reason(self):
        for data in ({"action": "dismiss", "reason": ""}, {"action": "dismiss", "reason": "no"}):
            response = self.act(data)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'role="alert"')
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_open)

    def test_dismiss_tells_the_reporter_with_the_reason(self):
        response = self.act({"action": "dismiss", "reason": "The links are part of the product."})
        self.assertRedirects(response, reverse("moderation:queue"), fetch_redirect_response=False)
        self.report.refresh_from_db()
        self.assertEqual((self.report.status, self.report.handled_by), (Report.Status.DISMISSED, self.mira))
        notice = Notice.objects.get(user=self.bob)
        self.assertEqual((notice.kind, notice.reason), ("report_dismissed", "The links are part of the product."))
        self.assertTrue(AuditLog.objects.filter(action="moderation.report.dismissed", actor=self.mira).exists())

    def test_remove_project(self):
        self.act({"action": "remove_project", "reason": REASON})
        self.project.refresh_from_db()
        self.assertEqual((self.project.status, self.project.removed_by), (Project.Status.REMOVED, self.mira))
        self.client.logout()
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("pages:explore")), "Quillbox")
        self.client.force_login(self.ana)
        page = self.client.get(self.project.get_absolute_url())
        self.assertContains(page, "Removed by moderators")
        self.assertContains(page, REASON)
        edit = reverse("projects:edit", args=["ana", self.project.slug])
        self.assertEqual(self.client.post(edit, {"name": "x", "tagline": "y"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("projects:publish", args=["ana", self.project.slug])).status_code, 403)
        self.assertEqual(Notice.objects.get(user=self.ana).kind, "project_removed")
        self.assertEqual(Notice.objects.get(user=self.bob).kind, "report_actioned")
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, Report.Status.RESOLVED)
        self.assertTrue(AuditLog.objects.filter(action="moderation.project.removed", actor=self.mira).exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("projects:delete", args=["ana", self.project.slug]))  # owner may delete
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_restore_and_purge_are_superuser_only(self):
        decisions.remove_project(self.project, self.mira, REASON)
        with self.assertRaises(PermissionDenied):
            decisions.restore_project(self.project, self.mira)
        with self.assertRaises(PermissionDenied):
            decisions.purge_project(self.project, self.mira)
        self.client.force_login(self.mira)
        changelist = reverse("admin:projects_project_changelist")
        self.client.post(changelist, {"action": "restore", "_selected_action": [self.project.pk]})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.REMOVED)
        self.client.force_login(self.boss)
        self.assertEqual(self.client.get(changelist, {"status__exact": "removed"}).status_code, 200)
        self.client.post(changelist, {"action": "restore", "_selected_action": [self.project.pk]})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PUBLISHED)
        self.assertTrue(AuditLog.objects.filter(action="moderation.project.restored", actor=self.boss).exists())
        decisions.remove_project(self.project, self.boss, REASON)
        self.client.post(changelist, {"action": "purge", "_selected_action": [self.project.pk]})
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action="moderation.project.purged").exists())

    def test_clear_profile_fields(self):
        report = Report.objects.create(reporter=self.bob, target_user=self.ana, target_owner=self.ana,
                                       target_repr="ana", reason="inappropriate")
        self.act({"action": "clear_profile", "reason": REASON, "fields": ["bio", "links"]}, report=report)
        ana = self.fresh(self.ana)
        self.assertEqual((ana.headline, ana.about), ("", ""))
        self.assertFalse(ana.links.exists())
        notice = Notice.objects.get(user=self.ana)
        self.assertEqual(notice.kind, "profile_cleared")
        entry = AuditLog.objects.get(action="moderation.profile.cleared")
        self.assertEqual(entry.metadata["changed"], ["bio", "links"])
        response = self.act({"action": "clear_profile", "reason": REASON}, report=Report.objects.create(
            reporter=self.bob, target_user=self.ana, target_repr="ana", reason="spam"))
        self.assertContains(response, "Choose at least one field.")

    def test_mute_within_the_limit(self):
        self.act(self.mute_data(7, "days"))
        mute = Sanction.objects.get(user=self.ana)
        self.assertEqual((mute.kind, mute.issued_by, mute.report), ("mute", self.mira, self.report))
        self.assertAlmostEqual((mute.expires_at - mute.starts_at).total_seconds(), 7 * 86400, delta=2)
        self.assertTrue(AuditLog.objects.filter(action="moderation.mute.issued", actor=self.mira).exists())

    def test_moderator_limits(self):
        for data, message in (
            (self.mute_data(8, "days"), "mute for at most 7 days"),
            (self.mute_data(169, "hours"), "mute for at most 7 days"),
            ({"action": "ban", "reason": REASON, "length": 15, "unit": "days"}, "ban for at most 14 days"),
            (self.mute_data(0), "Ensure this value is greater than or equal to 1"),
            ({"action": "mute", "reason": REASON, "permanent": "on"}, "Say how long."),  # forged: ignored
        ):
            response = self.act(data)
            self.assertContains(response, message)
        self.assertFalse(Sanction.objects.exists())
        self.act({"action": "ban", "reason": REASON, "length": 14, "unit": "days"})
        self.assertEqual(Sanction.objects.get().kind, "ban")

    def test_superuser_has_no_limit_and_may_issue_permanent(self):
        self.act({"action": "ban", "reason": REASON, "permanent": "on"}, as_user=self.boss)
        self.assertIsNone(Sanction.objects.get(user=self.ana).expires_at)


# ---------- Guardrails ----------

class GuardrailTests(ModTestCase):
    """Захищені акаунти й межі прав."""
    def test_moderator_cannot_touch_protected_accounts(self):
        other_mod = make_user("otto")
        badges.grant(other_mod, "moderator")
        official = make_user("teamacc")
        badges.grant(official, "official")
        self.client.force_login(self.mira)
        for target in (self.boss, official, other_mod, self.mira):
            url = reverse("moderation:act_user", args=[target.username])
            page = self.client.get(url)
            self.assertNotContains(page, 'name="action"')  # no form at all
            response = self.client.post(url, {**self.mute_data(), "category": "spam"})
            self.assertEqual(response.status_code, 403, target)
        self.assertFalse(Sanction.objects.exists())
        with self.assertRaises(PermissionDenied):
            sanctions.issue(other_mod, "ban", REASON, self.mira, length=timedelta(days=1))
        with self.assertRaises(PermissionDenied):
            sanctions.issue(system_user(), "ban", REASON, self.boss, length=timedelta(days=1))

    def protected_accounts(self):
        official = make_user("teamacc")
        badges.grant(official, "official")
        other_mod = make_user("otto")
        badges.grant(other_mod, "moderator")
        return {"superuser": self.boss, "official": official, "moderator": other_mod, "self": self.mira}

    def test_moderator_cannot_remove_projects_or_clear_profiles_of_protected_accounts(self):
        for label, owner in self.protected_accounts().items():
            project = make_project(owner, name=f"Of {label}")
            with self.assertRaises(PermissionDenied, msg=label):
                decisions.remove_project(project, self.mira, REASON)
            with self.assertRaises(PermissionDenied, msg=label):
                decisions.clear_profile(owner, ["avatar", "bio", "links"], self.mira, REASON)
            project.refresh_from_db()
            self.assertEqual(project.status, Project.Status.PUBLISHED, label)

    def test_forged_actions_cannot_get_around_the_protection(self):
        self.client.force_login(self.mira)
        for label, owner in self.protected_accounts().items():
            project = make_project(owner, name=f"Of {label}")
            # Moderate-while-browsing: refused outright.
            url = reverse("moderation:act_project", args=[project.pk])
            self.assertEqual(self.client.post(url, {"action": "remove_project", "reason": REASON,
                                                    "category": "spam"}).status_code, 403, label)
            # A report about it: only "dismiss" is offered, so a forged "remove_project" is an invalid choice.
            report = Report.objects.create(reporter=self.bob, project=project, target_owner=owner,
                                           target_repr=str(project), reason="spam")
            response = self.client.post(reverse("moderation:report_detail", args=[report.pk]),
                                        {"action": "remove_project", "reason": REASON})
            self.assertEqual(response.status_code, 200, label)
            project.refresh_from_db()
            report.refresh_from_db()
            self.assertEqual(project.status, Project.Status.PUBLISHED, label)
            self.assertTrue(report.is_open, label)  # nothing was decided
        self.assertFalse(Notice.objects.filter(kind="project_removed").exists())

    def test_report_about_a_protected_account_can_only_be_dismissed(self):
        official = make_user("teamacc")
        badges.grant(official, "official")
        report = Report.objects.create(reporter=self.bob, target_user=official, target_owner=official,
                                       target_repr="teamacc", reason="spam")
        response = self.act(self.mute_data(), report=report)
        self.assertEqual(response.status_code, 200)  # "mute" is not a choice here
        self.assertFalse(Sanction.objects.exists())
        self.act({"action": "dismiss", "reason": "Official account, nothing wrong."}, report=report)
        report.refresh_from_db()
        self.assertEqual(report.status, Report.Status.DISMISSED)

    def test_moderator_cannot_escalate_in_the_admin(self):
        sanction = Sanction.objects.create(user=self.ana, kind="mute", reason="x",
                                           expires_at=timezone.now() + timedelta(days=1))
        self.client.force_login(self.mira)
        for url in (reverse("admin:moderation_sanction_changelist"), reverse("admin:accounts_userbadge_add")):
            self.assertEqual(self.client.get(url).status_code, 302)  # not staff: the admin login
        self.client.post(reverse("admin:moderation_sanction_changelist"),
                         {"action": "revoke", "_selected_action": [sanction.pk]})
        sanction.refresh_from_db()
        self.assertIsNone(sanction.revoked_at)
        self.assertFalse(self.fresh(self.mira).is_superuser)

    def test_rate_limit_on_moderator_actions(self):
        from django.conf import settings
        from config.ratelimit import is_limited
        for _i in range(settings.MODERATION_ACTIONS_PER_HOUR):
            is_limited("mod_action", self.mira.pk, settings.MODERATION_ACTIONS_PER_HOUR, 3600)
        response = self.act(self.mute_data())
        self.assertContains(response, "Too many moderation actions")
        self.assertFalse(Sanction.objects.exists())

    def test_superuser_cannot_sanction_themselves(self):
        with self.assertRaises(PermissionDenied):
            sanctions.issue(self.boss, "mute", REASON, self.boss, length=timedelta(days=1))

    def test_a_muted_moderator_cannot_moderate(self):
        sanctions.issue(self.mira, "mute", REASON, self.boss, length=timedelta(days=1))
        response = self.act(self.mute_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Sanction.objects.filter(user=self.ana).count(), 0)


# ---------- Mute ----------

class MuteTests(ModTestCase):
    """Приглушення."""
    def setUp(self):
        super().setUp()
        self.mute = sanctions.issue(self.ana, "mute", REASON, self.mira, length=timedelta(days=2))
        self.entry = BuildLogEntry.objects.create(project=self.project, text="hello")
        self.client.force_login(self.ana)

    def test_muted_user_cannot_write(self):
        u, s = "ana", self.project.slug
        other = make_project(self.bob, name="Other")
        writes = [
            (reverse("projects:new"), {"name": "New", "tagline": "t"}),
            (reverse("projects:edit", args=[u, s]), {"name": "X", "tagline": "t"}),
            (reverse("projects:publish", args=[u, s]), {}),
            (reverse("projects:log_add", args=[u, s]), {"text": "update"}),
            (reverse("projects:screenshot_add", args=[u, s]), {"image": image_file()}),
            (reverse("projects:preview"), {"text": "x"}),
            (reverse("moderation:report_project", args=["bob", other.slug]), {"reason": "spam"}),
            (reverse("moderation:report_user", args=["bob"]), {"reason": "spam"}),
        ]
        for url, data in writes:
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 403, url)
        for url in (reverse("social:like", args=["bob", other.slug]), reverse("social:follow", args=["bob"])):
            response = self.client.post(url, HTTP_ACCEPT="application/json")
            self.assertEqual(response.status_code, 403, url)
            self.assertIn("muted until", json.loads(response.content)["message"])
            self.client.post(url)  # plain POST: redirect back with the same message, nothing changes
        self.assertFalse(Follow.objects.exists())
        self.assertFalse(other.likes.exists())
        self.assertEqual(Project.objects.filter(owner=self.ana).count(), 1)
        self.assertEqual(self.project.screenshots.count(), 0)
        self.assertFalse(Report.objects.filter(reporter=self.ana).exists())

    def test_muted_user_can_read_settings_export_and_delete(self):
        self.assertEqual(self.client.get(reverse("pages:explore")).status_code, 200)
        response = self.client.post(reverse("accounts:settings"), {"display_name": "Ana B", "headline": "Changed",
                                                                   "about": "", "preferred_language": "uk"})
        self.assertEqual(response.status_code, 302)
        ana = User.objects.get(pk=self.ana.pk)  # muted: the language is saved, the public profile is not
        self.assertEqual((ana.preferred_language, ana.display_name, ana.headline), ("uk", "", "Ana's headline"))
        self.assertEqual(self.client.post(reverse("accounts:export")).status_code, 200)
        self.client.post(reverse("projects:unpublish", args=["ana", self.project.slug]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.DRAFT)
        self.client.post(reverse("accounts:delete"), {"confirm": "ana"})
        self.assertFalse(User.objects.filter(username="ana").exists())

    def test_the_banner_says_why_and_until_when(self):
        response = self.client.get(reverse("pages:explore"))
        self.assertContains(response, "Your account is muted until")
        self.assertContains(response, REASON)
        self.assertContains(response, branding.CONTACT_EMAIL)

    def test_mute_does_not_hide_projects(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 200)
        self.assertContains(self.client.get(reverse("pages:explore")), "Quillbox")

    def test_mute_ends_by_itself(self):
        Sanction.objects.filter(pk=self.mute.pk).update(starts_at=timezone.now() - timedelta(days=5), expires_at=timezone.now() - timedelta(seconds=1))
        response = self.client.post(reverse("social:follow", args=["bob"]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Follow.objects.filter(follower=self.ana).exists())


# ---------- Ban ----------

def social_request():
    request = RequestFactory().get("/accounts/github/login/callback/")
    SessionMiddleware(lambda r: None).process_request(request)
    MessageMiddleware(lambda r: None).process_request(request)
    return request


def github_login(user, uid):
    return SocialLogin(user=user, account=SocialAccount(provider="github", uid=uid, user=user if user.pk else None))


class BanTests(ModTestCase):
    """Бани."""
    def setUp(self):
        super().setUp()
        SocialAccount.objects.create(user=self.ana, provider="github", uid="4242", extra_data={"login": "ana"})

    def ban(self, days=3):
        return sanctions.issue(self.ana, "ban", REASON, self.mira, length=timedelta(days=days))

    def test_ban_ends_the_active_session(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse("accounts:settings")).status_code, 200)
        self.ban()
        response = self.client.get(reverse("accounts:settings"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "This account is banned", status_code=403)
        self.assertContains(response, REASON, status_code=403)
        self.assertContains(response, branding.CONTACT_EMAIL, status_code=403)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(reverse("accounts:settings")).status_code, 302)  # signed out now

    def test_banned_users_projects_and_profile_are_hidden(self):
        self.ban()
        for url in (self.project.get_absolute_url(), reverse("accounts:profile", args=["ana"])):
            self.assertEqual(self.client.get(url).status_code, 404, url)
        for url in (reverse("pages:explore"), reverse("social:feed") + "?tab=latest", reverse("pages:landing")):
            self.assertNotContains(self.client.get(url), "Quillbox")
        badge = self.client.get(reverse("projects:badge_project", args=["ana", self.project.slug]))
        self.assertNotContains(badge, "Quillbox")

    def test_banned_user_cannot_sign_in(self):
        self.ban()
        with self.assertRaises(ImmediateHttpResponse) as caught:
            SocialAccountAdapter().pre_social_login(social_request(), github_login(self.ana, "4242"))
        self.assertEqual(caught.exception.response.status_code, 403)
        self.assertIn(REASON, caught.exception.response.content.decode())

    def test_deleting_the_account_does_not_end_the_ban(self):
        self.ban()
        row = BannedIdentity.objects.get()
        self.assertNotIn("4242", row.identity_hash)
        self.assertEqual(len(row.identity_hash), 64)
        delete_account(self.fresh(self.ana))
        self.assertEqual(BannedIdentity.objects.count(), 1)  # survives, linked to no account
        newcomer = User(username="ana-again")
        with self.assertRaises(ImmediateHttpResponse) as caught:
            SocialAccountAdapter().pre_social_login(social_request(), github_login(newcomer, "4242"))
        self.assertIn(REASON, caught.exception.response.content.decode())
        SocialAccountAdapter().pre_social_login(social_request(), github_login(User(username="carl"), "777"))

    def test_hash_is_kept_only_while_the_ban_lasts(self):
        ban = self.ban()
        sanctions.revoke(ban, self.boss)
        self.assertFalse(BannedIdentity.objects.exists())
        ban = self.ban()
        Sanction.objects.filter(pk=ban.pk).update(starts_at=timezone.now() - timedelta(days=5), expires_at=timezone.now() - timedelta(seconds=1))
        BannedIdentity.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        out = StringIO()
        call_command("prune_bans", stdout=out)
        self.assertIn("Deleted 1", out.getvalue())
        self.assertIsNone(bans.find("4242"))

    def test_revoking_a_ban_in_the_admin_deletes_its_hash_at_once(self):
        ban = self.ban()
        self.assertEqual(BannedIdentity.objects.count(), 1)
        self.client.force_login(self.boss)
        self.client.post(reverse("admin:moderation_sanction_changelist"),
                         {"action": "revoke", "_selected_action": [ban.pk]})
        ban.refresh_from_db()
        self.assertEqual(ban.revoked_by, self.boss)
        self.assertFalse(BannedIdentity.objects.exists())
        self.assertIsNone(bans.find("4242"))

    def test_prune_keeps_running_bans_and_permanent_ones(self):
        running = self.ban(days=3)
        permanent = sanctions.issue(self.ana, "ban", REASON, self.boss, length=None)
        past = sanctions.issue(self.ana, "ban", REASON, self.mira, length=timedelta(days=1))
        BannedIdentity.objects.filter(sanction=past).update(expires_at=timezone.now() - timedelta(seconds=1))
        out = StringIO()
        call_command("prune_bans", stdout=out)
        call_command("prune_bans", stdout=out)  # running it again changes nothing
        self.assertEqual(out.getvalue().count("Deleted 1"), 1)
        self.assertEqual({row.sanction_id for row in BannedIdentity.objects.all()}, {running.pk, permanent.pk})

    def test_ban_ends_by_itself(self):
        ban = self.ban()
        Sanction.objects.filter(pk=ban.pk).update(starts_at=timezone.now() - timedelta(days=5), expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 200)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse("accounts:settings")).status_code, 200)


def expected_hash(uid, key=None):
    """The documented scheme, written out independently of moderation/bans.py."""
    return hmac.new((key or settings.BAN_HASH_KEY).encode(), f"shipmark.moderation.banned-identity:github:{uid}".encode(),
                    hashlib.sha256).hexdigest()


def legacy_hash(uid, secret=None):
    return salted_hmac("shipmark.moderation.banned-identity", f"github:{uid}", secret=secret or settings.SECRET_KEY,
                       algorithm="sha256").hexdigest()


class BanHashKeyTests(ModTestCase):
    """Хеш бану використовує BAN_HASH_KEY.

    The ban hash uses its own key (BAN_HASH_KEY), not SECRET_KEY."""

    def setUp(self):
        super().setUp()
        SocialAccount.objects.create(user=self.ana, provider="github", uid="4242", extra_data={"login": "ana"})

    def ban(self):
        return sanctions.issue(self.ana, "ban", REASON, self.mira, length=timedelta(days=3))

    def refuses_signup(self, uid="4242"):
        try:
            SocialAccountAdapter().pre_social_login(social_request(), github_login(User(username="newcomer"), uid))
        except ImmediateHttpResponse as refused:
            return refused.response
        return None

    def test_hash_is_hmac_sha256_of_the_id_under_the_ban_key(self):
        self.ban()
        row = BannedIdentity.objects.get()
        self.assertEqual((row.identity_hash, row.hash_scheme), (expected_hash("4242"), "ban_key"))
        self.assertNotEqual(row.identity_hash, legacy_hash("4242"))
        self.assertNotIn("4242", row.identity_hash)

    def test_signup_with_a_banned_id_is_refused_with_the_ban_page(self):
        self.ban()
        response = self.refuses_signup()
        self.assertEqual(response.status_code, 403)
        self.assertIn(REASON, response.content.decode())
        self.assertIsNone(self.refuses_signup("999"))

    def test_a_wrong_key_does_not_match(self):
        self.ban()
        with override_settings(BAN_HASH_KEY="a-different-ban-key-" + "y" * 40):
            self.assertIsNone(bans.find("4242"))
            self.assertIsNone(self.refuses_signup())
        self.assertIsNotNone(bans.find("4242"))

    def test_secret_key_is_not_involved_any_more(self):
        self.ban()
        with override_settings(SECRET_KEY="a-brand-new-secret-key-" + "x" * 40, SECRET_KEY_FALLBACKS=[]):
            self.assertIsNotNone(bans.find("4242"))
            self.assertIsNotNone(self.refuses_signup())

    def old_row(self, uid="4242", secret=None, sanction=None):
        return BannedIdentity.objects.create(
            identity_hash=legacy_hash(uid, secret), hash_scheme="secret_key", sanction=sanction, reason=REASON,
            expires_at=timezone.now() + timedelta(days=5))

    def test_old_hashes_keep_working_until_rehashed(self):
        self.old_row()
        self.assertIsNotNone(bans.find("4242"))
        self.assertIsNotNone(self.refuses_signup())
        self.assertIsNone(bans.find("777"))
        old_key = settings.SECRET_KEY
        self.old_row("5555", secret=old_key)
        with override_settings(SECRET_KEY="the-new-secret-key-" + "z" * 40, SECRET_KEY_FALLBACKS=[old_key]):
            self.assertIsNotNone(bans.find("5555"))  # rotation with a fallback, as before
        with override_settings(SECRET_KEY="the-new-secret-key-" + "z" * 40, SECRET_KEY_FALLBACKS=[]):
            self.assertIsNone(bans.find("5555"))

    def test_new_bans_use_the_new_key_even_when_old_rows_exist(self):
        self.old_row("5555")
        self.ban()
        self.assertEqual(BannedIdentity.objects.filter(hash_scheme="ban_key").get().identity_hash, expected_hash("4242"))
        self.assertEqual(BannedIdentity.objects.filter(hash_scheme="secret_key").count(), 1)

    def test_rehash_converts_rows_whose_account_exists_and_reports_the_rest(self):
        ban = sanctions.issue(self.ana, "ban", REASON, self.mira, length=timedelta(days=3))
        BannedIdentity.objects.all().delete()
        row = self.old_row(sanction=ban)  # an old-scheme row for a live account
        orphan = self.old_row("8888")  # its account was deleted: no sanction, no id to rehash from
        out = StringIO()
        call_command("rehash_bans", stdout=out)
        row.refresh_from_db()
        orphan.refresh_from_db()
        self.assertEqual((row.hash_scheme, row.identity_hash), ("ban_key", expected_hash("4242")))
        self.assertEqual((orphan.hash_scheme, orphan.identity_hash), ("secret_key", legacy_hash("8888")))
        self.assertIn("Rehashed 1", out.getvalue())
        self.assertIn("1 old-scheme hash(es) cannot be converted", out.getvalue())
        # The converted ban no longer depends on SECRET_KEY; the orphan still matches through the old scheme.
        with override_settings(SECRET_KEY="the-new-secret-key-" + "z" * 40, SECRET_KEY_FALLBACKS=[]):
            self.assertIsNotNone(bans.find("4242"))
            self.assertIsNone(bans.find("8888"))
        self.assertIsNotNone(bans.find("8888"))
        call_command("rehash_bans", stdout=StringIO())  # running it again changes nothing
        self.assertEqual(BannedIdentity.objects.filter(hash_scheme="ban_key").count(), 1)

    def test_rehash_never_converts_on_a_guess(self):
        ban = sanctions.issue(self.ana, "ban", REASON, self.mira, length=timedelta(days=3))
        BannedIdentity.objects.all().delete()
        row = BannedIdentity.objects.create(identity_hash="f" * 64, hash_scheme="secret_key", sanction=ban,
                                            reason=REASON, expires_at=timezone.now() + timedelta(days=1))
        self.assertEqual(bans.rehash(), (0, 1))
        row.refresh_from_db()
        self.assertEqual((row.hash_scheme, row.identity_hash), ("secret_key", "f" * 64))

    def test_when_nothing_is_left_the_command_says_so(self):
        self.ban()
        out = StringIO()
        call_command("rehash_bans", stdout=out)
        self.assertIn("No old-scheme hashes left", out.getvalue())


# ---------- The reporter stays anonymous ----------

class ReporterPrivacyTests(ModTestCase):
    """Автор скарги лишається прихованим."""
    def test_reporter_is_never_shown_to_the_reported_person(self):
        decisions.remove_project(self.project, self.mira, REASON, report=self.report)
        sanctions.issue(self.ana, "mute", REASON, self.mira, length=timedelta(days=1), report=self.report)
        self.client.force_login(self.ana)
        pages = [self.project.get_absolute_url(), reverse("projects:edit", args=["ana", self.project.slug]),
                 reverse("accounts:profile", args=["ana"]), reverse("accounts:settings"), reverse("pages:explore")]
        for url in pages:
            body = self.client.get(url).content.decode()
            self.assertNotIn("@bob", body, url)
            self.assertNotIn(reverse("accounts:profile", args=["bob"]), body, url)
        export = self.client.post(reverse("accounts:export")).content.decode()
        self.assertNotIn("bob", export)
        self.assertIn(REASON, export)
        self.client.force_login(self.mira)
        self.assertContains(self.client.get(reverse("moderation:report_detail", args=[self.report.pk])), "@bob")


# ---------- Moderate while browsing, reports on log entries ----------

class BrowseTests(ModTestCase):
    """«Модерувати» під час перегляду."""
    def test_menu_only_for_moderators_and_never_on_own_things(self):
        act = reverse("moderation:act_project", args=[self.project.pk])
        self.client.force_login(self.mira)
        self.assertContains(self.client.get(self.project.get_absolute_url()), act)
        self.assertContains(self.client.get(reverse("social:feed") + "?tab=latest"), act)
        self.assertContains(self.client.get(reverse("accounts:profile", args=["ana"])),
                            reverse("moderation:act_user", args=["ana"]))
        own = make_project(self.mira, name="Mine")
        self.assertNotContains(self.client.get(own.get_absolute_url()), reverse("moderation:act_project", args=[own.pk]))
        self.client.force_login(self.bob)
        self.assertNotContains(self.client.get(self.project.get_absolute_url()), act)

    def test_acting_while_browsing_links_the_open_report(self):
        self.client.force_login(self.mira)
        url = reverse("moderation:act_project", args=[self.project.pk])
        self.client.post(url, {"action": "remove_project", "reason": REASON, "category": "spam"})
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, Report.Status.RESOLVED)
        self.assertEqual(Report.objects.count(), 1)  # no second history

    def test_acting_without_a_report_creates_one(self):
        self.report.delete()
        self.client.force_login(self.mira)
        self.client.post(reverse("moderation:act_user", args=["ana"]), {**self.mute_data(), "category": "spam"})
        report = Report.objects.get()
        self.assertEqual((report.source, report.reporter, report.status), ("moderator", self.mira, "resolved"))
        self.assertEqual(Sanction.objects.get().report, report)

    def test_report_a_build_log_entry(self):
        entry = BuildLogEntry.objects.create(project=self.project, text="Buy followers here")
        url = reverse("moderation:report_log_entry", args=["ana", self.project.slug, entry.pk])
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(self.project.get_absolute_url()), url)
        self.client.post(url, {"reason": "spam", "details": ""})
        report = Report.objects.get(log_entry=entry)
        self.assertEqual((report.target_owner, report.reporter), (self.ana, self.bob))
        self.client.force_login(self.ana)
        response = self.client.post(url, {"reason": "spam"})
        self.assertEqual(response.status_code, 302)  # own project: refused with a message
        self.assertEqual(Report.objects.filter(log_entry=entry).count(), 1)
        self.client.force_login(self.mira)
        self.assertContains(self.client.get(reverse("moderation:report_detail", args=[report.pk])), "Buy followers")


class NoticeTests(ModTestCase):
    """Повідомлення про рішення."""
    def test_notice_is_dismissed_only_by_its_owner(self):
        decisions.dismiss(self.report, self.mira, "Nothing against the rules.")
        notice = Notice.objects.get(user=self.bob)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(reverse("moderation:dismiss_notice", args=[notice.pk])).status_code, 404)
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(reverse("pages:explore")), "Nothing against the rules.")
        self.client.post(reverse("moderation:dismiss_notice", args=[notice.pk]), {"next": "https://evil.example/"})
        notice.refresh_from_db()
        self.assertIsNotNone(notice.dismissed_at)
        self.assertNotContains(self.client.get(reverse("pages:explore")), "Nothing against the rules.")

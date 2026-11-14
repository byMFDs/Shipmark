"""Sanction model and its admin: when a sanction is in force, who may issue and revoke, and the history."""
from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts import badges
from accounts.system import system_user
from accounts.test_badges import staff_with_all_badge_perms
from accounts.models import User
from projects.tests import make_user

from . import sanctions
from .models import AuditLog, Sanction


def admin_datetime(prefix, value):
    """Admin split date/time widget fields."""
    local = timezone.localtime(value)
    return {f"{prefix}_0": local.strftime("%Y-%m-%d"), f"{prefix}_1": local.strftime("%H:%M:%S")}


class SanctionStateTests(TestCase):
    """Стани санкцій."""
    def setUp(self):
        self.ana = make_user("ana")
        self.now = timezone.now()

    def make(self, **extra):
        data = {"user": self.ana, "kind": Sanction.Kind.MUTE, "reason": "Spam", "starts_at": self.now - timedelta(hours=1)}
        data.update(extra)
        return Sanction.objects.create(**data)

    def test_active_expired_scheduled_revoked_permanent(self):
        active = self.make(expires_at=self.now + timedelta(days=1))
        expired = self.make(starts_at=self.now - timedelta(days=3), expires_at=self.now - timedelta(days=1))
        scheduled = self.make(starts_at=self.now + timedelta(days=1), expires_at=self.now + timedelta(days=2))
        revoked = self.make(expires_at=self.now + timedelta(days=1), revoked_at=self.now)
        permanent = self.make(kind=Sanction.Kind.BAN, expires_at=None)
        self.assertEqual({s.pk for s in Sanction.objects.active(self.now)}, {active.pk, permanent.pk})
        self.assertEqual([s.state(self.now) for s in (active, expired, scheduled, revoked, permanent)],
                         ["active", "expired", "scheduled", "revoked", "active"])
        self.assertTrue(permanent.is_permanent)
        self.assertFalse(active.is_active(self.now + timedelta(days=2)))  # expiry needs no cron

    def test_end_must_be_after_start(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make(expires_at=self.now - timedelta(hours=2))

    def test_revoke_is_logged_once(self):
        boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        sanction = self.make(expires_at=self.now + timedelta(days=1))
        self.assertTrue(sanctions.revoke(sanction, boss))
        self.assertFalse(sanctions.revoke(sanction, boss))
        self.assertEqual(AuditLog.objects.filter(action="moderation.mute.revoked", actor=boss).count(), 1)
        self.assertFalse(sanction.is_active())

    def test_target_rules(self):
        boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        moderator = make_user("mira")
        badges.grant(moderator, "moderator")
        with self.assertRaises(PermissionDenied):
            sanctions.check_target(boss, boss)  # yourself
        with self.assertRaises(PermissionDenied):
            sanctions.check_target(system_user(), boss)
        with self.assertRaises(PermissionDenied):
            sanctions.check_target(boss, moderator)  # a superuser
        official = make_user("team")
        badges.grant(official, "official")
        with self.assertRaises(PermissionDenied):
            sanctions.check_target(official, moderator)
        sanctions.check_target(official, boss)  # superusers may
        sanctions.check_target(self.ana, moderator)


class SanctionAdminTests(TestCase):
    """Санкції в адмінці."""
    def setUp(self):
        self.boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        self.ana = make_user("ana")
        self.add_url = reverse("admin:moderation_sanction_add")
        self.now = timezone.now()

    def post_data(self, user, **extra):
        data = {"user": user.pk, "kind": "ban", "reason": "Fake proof, repeated", "report": ""}
        data.update(admin_datetime("starts_at", self.now))
        data.update(extra)
        return data

    def test_superuser_issues_a_permanent_ban_and_it_is_logged(self):
        self.client.force_login(self.boss)
        response = self.client.post(self.add_url, self.post_data(self.ana))
        self.assertEqual(response.status_code, 302, response.content[:2000])
        sanction = Sanction.objects.get(user=self.ana)
        self.assertEqual((sanction.issued_by, sanction.kind, sanction.expires_at), (self.boss, "ban", None))
        entry = AuditLog.objects.get(action="moderation.ban.issued")
        self.assertEqual((entry.actor, entry.metadata["expires_at"], entry.metadata["reason"]),
                         (self.boss, None, "Fake proof, repeated"))

    def test_revoke_action(self):
        sanction = Sanction.objects.create(user=self.ana, kind="mute", reason="x", expires_at=self.now + timedelta(days=1))
        self.client.force_login(self.boss)
        self.client.post(reverse("admin:moderation_sanction_changelist"),
                         {"action": "revoke", "_selected_action": [sanction.pk]})
        sanction.refresh_from_db()
        self.assertEqual(sanction.revoked_by, self.boss)
        self.assertTrue(AuditLog.objects.filter(action="moderation.mute.revoked").exists())

    def test_cannot_sanction_yourself_or_the_system_account(self):
        self.client.force_login(self.boss)
        for target in (self.boss, system_user()):
            response = self.client.post(self.add_url, self.post_data(target))
            self.assertEqual(response.status_code, 200)
            self.assertFalse(Sanction.objects.filter(user=target).exists())
        self.assertContains(response, "cannot be sanctioned")

    def test_end_before_start_is_a_form_error(self):
        self.client.force_login(self.boss)
        data = self.post_data(self.ana, **admin_datetime("expires_at", self.now - timedelta(days=1)))
        response = self.client.post(self.add_url, data)
        self.assertContains(response, "The end must be after the start.")
        self.assertFalse(Sanction.objects.exists())

    def test_staff_can_look_but_not_issue_change_revoke_or_delete(self):
        sanction = Sanction.objects.create(user=self.ana, kind="mute", reason="x", expires_at=self.now + timedelta(days=1))
        staff = staff_with_all_badge_perms()
        from django.contrib.auth.models import Permission
        staff.user_permissions.add(*Permission.objects.filter(content_type__app_label="moderation"))
        staff = User.objects.get(pk=staff.pk)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("admin:moderation_sanction_changelist")).status_code, 200)
        self.assertEqual(self.client.post(self.add_url, self.post_data(self.ana)).status_code, 403)
        self.client.post(reverse("admin:moderation_sanction_changelist"), {"action": "revoke", "_selected_action": [sanction.pk]})
        url = reverse("admin:moderation_sanction_delete", args=[sanction.pk])
        self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
        sanction.refresh_from_db()
        self.assertIsNone(sanction.revoked_at)
        self.assertEqual(Sanction.objects.count(), 1)

    def test_superuser_cannot_delete_either(self):
        sanction = Sanction.objects.create(user=self.ana, kind="mute", reason="x", expires_at=self.now + timedelta(days=1))
        self.client.force_login(self.boss)
        self.client.post(reverse("admin:moderation_sanction_delete", args=[sanction.pk]), {"post": "yes"})
        self.assertTrue(Sanction.objects.filter(pk=sanction.pk).exists())

    def test_list_renders_with_state_filter(self):
        Sanction.objects.create(user=self.ana, kind="mute", reason="x", expires_at=self.now + timedelta(days=1))
        self.client.force_login(self.boss)
        for state in ("", "active", "scheduled", "expired", "revoked"):
            response = self.client.get(reverse("admin:moderation_sanction_changelist"), {"state": state} if state else {})
            self.assertEqual(response.status_code, 200)

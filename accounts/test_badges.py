"""Badges and roles: who grants them, what they allow, and how they show next to names."""
from io import StringIO

from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.github.provider import GitHubProvider

from django.contrib.admin.sites import site
from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.management import CommandError, call_command
from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from moderation.models import AuditLog
from projects.tests import make_project

from . import badges, roles
from .admin import UserAdmin, UserBadgeInline
from .forms import SettingsForm
from .models import User, UserBadge
from .system import SYSTEM_USERNAME, system_user
from .tests import GITHUB_DATA
from .usernames import RESERVED_USERNAMES, looks_official, validate_display_name, validate_username


def make_user(username, **extra):
    return User.objects.create_user(username=username, password="x", **extra)


def staff_with_all_badge_perms(username="clerk"):
    """Staff who has every Django permission on users and badges, but is not a superuser."""
    staff = make_user(username, is_staff=True)
    staff.user_permissions.set(Permission.objects.filter(content_type__app_label="accounts"))
    return User.objects.get(pk=staff.pk)  # fresh object: the permission cache is per instance


class RoleTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")

    def test_moderation_comes_from_the_badge_not_from_staff(self):
        staff = make_user("clerk", is_staff=True)
        self.assertFalse(roles.can_moderate(staff))
        self.assertFalse(roles.can_moderate(self.ana))
        badges.grant(self.ana, UserBadge.Kind.MODERATOR)
        self.assertTrue(roles.can_moderate(self.ana))
        self.assertTrue(roles.can_moderate(User.objects.create_superuser("boss", "b@example.com", "pw")))

    def test_official_badge_gives_no_permissions(self):
        badges.grant(self.ana, UserBadge.Kind.OFFICIAL)
        self.assertTrue(roles.is_official(self.ana))
        self.assertFalse(roles.can_moderate(self.ana))
        self.assertFalse(roles.can_manage_badges(self.ana))

    def test_inactive_moderator_cannot_moderate(self):
        badges.grant(self.ana, UserBadge.Kind.MODERATOR)
        self.ana.is_active = False
        self.assertFalse(roles.can_moderate(self.ana))

    def test_revoke_takes_effect_on_the_same_object(self):
        badges.grant(self.ana, UserBadge.Kind.MODERATOR)
        self.assertTrue(roles.can_moderate(self.ana))
        badges.revoke(self.ana, UserBadge.Kind.MODERATOR)
        self.assertFalse(roles.can_moderate(self.ana))

    def test_grant_and_revoke_are_logged_once(self):
        boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        self.assertIsNotNone(badges.grant(self.ana, "moderator", actor=boss, note="trial"))
        self.assertIsNone(badges.grant(self.ana, "moderator", actor=boss))  # already has it
        self.assertTrue(badges.revoke(self.ana, "moderator", actor=boss))
        self.assertFalse(badges.revoke(self.ana, "moderator", actor=boss))
        log = list(AuditLog.objects.filter(target_id=str(self.ana.pk)).values_list("action", "actor", "metadata__kind"))
        self.assertEqual(sorted(log), [("badge.granted", boss.pk, "moderator"), ("badge.revoked", boss.pk, "moderator")])

    def test_anonymous_has_no_roles(self):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        self.assertEqual(roles.badge_kinds(anon), frozenset())
        self.assertFalse(roles.can_moderate(anon))


class BadgeAdminTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        self.ana = make_user("ana")
        self.add_url = reverse("admin:accounts_userbadge_add")

    def test_superuser_grants_in_the_admin_and_it_is_logged(self):
        self.client.force_login(self.boss)
        response = self.client.post(self.add_url, {"user": self.ana.pk, "kind": "moderator", "note": "helps out"})
        self.assertEqual(response.status_code, 302)
        badge = UserBadge.objects.get(user=self.ana)
        self.assertEqual(badge.granted_by, self.boss)
        entry = AuditLog.objects.get(action="badge.granted")
        self.assertEqual((entry.actor, entry.metadata["kind"], entry.metadata["via"]), (self.boss, "moderator", "admin"))
        self.client.post(reverse("admin:accounts_userbadge_delete", args=[badge.pk]), {"post": "yes"})
        self.assertFalse(UserBadge.objects.filter(user=self.ana).exists())
        self.assertTrue(AuditLog.objects.filter(action="badge.revoked", actor=self.boss).exists())

    def test_staff_with_every_permission_still_cannot_change_badges(self):
        staff = staff_with_all_badge_perms()
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("admin:accounts_userbadge_changelist")).status_code, 200)  # can look
        response = self.client.post(self.add_url, {"user": staff.pk, "kind": "moderator"})
        self.assertEqual(response.status_code, 403)
        badge = UserBadge.objects.create(user=self.ana, kind="official")
        response = self.client.post(reverse("admin:accounts_userbadge_delete", args=[badge.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(UserBadge.objects.filter(user=staff).exists())
        self.assertTrue(UserBadge.objects.filter(pk=badge.pk).exists())

    def test_user_inline_is_read_only_for_staff(self):
        request = RequestFactory().get("/")
        inline = UserBadgeInline(User, site)
        request.user = staff_with_all_badge_perms()
        self.assertTrue(inline.has_view_permission(request))
        self.assertFalse(inline.has_add_permission(request))
        self.assertFalse(inline.has_change_permission(request))
        self.assertFalse(inline.has_delete_permission(request))
        request.user = self.boss
        self.assertTrue(inline.has_add_permission(request))

    def test_staff_cannot_make_themselves_superuser(self):
        request = RequestFactory().get("/")
        request.user = staff_with_all_badge_perms()
        readonly = UserAdmin(User, site).get_readonly_fields(request, request.user)
        for field in ("is_staff", "is_superuser", "groups", "user_permissions"):
            self.assertIn(field, readonly)
        request.user = self.boss
        self.assertNotIn("is_superuser", UserAdmin(User, site).get_readonly_fields(request, self.ana))


class GrantBadgeCommandTests(TestCase):
    def test_grant_and_revoke(self):
        ana = make_user("ana")
        out = StringIO()
        call_command("grant_badge", "Ana", "moderator", "--note", "first", stdout=out)
        self.assertIn("Granted moderator to ana", out.getvalue())
        self.assertTrue(roles.can_moderate(User.objects.get(pk=ana.pk)))
        call_command("grant_badge", "ana", "moderator", stdout=out)
        self.assertIn("already has", out.getvalue())
        call_command("grant_badge", "ana", "moderator", "--revoke", stdout=out)
        self.assertFalse(UserBadge.objects.filter(user=ana).exists())
        self.assertEqual(AuditLog.objects.filter(metadata__via="command").count(), 2)

    def test_unknown_user_and_kind(self):
        with self.assertRaises(CommandError):
            call_command("grant_badge", "nobody", "official")
        make_user("ana")
        with self.assertRaises(CommandError):
            call_command("grant_badge", "ana", "admin")


class SystemAccountTests(TestCase):
    def test_created_by_migration_with_the_official_badge(self):
        account = system_user()
        self.assertEqual(account.username, SYSTEM_USERNAME)
        self.assertTrue(roles.is_official(account))
        self.assertFalse(roles.can_moderate(account))
        self.assertFalse(account.has_usable_password())
        self.assertFalse(account.is_active)

    def test_nobody_can_sign_in_as_it(self):
        self.assertIsNone(authenticate(username=SYSTEM_USERNAME, password=""))
        self.assertFalse(self.client.login(username=SYSTEM_USERNAME, password=""))
        response = self.client.post(reverse("admin:login"), {"username": SYSTEM_USERNAME, "password": ""})
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 200)


class NameRuleTests(TestCase):
    def test_new_reserved_usernames(self):
        for name in ("shipmark", "official", "moderator", "mod", "support", "team", "staff", "news", "admin"):
            self.assertIn(name, RESERVED_USERNAMES)
            with self.assertRaises(ValidationError):
                validate_username(name)

    def test_official_looking_display_names(self):
        for name in ("Shipmark", "  SHIPMARK ", "Shipmark Team", "shipmark-official", "Official Shipmark",
                     "Ｓｈｉｐｍａｒｋ", "Shipmark   Support"):
            self.assertTrue(looks_official(name), name)
        for name in ("Shipmark fan", "Ship Marker", "Alice", "", "Shipmarks"):
            self.assertFalse(looks_official(name), name)

    def test_only_official_accounts_may_use_them(self):
        ana = make_user("ana")
        with self.assertRaises(ValidationError):
            validate_display_name("Shipmark Team", ana)
        badges.grant(ana, UserBadge.Kind.OFFICIAL)
        validate_display_name("Shipmark Team", ana)  # no error

    def test_settings_form_refuses_it(self):
        ana = make_user("ana", display_name="Ana")
        form = SettingsForm({"display_name": "shipmark official", "bio": "", "website": "", "preferred_language": ""},
                            instance=ana)
        self.assertFalse(form.is_valid())
        self.assertIn("reserved for official", form.errors["display_name"][0])

    def test_github_name_is_not_carried_over(self):
        request = RequestFactory().post("/signup/")
        SessionMiddleware(lambda r: None).process_request(request)
        provider = GitHubProvider(request, app=SocialApp(provider="github", client_id="id", secret="secret"))
        sociallogin = provider.sociallogin_from_response(request, {**GITHUB_DATA, "name": "Shipmark Team"})
        self.assertEqual(sociallogin.user.display_name, "")


class BadgeDisplayTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana", display_name="Ana")
        self.project = make_project(self.ana, name="Quillbox")
        badges.grant(self.ana, UserBadge.Kind.OFFICIAL)

    def test_profile_project_page_and_lists(self):
        for url in (reverse("accounts:profile", args=["ana"]), self.project.get_absolute_url(),
                    reverse("pages:explore"), reverse("social:feed") + "?tab=latest", reverse("pages:landing")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "user-mark--official")
                self.assertContains(response, "Official Shipmark account")

    def test_moderator_label_and_nothing_for_others(self):
        badges.grant(self.ana, UserBadge.Kind.MODERATOR)
        response = self.client.get(reverse("accounts:profile", args=["ana"]))
        self.assertContains(response, '<span class="user-mark user-mark--mod">Moderator</span>', html=True)
        bob = make_user("bob")
        response = self.client.get(reverse("accounts:profile", args=["bob"]))
        self.assertNotContains(response, "user-mark")

    def test_account_menu_shows_my_badge(self):
        self.client.force_login(self.ana)
        response = self.client.get(reverse("accounts:settings"))
        self.assertContains(response, "user-mark--official", count=2)  # desktop menu and phone menu

    def test_badges_do_not_add_a_query_per_row(self):
        def explore_queries():
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(reverse("pages:explore"))
            return len(ctx)

        few = explore_queries()
        for n in range(6):
            owner = make_user(f"maker{n}")
            badges.grant(owner, UserBadge.Kind.MODERATOR)
            make_project(owner, name=f"Thing {n}")
        self.assertEqual(explore_queries(), few)

"""Badges and roles: who grants them, what they allow, and how they show next to names."""
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from io import StringIO

from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.github.provider import GitHubProvider

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.admin.sites import site
from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.management import CommandError, call_command
from django.db import connection
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.formats import date_format

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
    """Ролі: хто може модерувати й видавати бейджі."""
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
    """Бейджі в адмінці: права й записи в AuditLog."""
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
    """Команда grant_badge."""
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
    """Системний акаунт shipmark."""
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
    """Зарезервовані імена користувача та відображувані імена."""
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
        # English on purpose: a request in an earlier test of the same process may have left "uk" active
        # (the order differs in `manage.py test --parallel`).
        with translation.override("en"):
            self.assertFalse(form.is_valid())
            self.assertIn("reserved for official", form.errors["display_name"][0])

    def test_github_name_is_not_carried_over(self):
        request = RequestFactory().post("/signup/")
        SessionMiddleware(lambda r: None).process_request(request)
        provider = GitHubProvider(request, app=SocialApp(provider="github", client_id="id", secret="secret"))
        sociallogin = provider.sociallogin_from_response(request, {**GITHUB_DATA, "name": "Shipmark Team"})
        self.assertEqual(sociallogin.user.display_name, "")


class BadgeDisplayTests(TestCase):
    """Показ бейджів біля імен на сторінках."""
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
                self.assertContains(response, 'data-badge="official"')
                self.assertContains(response, 'aria-label="Verified account"')

    def test_moderator_label_and_nothing_for_others(self):
        badges.grant(self.ana, UserBadge.Kind.MODERATOR)
        response = self.client.get(reverse("accounts:profile", args=["ana"]))
        self.assertContains(response, 'data-badge="moderator"')
        self.assertContains(response, 'aria-label="Moderator"')
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


class BadgeComponentTests(TestCase):
    """Один компонент бейджа: кнопка, підказка, спільна панель з датою.

    One component for every badge: a labelled button, a tooltip, and the shared panel with the real date."""

    def setUp(self):
        self.ana = make_user("ana", display_name="Ana")
        self.project = make_project(self.ana, name="Quillbox")

    def grant(self, kind, when):
        badges.grant(self.ana, kind)
        UserBadge.objects.filter(user=self.ana, kind=kind).update(granted_at=when)

    def buttons(self, html):
        return re.findall(r'<button type="button" class="user-mark user-mark--(\w+) user-mark--(\w)" data-badge="(\w+)" '
                          r'data-since="([^"]*)" data-tip="([^"]*)" aria-label="([^"]*)" aria-haspopup="dialog" '
                          r'aria-expanded="false">', html)

    def test_official_and_moderator_reuse_the_same_rosette_with_different_colours(self):
        icons = []
        for kind in ("official", "moderator"):
            with open(finders.find(f"icons/badge-{kind}.svg")) as source:
                icons.append(ET.fromstring(source.read()))
        self.assertEqual([icon.get("color") for icon in icons], ["#0096FF", "#E0245E"])
        self.assertEqual([next(iter(icon)).get("href") for icon in icons],
                         ["#account-rosette", "#account-rosette"])
        with open(finders.find("icons/account-rosette.svg")) as source:
            symbol = ET.fromstring(source.read()).find("{http://www.w3.org/2000/svg}symbol")
        self.assertEqual(symbol.get("id"), "account-rosette")
        shape, check = list(symbol)
        self.assertEqual(shape.get("d").count("Q"), 24)  # 12 crests and 12 valleys
        self.assertEqual(check.get("stroke"), "#FFFFFF")
        self.assertEqual(check.get("stroke-linecap"), "round")
        self.grant(UserBadge.Kind.OFFICIAL, timezone.now())
        self.grant(UserBadge.Kind.MODERATOR, timezone.now())
        html = self.client.get(reverse("accounts:profile", args=["ana"])).content.decode()
        self.assertEqual(html.count('id="account-rosette"'), 1)
        self.assertIn('color="#0096FF"', html)
        self.assertIn('color="#E0245E"', html)

    def test_each_kind_renders_with_its_label_glyph_and_the_real_date(self):
        official = timezone.make_aware(datetime(2025, 3, 3, 12, 0))
        moderator = timezone.make_aware(datetime(2026, 1, 20, 9, 30))
        self.grant(UserBadge.Kind.OFFICIAL, official)
        self.grant(UserBadge.Kind.MODERATOR, moderator)
        html = self.client.get(reverse("accounts:profile", args=["ana"])).content.decode()
        found = {kind: (since, tip, label) for _c, _s, kind, since, tip, label in self.buttons(html)}
        self.assertEqual(found["official"], (f"Verified since {date_format(official, 'DATE_FORMAT')}", "Verified account",
                                             "Verified account"))
        self.assertEqual(found["moderator"], (f"Verified since {date_format(moderator, 'DATE_FORMAT')}", "Moderator",
                                              "Moderator"))
        self.assertIn("March 3, 2025", found["official"][0])  # the date it was granted, not today
        self.assertIn('class="icon"', html)

    def test_the_date_is_in_the_page_language(self):
        self.grant(UserBadge.Kind.OFFICIAL, timezone.make_aware(datetime(2025, 3, 3, 12, 0)))
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uk"
        html = self.client.get(reverse("accounts:profile", args=["ana"])).content.decode()
        since = self.buttons(html)[0][3]
        self.assertIn("2025", since)
        self.assertIn("березня", since)
        self.assertNotIn("Verified since", since)

    def test_one_shared_panel_per_page_with_both_texts_and_the_how_link(self):
        self.grant(UserBadge.Kind.OFFICIAL, timezone.now())
        html = self.client.get(reverse("accounts:profile", args=["ana"])).content.decode()
        self.assertEqual(html.count("data-badge-pop>"), 1)
        self.assertIn('id="badge-tpl-official"', html)
        self.assertIn('id="badge-tpl-moderator"', html)
        self.assertIn("This account is verified and operated by the Shipmark team.", html)
        self.assertIn("Affiliated with Shipmark", html)
        self.assertIn("Moderators can review reports.", html)
        self.assertIn(f'href="{reverse("pages:how_proof_works")}#badges"', html)
        self.assertIn("js/badges.js", html)
        self.assertIn('role="dialog"', html)

    def test_size_variants(self):
        self.grant(UserBadge.Kind.OFFICIAL, timezone.now())
        render = Template("{% load ui %}{% user_marks person 's' %}|{% user_marks person 'xl' %}").render(
            Context({"person": User.objects.get(pk=self.ana.pk)}))
        small, fallback = render.split("|")
        self.assertIn("user-mark--s", small)
        self.assertIn("user-mark--m", fallback)  # an unknown size falls back to the default

    def test_ordinary_people_get_no_badge_anywhere(self):
        bob = make_user("bob")
        make_project(bob, name="Plainbox")
        for url in (reverse("accounts:profile", args=["bob"]), reverse("pages:explore"), reverse("pages:landing"),
                    reverse("social:feed") + "?tab=latest"):
            with self.subTest(url=url):
                self.assertEqual(self.buttons(self.client.get(url).content.decode()), [])

    def test_how_proof_works_explains_badges_in_every_language(self):
        for code, _name in settings.LANGUAGES:
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = code
            with self.subTest(language=code):
                self.assertContains(self.client.get(reverse("pages:how_proof_works")), 'id="badges"')


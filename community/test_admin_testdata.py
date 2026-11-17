"""Розділ адмінки «Тестові дані», лічильник людей, системний акаунт і очищення ручних тестових даних."""
import io
import tempfile
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import ProfileLink, User, UserBadge
from accounts.system import system_user
from accounts.test_github_identity import FakeGitHub
from accounts.tests import FAKE_GITHUB_APP
from news.models import NewsPost
from pages import stats
from social.models import Follow

from . import services, testdata, testdata_tools as tools
from .models import (Board, CommunityImage, Reply, ReplyNotification, TestDataFile, TestDataObject, Thread)

LOCAL = {"DEBUG": True, "SITE_URL": "http://localhost:8000", "COMMUNITY_ENABLED": True}


def png(name="pic.png", size=(320, 240), color=(120, 200, 90)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def profile_post(username, **extra):
    data = {"username": username, "display_name": "", "headline": "", "location": "", "status": "", "about": "",
            "preferred_language": "", "skills_text": "", "_save": "Save"}
    for i in range(6):
        data[f"link{i}_kind"], data[f"link{i}_url"] = "website", ""
    data.update(extra)
    return data


class MediaMixin:
    """Окремий каталог media й локальні налаштування для кожного тесту."""
    def setUp(self):
        super().setUp()
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name, **LOCAL)
        override.enable()
        self.addCleanup(override.disable)
        cache.clear()
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")
        self.real = User.objects.create_user("realperson", password="pw", display_name="Real Person")
        self.board = Board.objects.get(slug="help")

    def admin_url(self, name, *args):
        return reverse(f"admin:community_{name}", args=args)

    def add_test_user(self, username, **extra):
        self.client.force_login(self.boss)
        response = self.client.post(self.admin_url("testaccount_add"), profile_post(username, **extra))
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["adminform"].form.errors)
        return User.objects.get(username=username)

    def add_thread(self, author, title="Testing the new board", body="Hello from a test account", images=()):
        self.client.force_login(self.boss)
        data = {"author": author.pk, "board": self.board.pk, "title": title, "body": body, "_save": "Save"}
        if images:
            data["images"] = list(images)
        return self.client.post(self.admin_url("testthread_add"), data)

    def add_reply(self, author, thread, parent=None, body="A test answer", images=()):
        self.client.force_login(self.boss)
        data = {"author": author.pk, "thread": thread.pk, "parent": parent.pk if parent else "", "body": body,
                "_save": "Save"}
        if images:
            data["images"] = list(images)
        return self.client.post(self.admin_url("testreply_add"), data)


class TestUserAdminTests(MediaMixin, TestCase):
    """Суперкористувач створює й оформлює тестові акаунти; справжні недоступні."""
    def test_superuser_creates_and_styles_a_test_user(self):
        person = self.add_test_user(
            "maple-lane", display_name="Maple Lane", headline="Builds tiny tools", location="Lviv",
            about="I *like* [links](https://example.org)", status="building_in_public", skills_text="python, design",
            link0_kind="website", link0_url="https://maple.example.org", avatar_file=png())
        self.assertTrue(person.email.endswith("@example.invalid"))
        self.assertFalse(person.has_usable_password())
        self.assertFalse(person.is_staff or person.is_superuser or person.badges.exists())
        self.assertEqual(person.location, "Lviv")
        self.assertTrue(person.avatar.name.startswith("avatars/"))
        self.assertEqual(person.skills.count(), 2)
        run = tools.run_of(person)
        self.assertEqual(run.dataset.name, tools.ADMIN_DATASET)
        self.assertTrue(TestDataFile.objects.filter(name=person.avatar.name, run=run).exists())
        self.assertTrue(TestDataObject.objects.filter(model_label="accounts.profilelink",
                                                      object_id=person.links.get().pk).exists())
        self.assertEqual(TestDataObject.objects.filter(model_label="accounts.user_skills").count(), 2)
        page = self.client.get(f"/u/{person.username}/")
        self.assertContains(page, "Maple Lane")
        self.assertContains(page, "Builds tiny tools")

        # Replace the avatar, then remove it: the registry follows the files.
        first = person.avatar.name
        change = self.admin_url("testaccount_change", person.pk)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(change, profile_post("maple-lane", display_name="Maple L.", avatar_file=png(color=(10, 10, 200))))
        self.assertEqual(response.status_code, 302)
        person.refresh_from_db()
        self.assertNotEqual(person.avatar.name, first)
        self.assertFalse(TestDataFile.objects.filter(name=first).exists())
        self.assertFalse(person.avatar.storage.exists(first))
        self.assertTrue(TestDataFile.objects.filter(name=person.avatar.name).exists())
        second = person.avatar.name
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(change, profile_post("maple-lane", display_name="Maple L.", remove_avatar="on"))
        person.refresh_from_db()
        self.assertFalse(person.avatar)
        self.assertFalse(TestDataFile.objects.filter(name=second).exists())
        self.assertEqual(person.display_name, "Maple L.")
        self.assertEqual(person.skills.count(), 0)  # skills are replaced as a whole, like in Settings

    def test_only_registered_synthetic_accounts_are_listed(self):
        test = self.add_test_user("listed-one")
        page = self.client.get(self.admin_url("testaccount_changelist"))
        self.assertContains(page, "listed-one")
        self.assertNotContains(page, "realperson")
        self.assertNotContains(page, ">boss<")
        self.assertIn(test.pk, list(tools.test_users().values_list("pk", flat=True)))
        self.assertNotIn(system_user().pk, list(tools.test_users().values_list("pk", flat=True)))

    def test_real_and_system_accounts_cannot_be_opened_or_saved(self):
        self.client.force_login(self.boss)
        for target in (self.real, system_user(), self.boss):
            url = self.admin_url("testaccount_change", target.pk)
            self.assertEqual(self.client.get(url).status_code, 302)  # "does not exist" redirect
            before = User.objects.get(pk=target.pk)
            self.client.post(url, profile_post("hijacked", display_name="Hijacked"))
            after = User.objects.get(pk=target.pk)
            self.assertEqual((after.username, after.display_name), (before.username, before.display_name))
        self.assertFalse(TestDataObject.objects.filter(model_label="accounts.user", object_id=self.real.pk).exists())

    def test_server_check_refuses_a_real_account_even_if_the_form_is_bypassed(self):
        with self.assertRaises(Exception):
            tools.require_test_user(self.real)
        # Registering a real person by hand still does not make them a test account: they are not synthetic.
        tools.register(self.real, tools.admin_run())
        self.assertNotIn(self.real.pk, list(tools.test_users().values_list("pk", flat=True)))
        with self.assertRaises(Exception):
            tools.require_test_user(self.real)

    def test_a_test_account_given_a_badge_drops_out(self):
        person = self.add_test_user("badge-later")
        UserBadge.objects.create(user=person, kind=UserBadge.Kind.MODERATOR)
        self.assertEqual(self.client.get(self.admin_url("testaccount_change", person.pk)).status_code, 302)

    def test_nobody_else_gets_in(self):
        staff = User.objects.create_user("helper", password="pw", is_staff=True)
        staff.user_permissions.set(Permission.objects.filter(content_type__app_label__in=["community", "accounts"]))
        moderator = User.objects.create_user("modperson", password="pw")
        UserBadge.objects.create(user=moderator, kind=UserBadge.Kind.MODERATOR)
        urls = [self.admin_url(name) for name in ("testaccount_changelist", "testaccount_add", "testthread_add",
                                                  "testreply_add")]
        for person in (self.real, moderator, staff):
            self.client.force_login(person)
            for url in urls:
                response = self.client.get(url)
                self.assertIn(response.status_code, (302, 403), (person, url))
            response = self.client.post(self.admin_url("testaccount_add"), profile_post("sneaky"))
            self.assertIn(response.status_code, (302, 403))
        self.assertFalse(User.objects.filter(username="sneaky").exists())

    @override_settings(DEBUG=False)
    def test_superuser_outside_local_development_gets_nothing(self):
        self.client.force_login(self.boss)
        self.assertEqual(self.client.get(self.admin_url("testaccount_add")).status_code, 403)
        self.assertEqual(self.client.post(self.admin_url("testaccount_add"), profile_post("prod-ghost")).status_code, 403)
        self.assertFalse(User.objects.filter(username="prod-ghost").exists())


class TestPostAdminTests(MediaMixin, TestCase):
    """Теми й відповіді від тестових акаунтів через звичайні сервіси спільноти."""
    def test_thread_with_image_and_nested_replies_appear_in_the_community(self):
        ann = self.add_test_user("ann-test")
        bob = self.add_test_user("bob-test")
        response = self.add_thread(ann, images=[png("a.png")])
        self.assertEqual(response.status_code, 302)
        thread = Thread.objects.get(title="Testing the new board")
        self.assertEqual(thread.author, ann)
        image = CommunityImage.objects.get(thread=thread)
        for name in (image.image.name, image.thumb.name):
            self.assertTrue(TestDataFile.objects.filter(name=name).exists())
        self.assertEqual(self.add_reply(bob, thread, body="First answer").status_code, 302)
        first = Reply.objects.get(body="First answer")
        self.assertEqual(self.add_reply(ann, thread, parent=first, body="Nested answer", images=[png("b.png")]).status_code, 302)
        nested = Reply.objects.get(body="Nested answer")
        self.assertEqual((nested.parent, nested.depth), (first, 2))
        thread.refresh_from_db()
        self.assertEqual(thread.reply_count, 2)
        self.assertTrue(ReplyNotification.objects.filter(recipient=ann, reply=first).exists())
        for notice in ReplyNotification.objects.filter(reply__in=[first, nested]):
            self.assertTrue(TestDataObject.objects.filter(model_label="community.replynotification", object_id=notice.pk).exists())
        self.client.logout()
        page = self.client.get(thread.get_absolute_url())
        self.assertContains(page, "Hello from a test account")
        self.assertContains(page, "Nested answer")
        self.assertContains(page, image.thumb.url if image.thumb else image.image.url)
        self.assertContains(self.client.get(f"/community/b/{self.board.slug}/"), "Testing the new board")
        self.assertContains(self.client.get("/community/", {"q": "Testing the new"}), "Testing the new board")

    def test_real_or_system_author_is_refused_without_changes(self):
        for author in (self.real, system_user(), self.boss):
            before = (Thread.objects.count(), TestDataObject.objects.count())
            response = self.add_thread(author, title=f"Spoofed by {author.username}")
            self.assertEqual(response.status_code, 200)  # the form again, with an error
            self.assertTrue(response.context["adminform"].form.errors.get("author"))
            self.assertEqual((Thread.objects.count(), TestDataObject.objects.count()), before)

    def test_server_refuses_a_real_author_even_without_the_form(self):
        with self.assertRaises(Exception):
            tools.create_thread(self.real, self.board, "Direct call", "x")
        self.assertFalse(Thread.objects.filter(title="Direct call").exists())

    def test_real_posts_cannot_be_edited_or_answered(self):
        ann = self.add_test_user("ann-test")
        real_thread = services.create_thread(self.real, self.board, "A real question", "Real words")
        real_reply = services.create_reply(self.real, real_thread, body="Real answer")
        self.client.force_login(self.boss)
        for url in (self.admin_url("testthread_change", real_thread.pk), self.admin_url("testreply_change", real_reply.pk)):
            self.assertEqual(self.client.get(url).status_code, 302)
            self.client.post(url, {"title": "Taken over", "body": "Taken over", "_save": "Save"})
        real_thread.refresh_from_db()
        real_reply.refresh_from_db()
        self.assertEqual((real_thread.body, real_reply.body), ("Real words", "Real answer"))
        response = self.add_reply(ann, real_thread, body="Into a real thread")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reply.objects.filter(body="Into a real thread").exists())
        with self.assertRaises(Exception):
            tools.create_reply(ann, real_thread, body="Direct into a real thread")
        self.assertFalse(Reply.objects.filter(body="Direct into a real thread").exists())

    def test_edit_keeps_the_author(self):
        ann = self.add_test_user("ann-test")
        self.add_thread(ann)
        thread = Thread.objects.get(author=ann)
        response = self.client.post(self.admin_url("testthread_change", thread.pk),
                                    {"title": "Testing the new board", "body": "Edited text", "author": self.real.pk,
                                     "_save": "Save"})
        self.assertEqual(response.status_code, 302)
        thread.refresh_from_db()
        self.assertEqual((thread.body, thread.author), ("Edited text", ann))


@override_settings(PUBLIC_USER_COUNT_ENABLED=True, SOCIALACCOUNT_PROVIDERS=FAKE_GITHUB_APP)
class PeopleCountScenarioTests(MediaMixin, TestCase):
    """3 → 28 (25 тестових) → 29 (справжня реєстрація через GitHub) → 4 (очищення тестових)."""
    def counted(self):
        return stats.public_user_count()

    def sign_up_with_github(self, uid, login):
        self.client.logout()
        fake = FakeGitHub({"id": uid, "login": login, "name": login, "bio": "", "avatar_url": ""})
        with patch("accounts.adapters.SocialAccountAdapter.get_requests_session", return_value=fake):
            start = self.client.post(reverse("github_login"), {"process": "login"})
            state = parse_qs(urlparse(start["Location"]).query)["state"][0]
            response = self.client.get(reverse("github_callback"), {"code": "c0de", "state": state})
            self.assertTrue(response["Location"].endswith(reverse("socialaccount_signup")))
            response = self.client.post(reverse("socialaccount_signup"), {"username": login.lower(), "terms": "on"})
        self.assertEqual(response.status_code, 302)

    def test_three_twenty_eight_twenty_nine_four(self):
        User.objects.create_user("third", password="pw")
        self.assertEqual(self.counted(), 3)  # boss, realperson, third; never the system account
        for n in range(25):
            with self.captureOnCommitCallbacks(execute=True):
                self.add_test_user(f"tester-{n:02d}")
        self.assertEqual(self.counted(), 28)
        self.assertContains(self.client.get("/explore/"), "28 people joined")
        with self.captureOnCommitCallbacks(execute=True):
            self.sign_up_with_github(777, "Newcomer")
        self.assertTrue(User.objects.filter(username="newcomer", github_login="Newcomer").exists())
        self.assertEqual(self.counted(), 29)
        with patch.object(testdata, "backup", return_value="verified-test-backup"):
            with self.captureOnCommitCallbacks(execute=True):
                result = testdata.clean(tools.ADMIN_DATASET)
        self.assertIsNone(result["blocked"])
        self.assertEqual(result["counts"]["accounts.user"], 25)
        self.assertEqual(self.counted(), 4)
        self.assertTrue(User.objects.filter(username="newcomer").exists())
        self.assertFalse(User.objects.filter(username__startswith="tester-").exists())


class CleanupOfManualDataTests(MediaMixin, TestCase):
    """Команда очищення бачить ручні тестові дані й не чіпає справжні."""
    def clean(self, name=None):
        with patch.object(testdata, "backup", return_value="verified-test-backup"):
            with self.captureOnCommitCallbacks(execute=True):
                return testdata.clean(name)

    def test_manual_data_is_listed_and_cleaned_with_files(self):
        ann = self.add_test_user("ann-test", link0_url="https://ann.example.org", skills_text="python", avatar_file=png())
        bob = self.add_test_user("bob-test")
        self.add_thread(ann, images=[png()])
        thread = Thread.objects.get(author=ann)
        self.add_reply(bob, thread)
        real_thread = services.create_thread(self.real, self.board, "Real thread", "Stays")
        report = testdata.report(testdata.TestDataSet.objects.get(name=tools.ADMIN_DATASET))
        self.assertEqual(report["counts"]["accounts.user"], 2)
        self.assertEqual(report["counts"]["community.thread"], 1)
        files = [ann.avatar.name, *CommunityImage.objects.filter(thread=thread).values_list("image", flat=True)]
        result = self.clean()
        self.assertIsNone(result["blocked"])
        self.assertFalse(User.objects.filter(username__in=["ann-test", "bob-test"]).exists())
        self.assertFalse(Thread.objects.filter(pk=thread.pk).exists())
        self.assertFalse(ProfileLink.objects.filter(url="https://ann.example.org").exists())
        for name in files:
            self.assertFalse(ann.avatar.storage.exists(name), name)
        self.assertTrue(Thread.objects.filter(pk=real_thread.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.real.pk).exists())

    def test_a_real_reply_under_a_test_thread_blocks_cleanup(self):
        ann = self.add_test_user("ann-test")
        self.add_thread(ann)
        thread = Thread.objects.get(author=ann)
        real_reply = services.create_reply(self.real, thread, body="A real person answered")
        before = (User.objects.count(), Thread.objects.count(), Reply.objects.count())
        result = self.clean()
        self.assertIn("untracked dependencies", result["blocked"])
        self.assertIn(f"community.reply #{real_reply.pk}", result["blocked"])
        self.assertEqual((User.objects.count(), Thread.objects.count(), Reply.objects.count()), before)


@override_settings(COMMUNITY_ENABLED=True)
class SystemAccountTests(TestCase):
    """Офіційний акаунт: без публічного профілю, але автор новин і дописів; редагує лише суперкористувач."""
    def setUp(self):
        cache.clear()
        self.system = system_user()
        self.person = User.objects.create_user("plainperson", password="pw")
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")
        self.board = Board.objects.get(slug="help")
        self.thread = services.create_thread(self.system, self.board, "Welcome to the community", "Official words")
        self.news = NewsPost.objects.create(title="Official news", slug="official-news", body="News body",
                                            created_by=self.boss, published_at=timezone.now())

    def test_profile_is_404_for_everyone(self):
        for viewer in (None, self.person, self.boss):
            if viewer:
                self.client.force_login(viewer)
            for path in ("/u/shipmark/", "/u/Shipmark/", "/u/shipmark/?tab=about"):
                self.assertEqual(self.client.get(path).status_code, 404, (viewer, path))
        self.assertEqual(self.client.get("/u/plainperson/").status_code, 200)

    def test_the_mark_is_not_the_username(self):
        User.objects.filter(pk=self.system.pk).update(username="renamed-system")
        self.assertEqual(self.client.get("/u/renamed-system/").status_code, 404)
        self.assertEqual(system_user().pk, self.system.pk)

    def test_posts_and_news_stay_readable_without_a_profile_link(self):
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, "Official words")
        self.assertContains(page, "@shipmark")
        self.assertNotContains(page, 'href="/u/shipmark/"')
        listing = self.client.get(f"/community/b/{self.board.slug}/")
        self.assertNotContains(listing, 'href="/u/shipmark/"')
        self.client.force_login(self.person)
        response = self.client.post(f"/community/t/{self.thread.pk}/reply/", {"body": "Thanks!"})
        self.assertLess(response.status_code, 500)
        news = self.client.get(self.news.get_absolute_url())
        self.assertContains(news, "News body")
        self.assertNotContains(news, 'href="/u/shipmark/"')

    def test_no_follow_report_badge_or_search(self):
        self.client.force_login(self.person)
        self.assertEqual(self.client.post("/follow/shipmark/").status_code, 404)
        self.assertFalse(Follow.objects.filter(following=self.system).exists())
        self.assertEqual(self.client.get("/report/user/shipmark/").status_code, 404)
        self.assertContains(self.client.get("/badge/shipmark.svg"), "not found", status_code=200)
        from accounts.people import searchable_people
        self.assertFalse(searchable_people().filter(pk=self.system.pk).exists())

    def test_only_superusers_change_it_in_the_admin(self):
        staff = User.objects.create_user("staffer", password="pw", is_staff=True)
        staff.user_permissions.set(Permission.objects.filter(codename__in=["change_user", "view_user", "delete_user"]))
        url = reverse("admin:accounts_user_change", args=[self.system.pk])
        self.client.force_login(staff)
        response = self.client.post(url, {"display_name": "Hacked"})
        self.assertIn(response.status_code, (302, 403))
        self.system.refresh_from_db()
        self.assertNotEqual(self.system.display_name, "Hacked")
        page = self.client.get(url)
        self.assertNotContains(page, 'name="_save"')  # read-only view for staff
        self.client.force_login(self.boss)
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="_save"')
        self.assertEqual(self.client.get(reverse("admin:accounts_user_delete", args=[self.system.pk])).status_code, 403)

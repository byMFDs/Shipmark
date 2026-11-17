"""Перевірки реєстру, повторних запусків, хронології та захисту справжніх даних."""
import json
import tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command, CommandError
from django.db import transaction
from django.template.loader import render_to_string
from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone, translation
from PIL import Image

from accounts.models import User, UserBadge
from accounts.system import system_user
from news.models import NewsPost
from pages.stats import CACHE_KEY, count_people, public_user_count
from projects.models import Project
from social.models import Follow

from . import services, testdata
from .models import (Board, CommunityImage, Reply, ReplyNotification, TestDataFile,
                     TestDataObject, TestDataRun, TestDataSet, Thread, Vote)


def run(mode, *args):
    output = StringIO()
    call_command("community_testdata", mode, *args, stdout=output)
    return json.loads(output.getvalue())


@override_settings(DEBUG=True, SITE_URL="http://localhost:8000", COMMUNITY_ENABLED=True)
class TestDataTests(TestCase):
    """Тестові дані не захоплюють справжні записи та очищуються лише за реєстром."""
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        cache.clear()
        self.real = User.objects.create_user("control", password=None)
        self.board = Board.objects.get(slug="help")
        self.official = services.create_thread(system_user(), self.board, "Rules", "Keep me")
        self.official.pinned = True
        self.official.save()
        self.news = NewsPost.objects.create(title="Official news", slug="official", body="Keep", created_by=self.real)
        self.real_thread = services.create_thread(self.real, self.board, "Real work", "Keep me too")

    def seed(self, mode="seed", *args):
        return run(mode, *args)

    def clean(self):
        with patch.object(testdata, "backup", return_value="verified-test-backup"):
            with self.captureOnCommitCallbacks(execute=True):
                return testdata.clean("local-preview")

    def test_default_counts_repeat_activity_and_append(self):
        before = count_people()
        self.assertEqual(public_user_count(), before)
        with self.captureOnCommitCallbacks(execute=True):
            first = self.seed()
        self.assertEqual(first["counts"]["accounts.user"], 25)
        self.assertEqual(first["counts"]["community.thread"], 8)
        self.assertEqual(first["counts"]["community.reply"], 12)
        self.assertEqual(public_user_count(), before + 25)
        self.assertEqual(self.seed()["ids"], first["ids"])
        self.assertEqual(TestDataRun.objects.count(), 1)
        appended = self.seed("activity", "--append")
        self.assertEqual(appended["counts"]["accounts.user"], 25)
        self.assertEqual(appended["counts"]["community.thread"], 16)
        self.assertEqual(len(set(Thread.objects.exclude(pk__in=[self.official.pk, self.real_thread.pk]).values_list("title", flat=True))), 16)
        with self.assertRaisesMessage(CommandError, "exhausted"):
            self.seed("activity", "--append", "--threads", "17")
        self.assertEqual(TestDataRun.objects.count(), 2)

    def test_users_only_then_combined_and_user_append(self):
        result = self.seed("users", "--users", "20")
        self.assertEqual(result["counts"], {"accounts.user": 20})
        result = self.seed()
        self.assertEqual(result["counts"]["accounts.user"], 25)
        self.assertEqual(result["counts"]["community.thread"], 8)
        result = self.seed("users", "--append", "--users", "5")
        self.assertEqual(result["counts"]["accounts.user"], 30)

    def test_activity_requires_existing_users_and_never_adds_them(self):
        with self.assertRaisesMessage(CommandError, "At least 9"):
            self.seed("activity")
        self.assertFalse(TestDataSet.objects.exists())
        self.seed("users")
        before = User.objects.count()
        self.seed("activity")
        self.assertEqual(User.objects.count(), before)

    def test_profiles_avatars_chronology_votes_and_distribution(self):
        result = self.seed()
        people = User.objects.filter(pk__in=result["ids"]["accounts.user"])
        hashes = set()
        for person in people:
            self.assertFalse(person.has_usable_password())
            self.assertFalse(person.is_staff or person.is_superuser or person.badges.exists())
            self.assertTrue(person.email.endswith("@example.invalid"))
            self.assertFalse(person.username.startswith(("demo", "test", "bot")))
            with person.avatar.open("rb") as handle:
                image = Image.open(handle)
                self.assertEqual(image.format, "WEBP")
                image.verify()
            hashes.add(TestDataFile.objects.get(name=person.avatar.name).sha256)
            self.assertLessEqual(person.date_joined, timezone.now())
        self.assertEqual(len(hashes), 25)
        threads = Thread.objects.filter(pk__in=result["ids"]["community.thread"])
        self.assertEqual(threads.filter(reply_count=0).count(), 3)
        active = set(threads.values_list("author_id", flat=True))
        for thread in threads:
            self.assertLessEqual(thread.author.date_joined, thread.created_at)
            self.assertGreater(thread.created_at, timezone.now() - timedelta(days=14))
            self.assertEqual(thread.reply_count, thread.replies.count())
            self.assertEqual(thread.score, thread.votes.count())
            for reply in thread.replies.select_related("author", "parent"):
                active.add(reply.author_id)
                self.assertLessEqual(thread.created_at, reply.created_at)
                self.assertLessEqual(reply.author.date_joined, reply.created_at)
                self.assertLessEqual(reply.created_at, timezone.now())
                if reply.parent:
                    self.assertGreater(reply.created_at, reply.parent.created_at)
                self.assertEqual(reply.score, reply.votes.count())
        self.assertTrue(6 <= len(active) <= 9)
        for vote in Vote.objects.select_related("user", "thread", "reply"):
            target = vote.thread or vote.reply
            self.assertNotEqual(target.author_id, vote.user_id)
            self.assertGreaterEqual(vote.created_at, target.created_at)
            self.assertGreaterEqual(vote.created_at, vote.user.date_joined)
            self.assertLessEqual(vote.created_at, timezone.now())
        for notice in ReplyNotification.objects.select_related("reply"):
            self.assertEqual(notice.created_at, notice.reply.created_at)
        self.assertEqual(sum(1 for p in people if p.about), 16)

    def test_dry_run_complete_cleanup_and_repeat_preserve_official_and_real(self):
        result = self.seed()
        paths = [Path(self.media.name) / f["name"] for f in result["files"]]
        preview = self.seed("clean", "--dry-run")
        self.assertIsNone(preview["blocked"])
        self.assertEqual(preview["ids"], result["ids"])
        self.assertTrue(all(path.exists() for path in paths))
        self.clean()
        self.assertFalse(TestDataObject.objects.exists())
        self.assertFalse(TestDataFile.objects.exists())
        self.assertTrue(all(not path.exists() for path in paths))
        self.assertTrue(User.objects.filter(pk=system_user().pk).exists())
        self.assertTrue(system_user().badges.filter(kind="official").exists())
        self.official.refresh_from_db()
        self.assertTrue(self.official.pinned)
        self.assertEqual(self.official.body, "Keep me")
        self.assertTrue(NewsPost.objects.filter(pk=self.news.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.real.pk).exists())
        self.real_thread.refresh_from_db()
        self.assertEqual(self.real_thread.body, "Keep me too")
        self.assertEqual(self.seed("clean")["counts"], {})
        self.assertEqual(self.seed()["counts"]["accounts.user"], 25)

    def test_real_nested_reply_blocks_the_entire_cleanup(self):
        result = self.seed()
        thread = Thread.objects.get(pk=result["ids"]["community.thread"][0])
        parent = thread.replies.first()
        reply = services.create_reply(self.real, thread, parent=parent, body="A genuine reply")
        before = User.objects.count(), Thread.objects.count(), Reply.objects.count()
        for dry in (False, True):
            with self.assertRaisesMessage(CommandError, f"community.reply #{reply.pk}"):
                self.seed("clean", *(["--dry-run"] if dry else []))
        self.assertEqual((User.objects.count(), Thread.objects.count(), Reply.objects.count()), before)
        self.assertTrue(all((Path(self.media.name) / row["name"]).exists() for row in result["files"]))

    def test_external_vote_follow_and_set_null_reference_are_blocked(self):
        result = self.seed()
        person = User.objects.get(pk=result["ids"]["accounts.user"][0])
        edge = Follow.objects.create(follower=self.real, following=person)
        with self.assertRaisesMessage(CommandError, "social.follow"):
            self.seed("clean")
        edge.delete()
        self.news.created_by = person
        self.news.save()
        with self.assertRaisesMessage(CommandError, "news.newspost"):
            self.seed("clean")

    def test_tracked_vote_moved_to_real_content_is_protected(self):
        result = self.seed()
        vote = Vote.objects.get(pk=result["ids"]["community.vote"][0])
        Vote.objects.filter(pk=vote.pk).update(thread=self.real_thread, reply=None)
        with self.assertRaisesMessage(CommandError, "Interaction outside the test set"):
            self.seed("clean", "--all")
        self.assertTrue(Thread.objects.filter(pk=self.real_thread.pk).exists())

    def test_shared_or_modified_file_blocks_cleanup(self):
        result = self.seed()
        person = User.objects.get(pk=result["ids"]["accounts.user"][0])
        self.real.avatar = person.avatar.name
        self.real.save(update_fields=["avatar"])
        with self.assertRaisesMessage(CommandError, "Shared file"):
            self.seed("clean")
        self.real.avatar = ""
        self.real.save(update_fields=["avatar"])
        with person.avatar.open("wb") as handle:
            handle.write(b"changed")
        with self.assertRaisesMessage(CommandError, "File changed"):
            self.seed("clean")

    def test_protected_account_in_registry_is_never_deleted(self):
        result = self.seed()
        person = User.objects.get(pk=result["ids"]["accounts.user"][0])
        UserBadge.objects.create(user=person, kind="official")
        with self.assertRaisesMessage(CommandError, "Protected"):
            self.seed("clean")
        with self.assertRaisesMessage(CommandError, "Protected"):
            self.seed("activity", "--append")

    def test_unknown_activity_by_test_account_is_not_silently_deleted(self):
        result = self.seed()
        person = User.objects.get(pk=result["ids"]["accounts.user"][0])
        project = Project.objects.create(owner=person, name="Untracked work", slug="work")
        with self.assertRaisesMessage(CommandError, f"projects.project #{project.pk}"):
            self.seed("clean")

    def test_username_collision_and_seed_mismatch_are_atomic(self):
        User.objects.create_user("olena-ruta", password=None)
        with self.assertRaisesMessage(CommandError, "collision"):
            self.seed()
        self.assertFalse(TestDataSet.objects.exists())
        self.assertFalse(TestDataRun.objects.exists())
        self.assertEqual(list(Path(self.media.name).rglob("*.webp")), [])

    def test_seed_and_media_failure_leave_no_partial_dataset(self):
        self.seed("users", "--users", "9", "--seed", "42")
        with self.assertRaisesMessage(CommandError, "Dataset seed is 42"):
            self.seed()
        before = User.objects.count()
        with patch.object(testdata, "avatar_content", side_effect=OSError("disk unavailable")):
            with self.assertRaisesMessage(OSError, "disk unavailable"):
                self.seed("users", "--users", "10", "--seed", "42")
        self.assertEqual(User.objects.count(), before)
        self.assertEqual(TestDataFile.objects.count(), 9)

    def test_backup_failure_never_changes_data(self):
        self.seed()
        before = User.objects.count(), Thread.objects.count(), TestDataObject.objects.count()
        with patch.object(testdata, "backup", side_effect=OSError("backup disk full")):
            with self.assertRaisesMessage(OSError, "backup disk full"):
                self.seed("clean")
        self.assertEqual((User.objects.count(), Thread.objects.count(), TestDataObject.objects.count()), before)

    def test_file_delete_failure_is_retryable_and_rollback_keeps_files(self):
        result = self.seed("users", "--users", "1")
        path = Path(self.media.name) / result["files"][0]["name"]
        with patch.object(testdata, "backup", return_value="verified-test-backup"):
            with self.assertRaisesMessage(ValueError, "rollback"):
                with transaction.atomic():
                    self.seed("clean")
                    raise ValueError("rollback")
        self.assertTrue(path.exists())
        with patch.object(testdata.default_storage, "delete", side_effect=OSError("busy")):
            failed = self.clean()
        self.assertEqual(len(failed["file_delete_failures"]), 1)
        self.assertTrue(TestDataFile.objects.get().pending_delete)
        self.assertFalse(TestDataObject.objects.exists())
        self.assertTrue(path.exists())
        self.clean()
        self.assertFalse(path.exists())
        self.assertFalse(TestDataFile.objects.exists())

    def test_pending_file_already_removed_is_safe_to_retry(self):
        result = self.seed("users", "--users", "1")
        path = Path(self.media.name) / result["files"][0]["name"]
        with patch.object(testdata.default_storage, "delete", side_effect=OSError("busy")):
            self.clean()
        path.unlink()
        self.clean()
        self.assertFalse(TestDataFile.objects.exists())

    def test_guards_and_report(self):
        for overrides in ({"DEBUG": False}, {"SITE_URL": "https://shipmark.org"}, {"SETTINGS_MODULE": "config.settings.prod"}):
            with override_settings(**overrides), self.assertRaises(CommandError):
                self.seed()
        self.seed("users", "--users", "9")
        report = self.seed("list")
        self.assertEqual(report[0]["dataset"], "local-preview")
        self.assertEqual(len(report[0]["users"]), 9)

    def test_all_batches_search_sort_profiles_and_board_counts(self):
        from . import ranking

        result = self.seed()
        self.assertTrue(result["created"])
        self.assertEqual(self.seed()["created"], {})
        thread_ids = result["ids"]["community.thread"]
        threads = Thread.objects.filter(pk__in=thread_ids)
        self.assertEqual(set(threads.values_list("board__slug", flat=True)),
                         {"help", "show", "collab", "feedback", "off-topic"})
        people = User.objects.filter(pk__in=result["ids"]["accounts.user"])
        joined = list(people.values_list("date_joined", flat=True))
        self.assertGreater(max(joined) - min(joined), timedelta(days=4))
        for sort in ("hot", "new", "top"):
            response = self.client.get("/community/", {"sort": sort, "t": "all"})
            self.assertEqual(response.status_code, 200)
            actual = [t.pk for t in response.context["threads"]]
            expected = list(ranking.ordered(Thread.objects.public().filter(pinned=False),
                                           sort, "all", timezone.now()).values_list("pk", flat=True))
            self.assertEqual(actual, expected)
            for board in response.context["boards"]:
                self.assertEqual(board.thread_count, Thread.objects.public().filter(board=board).count())
        target = threads.first()
        response = self.client.get("/community/", {"q": target.title})
        self.assertEqual([t.pk for t in response.context["threads"]], [target.pk])
        self.assertContains(self.client.get(target.get_absolute_url()), target.author.avatar.url)
        self.assertEqual(self.client.get(f"/u/{target.author.username}/").status_code, 200)
        for _ in range(3):
            result = self.seed("activity", "--append")
        self.assertEqual(result["counts"]["accounts.user"], 25)
        self.assertEqual(result["counts"]["community.thread"], 32)
        titles = Thread.objects.filter(pk__in=result["ids"]["community.thread"]).values_list("title", flat=True)
        self.assertEqual(len(set(titles)), 32)

    def test_mid_generation_failure_removes_written_files(self):
        original = testdata.avatar_content
        calls = 0

        def fail_second(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("failed after first avatar")
            return original(*args)

        with patch.object(testdata, "avatar_content", side_effect=fail_second):
            with self.assertRaisesMessage(OSError, "failed after first avatar"):
                self.seed()
        self.assertFalse(TestDataObject.objects.exists())
        self.assertFalse(TestDataSet.objects.exists())
        self.assertEqual(list(Path(self.media.name).rglob("*.webp")), [])

    def legacy_fixture(self):
        """Відтворює точний старий корпус у тестовій БД, без старої seed-команди."""
        from .management.commands.seed_community import PEOPLE, THREADS
        people = [User.objects.create_user(name, email=f"{name}@example.invalid", password=None,
                                          display_name=name.removeprefix("demo-").title()) for name in PEOPLE]
        for slug, who, title, body, _images, answers in THREADS:
            thread = services.create_thread(people[who], Board.objects.get(slug=slug), title, body)

            def add(items, parent=None):
                for who, text, _sizes, children in items:
                    reply = services.create_reply(people[who], thread, parent=parent, body=text)
                    add(children, reply)
            add(answers)
        return people

    def test_confirmed_legacy_cleanup_keeps_similar_real_and_official_accounts(self):
        people = self.legacy_fixture()
        uncertain = User.objects.create_user("demo-unknown", email="unknown@example.invalid", password=None)
        preview = self.seed("legacy-clean", "--dry-run")
        self.assertEqual(preview["counts"]["accounts.user"], 6)
        self.assertIsNone(preview["blocked"])
        with patch.object(testdata, "backup", return_value="verified-test-backup"):
            self.seed("legacy-clean")
        self.assertFalse(User.objects.filter(pk__in=[p.pk for p in people]).exists())
        self.assertTrue(User.objects.filter(pk=uncertain.pk).exists())
        self.assertTrue(Thread.objects.filter(pk=self.official.pk).exists())
        self.assertTrue(Thread.objects.filter(pk=self.real_thread.pk).exists())
        self.assertEqual(self.seed("legacy-clean")["counts"], {})

    def test_legacy_with_real_replies_is_blocked_without_partial_changes(self):
        people = self.legacy_fixture()
        thread = Thread.objects.filter(author=people[-1]).first()
        reply = services.create_reply(self.real, thread, body="This is a real reply")
        with self.assertRaisesMessage(CommandError, f"community.reply #{reply.pk}"):
            self.seed("legacy-clean")
        self.assertEqual(User.objects.filter(pk__in=[p.pk for p in people]).count(), 6)

    def test_historical_sticker_only_reply_is_proven_from_the_old_corpus(self):
        from .management.commands.seed_community import PEOPLE
        self.legacy_fixture()
        reply = Reply.objects.get(author__username=PEOPLE[3], body="That sounds good.")
        Reply.objects.filter(pk=reply.pk).update(body="", sticker_key="sleepy")
        preview = self.seed("legacy-clean", "--dry-run")
        self.assertIsNone(preview["blocked"])


class ModerationMenuCountTests(SimpleTestCase):
    """Нуль і додатний badge в усіх мовах та обох варіантах меню."""
    def test_all_locales_desktop_and_mobile(self):
        for language, _name in settings.LANGUAGES:
            with translation.override(language):
                for panel in (False, True):
                    for count in (0, 4):
                        with self.subTest(language=language, mobile=panel, count=count):
                            html = render_to_string("includes/site_nav.html", {
                                "signed_in": True, "in_panel": panel, "mod_url": "/mod/", "mod_count": count,
                                "me": {"user": None, "name": "Person"},
                            })
                            label = translation.gettext("Moderation")
                            self.assertIn(label, html)
                            self.assertIn('href="/mod/"', html)
                            if count:
                                self.assertIn('class="mod-count mono">4', html)
                            else:
                                self.assertNotIn('class="mod-count', html)
                                self.assertNotIn(label + "0", html)
                                self.assertNotIn(">0<", html)

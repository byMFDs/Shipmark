"""Стартові теми запуску й захист демо-команд від production."""
import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.system import system_user
from community.models import Reply, ReplyNotification, Thread, Vote
from community.management.commands.seed_launch_content import THREADS
from moderation.models import AuditLog
from pages.stats import count_people
from projects.tests import make_user

User = get_user_model()


def run(*args):
    out = StringIO()
    call_command("seed_launch_content", *args, stdout=out)
    return out.getvalue()


class LaunchContentTests(TestCase):
    """seed_launch_content: лише від shipmark, ідемпотентно, без вигаданих людей."""
    def test_creates_the_threads_from_the_system_account_only(self):
        users_before = User.objects.count()
        run()
        threads = Thread.objects.all()
        self.assertEqual(threads.count(), len(THREADS))
        self.assertTrue(4 <= threads.count() <= 6)
        self.assertEqual({t.author for t in threads}, {system_user()})
        self.assertEqual(User.objects.count(), users_before)  # nobody was created
        self.assertEqual((Reply.objects.count(), Vote.objects.count(), ReplyNotification.objects.count()), (0, 0, 0))
        self.assertEqual(AuditLog.objects.filter(action="community.launch_thread_posted").count(), len(THREADS))

    def test_titles_are_the_agreed_starters_and_one_is_pinned(self):
        run()
        titles = set(Thread.objects.values_list("title", flat=True))
        for title in ("What are you building this week?", "Which AI tools do you use, and for what?",
                      "Share the first thing you shipped", "Questions about how proof works? Ask here",
                      "Ideas for Shipmark"):
            self.assertIn(title, titles)
        self.assertEqual(list(Thread.objects.filter(pinned=True).values_list("title", flat=True)),
                         ["What are you building this week?"])

    def test_text_is_plain_english_written_as_the_team_with_no_contact_data(self):
        run()
        for thread in Thread.objects.all():
            with self.subTest(thread=thread.title):
                self.assertTrue(thread.body.rstrip().endswith("The Shipmark team"))
                self.assertNotIn("@", thread.body)
                self.assertNotIn("http", thread.body)
                self.assertLessEqual(len(thread.body), 700)
                for first_person in (" I ", " I'm ", " my "):
                    self.assertNotIn(first_person, thread.body)  # the team speaks, not an invented person

    def test_running_again_changes_nothing(self):
        run()
        before = list(Thread.objects.order_by("pk").values_list("pk", "title", "body", "pinned"))
        self.assertIn("Nothing to do", run())
        self.assertEqual(list(Thread.objects.order_by("pk").values_list("pk", "title", "body", "pinned")), before)

    def test_a_thread_removed_by_a_moderator_is_not_posted_again(self):
        run()
        gone = Thread.objects.get(title="Ideas for Shipmark")
        Thread.objects.filter(pk=gone.pk).update(status=Thread.Status.REMOVED)
        run()
        self.assertEqual(Thread.objects.filter(title="Ideas for Shipmark").count(), 1)

    def test_creates_only_the_missing_ones(self):
        run()
        Thread.objects.filter(title="Share the first thing you shipped").delete()
        out = run()
        self.assertEqual(Thread.objects.count(), len(THREADS))
        self.assertEqual(out.count("Posted:"), 1)

    def test_dry_run_writes_nothing(self):
        out = run("--dry-run")
        self.assertEqual(Thread.objects.count(), 0)
        self.assertIn(f"{len(THREADS)} thread(s) to create", out)

    def test_an_inactive_board_is_skipped_with_a_warning(self):
        from community.models import Board
        Board.objects.filter(slug="feedback").update(is_active=False)
        out = run()
        self.assertEqual(Thread.objects.count(), len(THREADS) - 1)
        self.assertIn("'feedback'", out)

    @override_settings(COMMUNITY_ENABLED=False)
    def test_works_with_the_flag_off_and_stays_hidden(self):
        run()
        self.assertEqual(Thread.objects.count(), len(THREADS))
        self.assertEqual(self.client.get("/community/").status_code, 404)
        thread = Thread.objects.first()
        self.assertEqual(self.client.get(thread.get_absolute_url()).status_code, 404)

    @override_settings(COMMUNITY_ENABLED=True)
    def test_threads_show_up_when_the_community_is_on(self):
        run()
        page = self.client.get("/community/").content.decode()
        self.assertIn("What are you building this week?", page)
        self.assertIn("Ideas for Shipmark", page)

    def test_fails_clearly_without_the_system_account(self):
        User.objects.filter(username="shipmark").delete()
        with self.assertRaisesMessage(CommandError, "does not exist"):
            run()


class DemoSafetyTests(TestCase):
    """seed_community не запускається в production; демо-акаунти не рахуються як люди."""
    def seed(self):
        call_command("seed_community", stdout=StringIO())

    def test_refuses_without_debug(self):
        with override_settings(DEBUG=False):
            with self.assertRaisesMessage(CommandError, "only with DEBUG"):
                self.seed()
        self.assertFalse(User.objects.filter(username__startswith="demo-").exists())

    def test_refuses_with_production_like_settings_even_if_debug_is_on(self):
        with override_settings(DEBUG=True, SITE_URL="https://shipmark.org"):
            with self.assertRaisesMessage(CommandError, "production settings"):
                self.seed()
        self.assertFalse(User.objects.filter(username__startswith="demo-").exists())

    def test_refuses_with_the_production_settings_module(self):
        with override_settings(DEBUG=True), patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "config.settings.prod"}):
            with self.assertRaisesMessage(CommandError, "production settings"):
                self.seed()
        self.assertFalse(User.objects.filter(username__startswith="demo-").exists())

    def test_old_seed_is_retired_in_development(self):
        before = count_people()
        with override_settings(DEBUG=True), self.assertRaisesMessage(CommandError, "retired"):
            self.seed()
        self.assertFalse(User.objects.filter(username__startswith="demo-").exists())
        self.assertEqual(count_people(), before)

    def test_demo_accounts_are_not_in_the_counter_but_a_similar_real_name_is(self):
        make_user("demo-real", email="someone@example.com")  # looks like a demo name, but a real address: a person
        make_user("demo-fake", email="demo-fake@example.invalid")
        self.assertEqual(count_people(), 1)

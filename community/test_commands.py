"""post_welcome and seed_community."""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import override_settings

from accounts.models import User
from accounts.system import system_user
from moderation.models import AuditLog

from .management.commands import post_welcome as welcome
from .management.commands.seed_community import PEOPLE, THREADS
from .models import CommunityImage, Reply, Thread, Vote
from .tests import CommunityTestCase, old_user


def run(*args):
    out = StringIO()
    call_command(*args, stdout=out)
    return out.getvalue()


class PostWelcomeTests(CommunityTestCase):
    def test_posts_one_pinned_thread_from_the_system_account(self):
        output = run("post_welcome")
        thread = Thread.objects.get(title=welcome.TITLE)
        self.assertEqual(thread.author, system_user())
        self.assertTrue(thread.pinned)
        self.assertEqual(thread.board.slug, "help")  # the first active board
        self.assertIn(thread.get_absolute_url(), output)
        self.assertIn("/community/rules/", thread.body)
        log = AuditLog.objects.get(action="community.welcome_posted")
        self.assertIsNone(log.actor)
        self.assertEqual(log.target_id, str(thread.pk))

    def test_running_again_changes_nothing(self):
        run("post_welcome")
        output = run("post_welcome")
        self.assertIn("already exists", output)
        self.assertEqual(Thread.objects.filter(title=welcome.TITLE).count(), 1)
        self.assertEqual(AuditLog.objects.filter(action="community.welcome_posted").count(), 1)

    def test_force_posts_a_new_one_and_unpins_the_old(self):
        run("post_welcome")
        old = Thread.objects.get(title=welcome.TITLE)
        run("post_welcome", "--force", "--board", "off-topic")
        new = Thread.objects.filter(title=welcome.TITLE).exclude(pk=old.pk).get()
        old.refresh_from_db()
        self.assertFalse(old.pinned)
        self.assertTrue(new.pinned)
        self.assertEqual(new.board.slug, "off-topic")

    def test_a_removed_welcome_does_not_block_a_new_one(self):
        run("post_welcome")
        Thread.objects.filter(title=welcome.TITLE).update(status=Thread.Status.REMOVED, pinned=False)
        run("post_welcome")
        self.assertEqual(Thread.objects.filter(title=welcome.TITLE, pinned=True).count(), 1)

    def test_unknown_or_inactive_board_is_an_error(self):
        with self.assertRaises(CommandError):
            run("post_welcome", "--board", "nope")
        self.board.is_active = False
        self.board.save()
        with self.assertRaises(CommandError):
            run("post_welcome", "--board", "help")
        self.assertFalse(Thread.objects.filter(title=welcome.TITLE).exists())

    def test_works_with_the_flag_off_and_shows_on_top_with_the_official_mark(self):
        with override_settings(COMMUNITY_ENABLED=False):
            run("post_welcome")
        page = self.client.get("/community/")
        self.assertContains(page, "thread-list--pinned")
        self.assertContains(page, welcome.TITLE)
        thread = Thread.objects.get(title=welcome.TITLE)
        detail = self.client.get(thread.get_absolute_url())
        self.assertContains(detail, "@shipmark")
        self.assertContains(detail, 'href="/community/rules/"')

    def test_replies_to_the_welcome_notify_nobody(self):
        run("post_welcome")
        thread = Thread.objects.get(title=welcome.TITLE)
        self.assertEqual(self.reply(self.bob, thread=thread, body="Hello everyone!").status_code, 302)
        self.assertFalse(system_user().community_notifications.exists())  # the system account never signs in


class SeedCommunityTests(CommunityTestCase):
    def test_refuses_without_debug(self):
        with override_settings(DEBUG=False), self.assertRaises(CommandError):
            run("seed_community")
        self.assertFalse(User.objects.filter(username__startswith="demo-").exists())

    @override_settings(DEBUG=True)
    def test_creates_demo_content_through_the_services(self):
        run("seed_community")
        people = User.objects.filter(username__in=PEOPLE)
        self.assertEqual(people.count(), len(PEOPLE))
        self.assertFalse(any(person.has_usable_password() for person in people))
        self.assertTrue(all(person.email.endswith("@example.invalid") for person in people))
        self.assertEqual(Thread.objects.filter(author__in=people).count(), len(THREADS))
        self.assertTrue(Reply.objects.filter(author__in=people, depth=3).exists())
        self.assertTrue(Reply.objects.filter(author__in=people).exclude(sticker_key="").exists())
        self.assertTrue(CommunityImage.objects.filter(uploader__in=people).exists())
        self.assertFalse(Vote.objects.filter(thread__author=self.ann).exists())
        for vote in Vote.objects.select_related("thread", "reply"):
            self.assertNotEqual(vote.user_id, (vote.thread or vote.reply).author_id)  # nobody upvotes their own post
        self.assertEqual(self.client.get("/community/").status_code, 200)

    @override_settings(DEBUG=True)
    def test_running_again_replaces_the_demo_content_and_clear_removes_it(self):
        real = old_user("demo-real")  # a real account that only looks like a demo one stays
        run("seed_community")
        threads = Thread.objects.count()
        images = CommunityImage.objects.count()
        run("seed_community")
        self.assertEqual(Thread.objects.count(), threads)
        self.assertEqual(CommunityImage.objects.count(), images)
        output = run("seed_community", "--clear")
        self.assertIn(f"Removed {len(PEOPLE)} demo people", output)
        self.assertFalse(User.objects.filter(username__in=PEOPLE).exists())
        self.assertEqual(Thread.objects.count(), 1)  # the thread from setUp
        self.assertFalse(CommunityImage.objects.exists())
        self.assertTrue(User.objects.filter(pk=real.pk).exists())

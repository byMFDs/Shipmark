"""Community backend: the flag, reading, posting rules, abuse cases, moderation, deletion and export."""
import re
import tempfile
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts import badges
from accounts.deletion import delete_account
from accounts.export import build_export
from accounts.models import User
from accounts.system import system_user
from moderation import decisions, sanctions
from moderation.models import AuditLog, Notice, Report, Sanction
from projects.tests import image_file, make_user

from . import limits, ranking, services
from .models import Board, CommunityImage, Reply, ReplyNotification, Thread, Vote

TEMP_MEDIA = tempfile.mkdtemp(prefix="shipmark-test-community-")
REASON = "Advertising in every post, against the rules."


def old_user(username, days=30, **extra):
    """An account old enough for every community rule."""
    return make_user(username, date_joined=timezone.now() - timedelta(days=days), **extra)


def make_thread(author, title="How do I verify a domain?", body="I added the TXT record.", board=None, **extra):
    board = board or Board.objects.get(slug="help")
    return Thread.objects.create(board=board, author=author, title=title, body=body, **extra)


def stored(image):
    return default_storage.exists(image.image.name), default_storage.exists(image.thumb.name)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CommunityTestCase(TestCase):
    """Спільні дані для тестів спільноти."""
    def setUp(self):
        cache.clear()
        self.board = Board.objects.get(slug="help")
        self.ann = old_user("ann")
        self.bob = old_user("bob")
        self.mira = old_user("mira")
        badges.grant(self.mira, "moderator")
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")
        self.thread = make_thread(self.ann)

    def login(self, user):
        self.client.force_login(user)
        return self.client

    def new_thread(self, user, **data):
        payload = {"board": self.board.pk, "title": "A question about uptime", "body": "How many checks a day?"}
        payload.update(data)
        return self.login(user).post(reverse("community:new"), payload)

    def reply(self, user, thread=None, **data):
        thread = thread or self.thread
        return self.login(user).post(reverse("community:reply", args=[thread.pk]), data)

    def vote(self, user, target, value="1", json=False):
        name = "community:vote_thread" if isinstance(target, Thread) else "community:vote_reply"
        headers = {"Accept": "application/json"} if json else {}
        return self.login(user).post(reverse(name, args=[target.pk]), {"value": value}, headers=headers)

    def act(self, user, target, action, **extra):
        name = "moderation:act_thread" if isinstance(target, Thread) else "moderation:act_reply"
        data = {"action": action, "reason": REASON, "category": "spam", **extra}
        return self.login(user).post(reverse(name, args=[target.pk]), data)

    def ban(self, user, kind=Sanction.Kind.BAN):
        return sanctions.issue(user, kind, REASON, self.boss, length=timedelta(days=1))


# ---------- The flag ----------

class FlagTests(CommunityTestCase):
    """Перемикач COMMUNITY_ENABLED."""
    def urls(self):
        reply = services.create_reply(self.bob, self.thread, body="Check the TTL.")
        return [
            reverse("community:home"), reverse("community:board", args=["help"]), self.thread.get_absolute_url(),
            reverse("community:new"), reverse("community:thread_edit", args=[self.thread.pk]),
            reverse("community:thread_delete", args=[self.thread.pk]), reverse("community:reply_edit", args=[reply.pk]),
            reverse("moderation:report_thread", args=[self.thread.pk]),
            reverse("moderation:report_reply", args=[reply.pk]),
            reverse("moderation:act_thread", args=[self.thread.pk]), reverse("moderation:act_reply", args=[reply.pk]),
        ], reply

    def test_off_means_404_everywhere_and_no_link(self):
        urls, reply = self.urls()
        with override_settings(COMMUNITY_ENABLED=False):
            for user in (None, self.ann, self.mira, self.boss):
                if user:
                    self.client.force_login(user)
                for url in urls:
                    with self.subTest(url=url, user=user and user.username):
                        self.assertEqual(self.client.get(url).status_code, 404)
            self.client.force_login(self.bob)
            for url, data in [
                (reverse("community:new"), {"board": self.board.pk, "title": "Hello there", "body": "x"}),
                (reverse("community:reply", args=[self.thread.pk]), {"body": "x"}),
                (reverse("community:vote_thread", args=[self.thread.pk]), {"value": "1"}),
                (reverse("community:vote_reply", args=[reply.pk]), {"value": "1"}),
            ]:
                self.assertEqual(self.client.post(url, data).status_code, 404)
            self.assertEqual(Thread.objects.count(), 1)
            self.assertEqual(Vote.objects.count(), 0)
            self.assertNotContains(self.client.get("/explore/"), 'href="/community/"')

    def test_a_report_about_a_thread_cannot_be_opened_while_off(self):
        report = Report.objects.create(reporter=self.bob, thread=self.thread, target_owner=self.ann,
                                       target_repr=self.thread.title, reason="spam")
        self.client.force_login(self.mira)
        url = reverse("moderation:report_detail", args=[report.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        with override_settings(COMMUNITY_ENABLED=False):
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_on_shows_the_link(self):
        self.assertContains(self.client.get("/explore/"), 'href="/community/"')


# ---------- Reading ----------

class ReadTests(CommunityTestCase):
    """Читання тем і дошок."""
    def test_anonymous_reads_everything_public(self):
        services.create_reply(self.bob, self.thread, body="Wait an hour, DNS is slow.")
        for url in (reverse("community:home"), reverse("community:board", args=["help"]), self.thread.get_absolute_url()):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "How do I verify a domain?")
        self.assertContains(self.client.get(self.thread.get_absolute_url()), "DNS is slow")

    def test_wrong_slug_redirects_to_the_canonical_address(self):
        for url in (f"/community/t/{self.thread.pk}-nope/", f"/community/t/{self.thread.pk}/"):
            self.assertRedirects(self.client.get(url), self.thread.get_absolute_url(), status_code=301)

    def test_inactive_board_hides_its_threads(self):
        self.board.is_active = False
        self.board.save()
        self.assertEqual(self.client.get(reverse("community:board", args=["help"])).status_code, 404)
        self.assertEqual(self.client.get(self.thread.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("community:home")), "How do I verify a domain?")

    def test_search_by_title(self):
        make_thread(self.bob, title="Looking for a designer")
        response = self.client.get(reverse("community:home"), {"q": "DESIGNER"})
        self.assertContains(response, "Looking for a designer")
        self.assertNotContains(response, "How do I verify a domain?")
        self.assertContains(self.client.get(reverse("community:home"), {"q": "zzzz"}), "No threads match this search")

    def test_board_page_lists_only_its_threads(self):
        make_thread(self.bob, title="Coffee or tea today", board=Board.objects.get(slug="off-topic"))
        response = self.client.get(reverse("community:board", args=["help"]))
        self.assertContains(response, "How do I verify a domain?")
        self.assertNotContains(response, "Coffee or tea today")

    def test_sorts(self):
        now = timezone.now()
        old_hit = make_thread(self.ann, title="Old and loved", created_at=now - timedelta(days=20), score=30)
        fresh = make_thread(self.bob, title="Fresh and quiet", created_at=now - timedelta(minutes=5))
        week = make_thread(self.bob, title="This week favourite", created_at=now - timedelta(days=2), score=9)

        def order(**params):
            threads = self.client.get(reverse("community:home"), params).context["threads"]
            return [t.pk for t in threads if t.pk != self.thread.pk]

        self.assertEqual(order(sort="new"), [fresh.pk, week.pk, old_hit.pk])
        self.assertEqual(order(sort="top", t="all"), [old_hit.pk, week.pk, fresh.pk])
        self.assertEqual(order(sort="top", t="week"), [week.pk, fresh.pk])
        # hot: (10*30+10)*2 = 620, (10*9+10)*8 = 800, (0+10)*32 = 320
        self.assertEqual(order(), [week.pk, old_hit.pk, fresh.pk])
        self.assertEqual(order(sort="nonsense", t="nonsense"), [week.pk, old_hit.pk, fresh.pk])

    def test_hot_formula(self):
        now = timezone.now()
        thread = make_thread(self.ann, created_at=now - timedelta(hours=1), score=3, reply_count=80)
        hot = ranking.with_hot(Thread.objects.filter(pk=thread.pk), now).get().hot
        self.assertEqual(hot, (3 * 10 + 50 * 4 + 10) * 32)  # replies capped at 50

    def test_pinned_threads_sit_in_their_own_row(self):
        pinned = make_thread(self.bob, title="Welcome and rules", pinned=True)
        response = self.client.get(reverse("community:home"))
        self.assertEqual([t.pk for t in response.context["pinned"]], [pinned.pk])
        self.assertNotIn(pinned.pk, [t.pk for t in response.context["threads"]])

    def test_pages(self):
        for n in range(limits.THREADS_PER_PAGE + 2):
            make_thread(self.bob, title=f"Thread number {n}")
        first = self.client.get(reverse("community:home"), {"sort": "new"})
        self.assertEqual(len(first.context["threads"]), limits.THREADS_PER_PAGE)
        self.assertTrue(first.context["has_next"])
        second = self.client.get(reverse("community:home"), {"sort": "new", "page": 2})
        self.assertEqual(len(second.context["threads"]), 3)
        self.assertFalse(set(t.pk for t in first.context["threads"]) & set(t.pk for t in second.context["threads"]))

    def test_list_queries_do_not_grow_with_the_number_of_threads(self):
        def count():
            with CaptureQueriesContext(connection) as queries:
                self.assertEqual(self.client.get(reverse("community:home")).status_code, 200)
            return len(queries)

        self.client.force_login(self.bob)
        make_thread(self.mira, title="Already pinned", pinned=True)  # the pinned row has its own prefetch
        few = count()
        for n in range(15):
            author = old_user(f"user{n}")
            badges.grant(author, "moderator")
            make_thread(author, title=f"Another thread {n}", pinned=n < 2)
        self.assertEqual(count(), few)

    def test_thread_queries_do_not_grow_with_the_number_of_replies(self):
        def count():
            with CaptureQueriesContext(connection) as queries:
                self.assertEqual(self.client.get(self.thread.get_absolute_url()).status_code, 200)
            return len(queries)

        self.client.force_login(self.bob)
        first = services.create_reply(self.mira, self.thread, body="First.")
        services.create_reply(self.bob, self.thread, parent=first, body="Second.")
        few = count()
        for n in range(12):
            author = old_user(f"user{n}")
            top = services.create_reply(author, self.thread, body=f"Top {n}", images=[_clean()])
            child = services.create_reply(self.mira, self.thread, parent=top, body=f"Child {n}")
            services.create_reply(author, self.thread, parent=child, body=f"Grandchild {n}")
            services.set_vote(self.bob, top, True)
        self.assertEqual(count(), few)

    def test_reply_tree_sorting_and_pages(self):
        low = services.create_reply(self.bob, self.thread, body="Low.")
        high = services.create_reply(self.mira, self.thread, body="High.")
        services.set_vote(self.ann, high, True)
        best = self.client.get(self.thread.get_absolute_url()).context["nodes"]
        self.assertEqual([n.reply.pk for n in best], [high.pk, low.pk])
        newest = self.client.get(self.thread.get_absolute_url(), {"sort": "new"}).context["nodes"]
        self.assertEqual([n.reply.pk for n in newest], [high.pk, low.pk])  # high was written last
        services.set_vote(self.mira, low, True)
        services.set_vote(self.bob, low, True)
        best = self.client.get(self.thread.get_absolute_url()).context["nodes"]
        self.assertEqual([n.reply.pk for n in best], [low.pk, high.pk])
        for n in range(limits.REPLIES_PER_PAGE):
            services.create_reply(self.bob, self.thread, body=f"More {n}")
        response = self.client.get(self.thread.get_absolute_url())
        self.assertEqual(len(response.context["nodes"]), limits.REPLIES_PER_PAGE)
        self.assertTrue(response.context["has_next"])


def _clean(**kwargs):
    from .images import clean_upload

    return clean_upload(image_file(**kwargs))


# ---------- Posting ----------

class PostingTests(CommunityTestCase):
    """Створення тем і правила для нових акаунтів."""
    def test_anonymous_cannot_write(self):
        for url, data in [
            (reverse("community:new"), {"board": self.board.pk, "title": "Hello there", "body": "x"}),
            (reverse("community:reply", args=[self.thread.pk]), {"body": "x"}),
            (reverse("community:vote_thread", args=[self.thread.pk]), {"value": "1"}),
            (reverse("community:thread_edit", args=[self.thread.pk]), {"body": "x"}),
            (reverse("community:thread_delete", args=[self.thread.pk]), {}),
            (reverse("moderation:report_thread", args=[self.thread.pk]), {"reason": "spam"}),
        ]:
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("/login/", response["Location"])
        response = self.client.post(reverse("community:vote_thread", args=[self.thread.pk]), {"value": "1"},
                                    headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual((Thread.objects.count(), Reply.objects.count(), Vote.objects.count()), (1, 0, 0))

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.bob)
        for url, data in [
            (reverse("community:new"), {"board": self.board.pk, "title": "Hello there", "body": "x"}),
            (reverse("community:reply", args=[self.thread.pk]), {"body": "x"}),
            (reverse("community:vote_thread", args=[self.thread.pk]), {"value": "1"}),
        ]:
            self.assertEqual(client.post(url, data).status_code, 403)
        self.assertEqual((Thread.objects.count(), Reply.objects.count(), Vote.objects.count()), (1, 0, 0))

    def test_post_a_thread_with_images(self):
        response = self.new_thread(self.bob, images=[image_file(size=(2400, 1200)), image_file(fmt="JPEG", name="b.jpg")])
        thread = Thread.objects.get(title="A question about uptime")
        self.assertRedirects(response, thread.get_absolute_url())
        self.assertEqual((thread.author, thread.status, thread.score, thread.pinned), (self.bob, "published", 0, False))
        images = list(thread.images.all())
        self.assertEqual(len(images), 2)
        big = images[0]
        self.assertEqual((big.width, big.height), (1600, 800))  # display copy: longest side 1600
        self.assertEqual((big.thumb_width, big.thumb_height), (640, 320))
        self.assertTrue(big.image.name.startswith("community/") and big.image.name.endswith(".webp"))
        self.assertNotIn("shot", big.image.name)  # never the uploaded name
        self.assertEqual(stored(big), (True, True))
        self.assertEqual(big.uploader, self.bob)

    def test_forged_fields_are_ignored(self):
        self.new_thread(self.bob, status="locked", pinned="on", score="999", reply_count="5", author=self.ann.pk,
                        deleted_at="2020-01-01", created_at="2020-01-01")
        thread = Thread.objects.get(title="A question about uptime")
        self.assertEqual((thread.status, thread.pinned, thread.score, thread.reply_count, thread.author),
                         ("published", False, 0, 0, self.bob))
        self.assertIsNone(thread.deleted_at)
        self.assertGreater(thread.created_at, timezone.now() - timedelta(minutes=1))

    def test_thread_validation(self):
        hidden = Board.objects.create(slug="hidden", name="Hidden", is_active=False)
        cases = [
            {"board": hidden.pk}, {"board": 999999}, {"board": ""}, {"title": "Hey"}, {"title": "x" * 121},
            {"body": ""}, {"body": "x" * 8001},
            {"images": [image_file(name=f"{n}.png") for n in range(5)]},
            {"images": [image_file(fmt="GIF", name="a.gif")]},
        ]
        for case in cases:
            with self.subTest(case={k: str(v)[:30] for k, v in case.items()}):
                self.assertEqual(self.new_thread(self.bob, **case).status_code, 400)
        self.assertEqual(Thread.objects.count(), 1)
        self.assertEqual(CommunityImage.objects.count(), 0)

    def test_markdown_is_sanitized(self):
        self.new_thread(self.bob, body='<script>alert(1)</script> **bold** <img src=x onerror=alert(1)> [x](javascript:alert(1))')
        html = self.client.get(Thread.objects.get(author=self.bob).get_absolute_url()).content.decode()
        self.assertIn("<strong>bold</strong>", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<img src=x", html)
        self.assertNotIn("javascript:", html)

    def test_new_accounts_wait_ten_minutes(self):
        newbie = make_user("newbie")
        self.assertEqual(self.new_thread(newbie).status_code, 403)
        self.assertEqual(self.reply(newbie, body="Hi").status_code, 403)
        self.assertEqual(self.vote(newbie, self.thread, json=True).status_code, 403)
        self.assertEqual((Thread.objects.count(), Reply.objects.count(), Vote.objects.count()), (1, 0, 0))
        User.objects.filter(pk=newbie.pk).update(date_joined=timezone.now() - timedelta(minutes=11))
        self.assertEqual(self.reply(User.objects.get(pk=newbie.pk), body="Hi").status_code, 302)

    def test_accounts_under_a_day_get_one_link_and_no_images(self):
        young = old_user("young", days=0.5)
        two = "See https://a.example and [this](https://b.example)."
        self.assertEqual(self.new_thread(young, body=two).status_code, 400)
        self.assertEqual(self.reply(young, body=two).status_code, 400)
        self.assertEqual(self.reply(young, body="Only [one](mailto:me@a.example) and <http://b.example>").status_code, 400)
        self.assertEqual(self.reply(young, body="Photo", images=[image_file()]).status_code, 400)
        self.assertEqual(self.new_thread(young, images=[image_file()]).status_code, 400)
        self.assertEqual((Thread.objects.count(), Reply.objects.count(), CommunityImage.objects.count()), (1, 0, 0))
        self.assertEqual(self.reply(young, body="One link: https://a.example").status_code, 302)
        self.assertEqual(self.reply(self.bob, body=two, images=[image_file()]).status_code, 302)  # an old account

    def test_muted_suspended_and_banned_cannot_write(self):
        mine = make_thread(self.bob, title="My own thread here")
        self.ban(self.bob, Sanction.Kind.MUTE)
        self.assertEqual(self.new_thread(self.bob).status_code, 403)
        self.assertEqual(self.reply(self.bob, body="Hi").status_code, 403)
        self.assertEqual(self.vote(self.bob, self.thread, json=True).status_code, 403)
        self.assertEqual(self.client.post(reverse("community:thread_edit", args=[mine.pk]), {"body": "x"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("moderation:report_thread", args=[self.thread.pk]),
                                          {"reason": "spam"}).status_code, 403)
        # A muted person can still take their own post down.
        self.assertEqual(self.client.post(reverse("community:thread_delete", args=[mine.pk])).status_code, 302)

        zed = old_user("zed", is_suspended=True)
        own = make_thread(zed, title="Thread of a suspended one")
        self.assertEqual(self.new_thread(zed).status_code, 403)
        self.assertEqual(self.client.post(reverse("community:thread_delete", args=[own.pk])).status_code, 404)

        cat = old_user("cat")
        self.ban(cat)
        self.assertEqual(self.new_thread(cat).status_code, 403)  # the ban page
        self.assertEqual((Thread.objects.filter(author__in=[self.bob, cat]).exclude(pk=mine.pk).count(),
                          Reply.objects.count(), Vote.objects.count()), (0, 0, 0))

    def test_rate_limits(self):
        for n in range(limits.THREADS_PER_HOUR):
            self.assertEqual(self.new_thread(self.bob, title=f"Thread number {n}").status_code, 302)
        self.assertEqual(self.new_thread(self.bob, title="One too many").status_code, 400)
        self.assertFalse(Thread.objects.filter(title="One too many").exists())

        for n in range(limits.REPLIES_PER_HOUR):
            self.assertEqual(self.reply(self.bob, body=f"A reply that is long enough, number {n}").status_code, 302)
        self.assertEqual(self.reply(self.bob, body="The thirty-first reply of the hour").status_code, 400)
        self.assertEqual(Reply.objects.count(), limits.REPLIES_PER_HOUR)

    def test_upload_limit_counts_every_image(self):
        cat = old_user("cat")
        for n in range(5):  # 5 x 2 = 10 images
            self.assertEqual(self.reply(cat, body=f"Pictures, part {n} of the story",
                                        images=[image_file(), image_file()]).status_code, 302)
        self.assertEqual(self.reply(cat, body="And one more picture", images=[image_file()]).status_code, 400)
        self.assertEqual(CommunityImage.objects.count(), limits.UPLOADS_PER_HOUR)

    def test_vote_limit(self):
        threads = [make_thread(self.ann, title=f"Thread to vote {n}") for n in range(3)]
        with mock.patch.object(limits, "VOTES_PER_HOUR", 2):
            self.assertEqual(self.vote(self.bob, threads[0], json=True).status_code, 200)
            self.assertEqual(self.vote(self.bob, threads[1], json=True).status_code, 200)
            self.assertEqual(self.vote(self.bob, threads[2], json=True).status_code, 429)
        self.assertEqual(Vote.objects.count(), 2)

    def test_duplicates(self):
        self.assertEqual(self.new_thread(self.bob).status_code, 302)
        self.assertEqual(self.new_thread(self.bob, title="a  QUESTION about uptime").status_code, 400)  # same text
        self.assertEqual(self.new_thread(self.ann).status_code, 302)  # another person may

        long_text = "This is the very same long reply, pasted again and again."
        other = make_thread(self.ann, title="Another thread entirely")
        self.assertEqual(self.reply(self.bob, body=long_text).status_code, 302)
        self.assertEqual(self.reply(self.bob, body=long_text, thread=other).status_code, 400)
        # Short answers are only duplicates in the same place; image-only replies never.
        self.assertEqual(self.reply(self.bob, body="Thanks!").status_code, 302)
        self.assertEqual(self.reply(self.bob, body="Thanks!").status_code, 400)
        self.assertEqual(self.reply(self.bob, body="Thanks!", thread=other).status_code, 302)
        self.assertEqual(self.reply(self.bob, images=[image_file()]).status_code, 302)
        self.assertEqual(self.reply(self.bob, images=[image_file()]).status_code, 302)


class ReplyTests(CommunityTestCase):
    """Відповіді та їхня вкладеність."""
    def test_reply_updates_the_counters(self):
        before = self.thread.last_activity_at
        self.assertEqual(self.reply(self.bob, body="Check the TTL.").status_code, 302)
        self.thread.refresh_from_db()
        reply = Reply.objects.get()
        self.assertEqual((self.thread.reply_count, reply.depth, reply.parent, reply.root), (1, 1, None, None))
        self.assertGreater(self.thread.last_activity_at, before)

    def test_depth_stops_at_three(self):
        first = services.create_reply(self.bob, self.thread, body="One.")
        self.reply(self.ann, parent=first.pk, body="Two.")
        second = Reply.objects.get(body="Two.")
        self.reply(self.bob, parent=second.pk, body="Three.")
        third = Reply.objects.get(body="Three.")
        self.reply(self.ann, parent=third.pk, body="Four, an answer to three.")
        fourth = Reply.objects.get(body__startswith="Four")
        self.assertEqual([r.depth for r in (first, second, third, fourth)], [1, 2, 3, 3])
        self.assertEqual((fourth.parent, fourth.root, third.root, second.root), (second, first, first, first))
        with self.assertRaises(IntegrityError), transaction.atomic():  # the database refuses a forged depth too
            Reply.objects.create(thread=self.thread, parent=third, root=first, depth=4, author=self.ann, body="x")

    def test_forged_parent_is_refused(self):
        other = make_thread(self.ann, title="Another thread entirely")
        foreign = services.create_reply(self.ann, other, body="In another thread.")
        removed = services.create_reply(self.ann, self.thread, body="Removed.")
        decisions.remove_reply(removed, self.mira, REASON)
        for parent in (foreign.pk, removed.pk, 999999, "abc", "-1"):
            with self.subTest(parent=parent):
                self.assertEqual(self.reply(self.bob, parent=parent, body="An answer to nothing.").status_code, 400)
        self.assertEqual(Reply.objects.filter(author=self.bob).count(), 0)

    def test_posted_sticker_cannot_set_the_database_field(self):
        self.assertEqual(self.reply(self.bob, sticker="thumbs-up").status_code, 400)
        self.assertEqual(self.reply(self.bob, body="Text remains valid.", sticker="thumbs-up").status_code, 302)
        self.assertEqual(Reply.objects.get().sticker_key, "")

    def test_reply_validation(self):
        self.assertEqual(self.reply(self.bob).status_code, 400)  # nothing at all
        self.assertEqual(self.reply(self.bob, body="   ").status_code, 400)
        self.assertEqual(self.reply(self.bob, body="x" * 4001).status_code, 400)
        self.assertEqual(self.reply(self.bob, body="Three", images=[image_file(name=f"{n}.png") for n in range(3)]).status_code, 400)
        self.assertEqual(Reply.objects.count(), 0)
        self.assertEqual(self.reply(self.bob, images=[image_file(), image_file()]).status_code, 302)  # images alone
        self.assertEqual(Reply.objects.get().images.count(), 2)

    def test_locked_thread_accepts_replies_from_moderators_only(self):
        decisions.lock_thread(self.thread, self.mira, REASON)
        self.assertEqual(self.reply(self.bob, body="Let me in.").status_code, 403)
        self.assertEqual(self.reply(self.ann, body="It is my thread.").status_code, 403)
        self.assertEqual(self.reply(self.mira, body="A note from the moderators.").status_code, 302)
        self.assertEqual(self.reply(self.boss, body="And from the superuser.").status_code, 302)
        self.assertEqual(Reply.objects.count(), 2)

    def test_no_replies_to_removed_or_hidden_threads(self):
        decisions.remove_thread(self.thread, self.mira, REASON)
        self.assertEqual(self.reply(self.bob, body="Hello?").status_code, 404)
        self.assertEqual(self.reply(self.ann, body="My own removed thread.").status_code, 403)
        self.assertEqual(Reply.objects.count(), 0)


class OwnershipTests(CommunityTestCase):
    """Редагувати й видаляти можна лише своє."""
    def setUp(self):
        super().setUp()
        self.answer = services.create_reply(self.ann, self.thread, body="My own answer.")

    def test_others_cannot_edit_or_delete(self):
        for user in (self.bob, self.mira, self.boss):  # not even moderators: they remove with a reason in /mod/
            self.client.force_login(user)
            for name, pk in [("community:thread_edit", self.thread.pk), ("community:thread_delete", self.thread.pk),
                             ("community:reply_edit", self.answer.pk), ("community:reply_delete", self.answer.pk)]:
                with self.subTest(user=user.username, name=name):
                    self.assertEqual(self.client.get(reverse(name, args=[pk])).status_code, 404)
                    self.assertEqual(self.client.post(reverse(name, args=[pk]), {"body": "Hacked", "title": "Hacked title"}).status_code, 404)
        self.thread.refresh_from_db()
        self.answer.refresh_from_db()
        self.assertEqual((self.thread.body, self.thread.deleted_at), ("I added the TXT record.", None))
        self.assertEqual((self.answer.body, self.answer.deleted_at), ("My own answer.", None))

    def test_edit_inside_the_silent_window(self):
        self.login(self.ann).post(reverse("community:thread_edit", args=[self.thread.pk]),
                                  {"title": "A better title", "body": "Better text."})
        self.thread.refresh_from_db()
        self.assertEqual((self.thread.title, self.thread.body, self.thread.edited_at), ("A better title", "Better text.", None))
        self.assertEqual(self.thread.slug, "a-better-title")
        self.assertRedirects(self.client.get(f"/community/t/{self.thread.pk}-how-do-i-verify-a-domain/"),
                             self.thread.get_absolute_url(), status_code=301)
        self.client.post(reverse("community:reply_edit", args=[self.answer.pk]), {"body": "Better answer."})
        self.answer.refresh_from_db()
        self.assertEqual((self.answer.body, self.answer.edited_at), ("Better answer.", None))

    def test_later_edits_are_marked_and_cannot_change_the_title(self):
        long_ago = timezone.now() - timedelta(minutes=16)
        Thread.objects.filter(pk=self.thread.pk).update(created_at=long_ago)
        Reply.objects.filter(pk=self.answer.pk).update(created_at=long_ago)
        self.login(self.ann).post(reverse("community:thread_edit", args=[self.thread.pk]),
                                  {"title": "Bait and switch", "body": "Later text."})
        self.thread.refresh_from_db()
        self.assertEqual((self.thread.title, self.thread.body), ("How do I verify a domain?", "Later text."))
        self.assertIsNotNone(self.thread.edited_at)
        self.client.post(reverse("community:reply_edit", args=[self.answer.pk]), {"body": "Later answer."})
        self.answer.refresh_from_db()
        self.assertIsNotNone(self.answer.edited_at)
        self.assertContains(self.client.get(self.thread.get_absolute_url()), "edited")

    def test_edit_keeps_the_rules(self):
        self.client.force_login(self.ann)
        url = reverse("community:thread_edit", args=[self.thread.pk])
        self.assertEqual(self.client.post(url, {"title": self.thread.title, "body": ""}).status_code, 400)
        decisions.lock_thread(self.thread, self.mira, REASON)
        self.assertEqual(self.client.post(url, {"title": self.thread.title, "body": "x"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("community:reply_edit", args=[self.answer.pk]), {"body": "x"}).status_code, 403)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.body, "I added the TXT record.")

    def test_delete_thread_without_replies(self):
        lonely = services.create_thread(self.bob, self.board, "A thread nobody answered", "Text.", [_clean()])
        image = lonely.images.get()
        self.login(self.bob)
        self.assertEqual(self.client.get(reverse("community:thread_delete", args=[lonely.pk])).status_code, 200)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("community:thread_delete", args=[lonely.pk]))
        self.assertRedirects(response, reverse("community:home"))
        lonely.refresh_from_db()
        self.assertEqual(lonely.body, "")  # wiped for real; the row is a soft delete
        self.assertIsNotNone(lonely.deleted_at)
        self.assertEqual(stored(image), (False, False))
        self.assertEqual(self.client.get(lonely.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("community:home")), "A thread nobody answered")

    def test_delete_thread_with_replies_keeps_the_replies(self):
        services.create_reply(self.bob, self.thread, body="A useful answer from Bob.")
        self.login(self.ann).post(reverse("community:thread_delete", args=[self.thread.pk]))
        response = self.client.get(self.thread.get_absolute_url())
        self.assertContains(response, "[deleted]")
        self.assertContains(response, "A useful answer from Bob.")
        self.assertNotContains(response, "I added the TXT record.")

    def test_delete_reply(self):
        child = services.create_reply(self.bob, self.thread, parent=self.answer, body="Bob answers Ann.")
        leaf = services.create_reply(self.ann, self.thread, parent=child, body="Ann again, a leaf.")
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.reply_count, 3)
        self.login(self.ann)
        self.client.post(reverse("community:reply_delete", args=[self.answer.pk]))
        self.client.post(reverse("community:reply_delete", args=[leaf.pk]))
        self.client.post(reverse("community:reply_delete", args=[leaf.pk]))  # twice: 404, counted once
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.reply_count, 1)
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertIn("Bob answers Ann.", html)
        self.assertNotIn("My own answer.", html)
        self.assertNotIn("Ann again, a leaf.", html)
        self.assertEqual(html.count("[deleted]"), 1)  # the parent keeps its place; the leaf is simply gone


class VoteTests(CommunityTestCase):
    """Голоси."""
    def test_vote_and_take_it_back(self):
        response = self.vote(self.bob, self.thread, json=True)
        self.assertEqual(response.json(), {"ok": True, "voted": True, "score": 1})
        self.assertEqual(self.vote(self.bob, self.thread, json=True).json()["score"], 1)  # twice counts once
        self.assertEqual(self.vote(self.mira, self.thread, json=True).json()["score"], 2)
        self.assertEqual(self.vote(self.bob, self.thread, "0", json=True).json(), {"ok": True, "voted": False, "score": 1})
        self.assertEqual(self.vote(self.bob, self.thread, "0", json=True).json()["score"], 1)
        self.assertEqual(Vote.objects.count(), 1)
        self.assertRedirects(self.vote(self.bob, self.thread), self.thread.get_absolute_url())  # plain form

    def test_no_vote_for_your_own_post_and_no_downvotes(self):
        answer = services.create_reply(self.ann, self.thread, body="My answer.")
        self.assertEqual(self.vote(self.ann, self.thread, json=True).status_code, 400)
        self.assertEqual(self.vote(self.ann, answer, json=True).status_code, 400)
        for value in ("-1", "2", "", "up"):
            self.assertEqual(self.vote(self.bob, self.thread, value, json=True).status_code, 400)
        self.thread.refresh_from_db()
        self.assertEqual((Vote.objects.count(), self.thread.score), (0, 0))

    def test_no_votes_on_hidden_things(self):
        answer = services.create_reply(self.ann, self.thread, body="My answer.")
        gone = services.create_reply(self.ann, self.thread, body="Deleted answer.")
        services.delete_reply(gone)
        self.assertEqual(self.vote(self.bob, gone, json=True).status_code, 404)
        decisions.remove_reply(answer, self.mira, REASON)
        self.assertEqual(self.vote(self.bob, answer, json=True).status_code, 404)
        decisions.remove_thread(self.thread, self.mira, REASON)
        self.assertEqual(self.vote(self.bob, self.thread, json=True).status_code, 404)
        self.assertEqual(Vote.objects.count(), 0)

    def test_database_keeps_one_vote_per_person(self):
        Vote.objects.create(user=self.bob, thread=self.thread)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(user=self.bob, thread=self.thread)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(user=self.bob)  # no target


# ---------- Moderation ----------

class ModerationTests(CommunityTestCase):
    """Модерація тем і відповідей."""
    def test_only_moderators_reach_the_moderate_pages(self):
        reply = services.create_reply(self.ann, self.thread, body="An answer.")
        clerk = old_user("clerk", is_staff=True)  # staff without the badge is not a moderator
        for user in (self.bob, self.ann, clerk):
            self.client.force_login(user)
            for target in (self.thread, reply):
                self.assertEqual(self.act(user, target, "remove_thread").status_code, 404)
                name = "moderation:act_thread" if target is self.thread else "moderation:act_reply"
                self.assertEqual(self.client.get(reverse(name, args=[target.pk])).status_code, 404)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.status, "published")
        self.assertNotContains(self.login(self.bob).get(self.thread.get_absolute_url()), "/mod/act/")
        self.assertContains(self.login(self.mira).get(self.thread.get_absolute_url()), f"/mod/act/thread/{self.thread.pk}/")

    def test_remove_thread(self):
        thread = services.create_thread(self.ann, self.board, "Buy cheap followers here", "Spam.", [_clean()])
        image = thread.images.get()
        report = Report.objects.create(reporter=self.bob, thread=thread, target_owner=self.ann,
                                       target_repr=thread.title, reason="spam")
        self.assertEqual(self.act(self.mira, thread, "remove_thread", reason="").status_code, 200)  # reason is required
        self.assertEqual(Thread.objects.get(pk=thread.pk).status, "published")
        with self.captureOnCommitCallbacks(execute=True):
            self.assertRedirects(self.act(self.mira, thread, "remove_thread"), thread.get_absolute_url(),
                                 fetch_redirect_response=False)
        thread.refresh_from_db()
        self.assertEqual((thread.status, thread.removed_reason, thread.removed_by), ("removed", REASON, self.mira))
        self.assertEqual(thread.body, "Spam.")  # kept for an appeal or a restore
        self.assertEqual(stored(image), (False, False))  # the pictures are gone at once
        self.assertFalse(thread.images.exists())
        report.refresh_from_db()
        self.assertEqual((report.status, report.handled_by), ("resolved", self.mira))
        notice = Notice.objects.get(user=self.ann, kind="thread_removed")
        self.assertEqual(notice.reason, REASON)
        log = AuditLog.objects.get(action="moderation.thread.removed")
        self.assertEqual((log.actor, log.metadata["reason"], log.metadata["images_deleted"]), (self.mira, REASON, 1))
        # Public: gone. Author: sees it with the reason. Moderators: see it.
        self.assertEqual(self.login(self.bob).get(thread.get_absolute_url()).status_code, 404)
        listed = self.client.get(reverse("community:home")).context["threads"]
        self.assertNotIn(thread.pk, [t.pk for t in listed])  # (the reporter's notice still names it)
        self.assertContains(self.login(self.ann).get(thread.get_absolute_url()), REASON)
        self.assertEqual(self.login(self.mira).get(thread.get_absolute_url()).status_code, 200)

    def test_remove_reply(self):
        top = services.create_reply(self.bob, self.thread, body="Rude words.", images=[_clean()])
        services.create_reply(self.ann, self.thread, parent=top, body="Please stay polite.")
        image = top.images.get()
        with self.captureOnCommitCallbacks(execute=True):
            self.act(self.mira, top, "remove_reply")
        top.refresh_from_db()
        self.thread.refresh_from_db()
        self.assertEqual((top.status, top.removed_reason, self.thread.reply_count), ("removed", REASON, 1))
        self.assertEqual(stored(image), (False, False))
        self.assertTrue(Notice.objects.filter(user=self.bob, kind="reply_removed", reason=REASON).exists())
        self.assertTrue(AuditLog.objects.filter(action="moderation.reply.removed", actor=self.mira).exists())
        html = self.login(self.ann).get(self.thread.get_absolute_url()).content.decode()
        self.assertIn("[removed]", html)
        self.assertNotIn("Rude words.", html)
        self.assertIn("Please stay polite.", html)

    def test_lock_and_pin(self):
        self.act(self.mira, self.thread, "lock_thread")
        self.thread.refresh_from_db()
        self.assertEqual((self.thread.status, self.thread.lock_reason), ("locked", REASON))
        self.assertTrue(Notice.objects.filter(user=self.ann, kind="thread_locked", reason=REASON).exists())
        self.assertContains(self.client.get(self.thread.get_absolute_url()), "This thread is locked")
        self.act(self.mira, self.thread, "pin_thread")
        self.act(self.mira, self.thread, "unlock_thread")
        self.thread.refresh_from_db()
        self.assertEqual((self.thread.status, self.thread.pinned), ("published", True))
        self.assertTrue(Notice.objects.filter(user=self.ann, kind="thread_pinned").exists())
        self.act(self.mira, self.thread, "unpin_thread")
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.pinned)
        actions = set(AuditLog.objects.filter(target_type="community.thread").values_list("action", flat=True))
        self.assertEqual(actions, {f"moderation.thread.{a}" for a in ("locked", "unlocked", "pinned", "unpinned")})

    def test_actions_that_do_not_fit_are_refused(self):
        reply = services.create_reply(self.ann, self.thread, body="An answer.")
        for target, action in [(self.thread, "remove_reply"), (self.thread, "remove_project"), (self.thread, "unlock_thread"),
                               (self.thread, "unpin_thread"), (self.thread, "clear_profile"), (reply, "remove_thread"),
                               (reply, "pin_thread"), (reply, "lock_thread")]:
            with self.subTest(action=action):
                self.assertEqual(self.act(self.mira, target, action).status_code, 200)  # the form says: invalid choice
        self.thread.refresh_from_db()
        reply.refresh_from_db()
        self.assertEqual((self.thread.status, self.thread.pinned, reply.status), ("published", False, "published"))
        self.assertFalse(AuditLog.objects.filter(target_type__startswith="community.").exists())

    def test_protected_accounts_pin_yes_remove_and_lock_no(self):
        colleague = old_user("colleague")
        badges.grant(colleague, "moderator")
        official = old_user("official-acc")
        badges.grant(official, "official")
        for author in (colleague, official, self.boss, system_user(), self.mira):  # the last one: her own thread
            thread = make_thread(author, title=f"Thread of {author.username}")
            reply = services.create_reply(author, thread, body="A protected reply.")
            with self.subTest(author=author.username):
                self.assertEqual(self.act(self.mira, thread, "remove_thread").status_code, 200)  # not offered
                self.assertEqual(self.act(self.mira, thread, "lock_thread").status_code, 200)
                self.assertEqual(self.act(self.mira, reply, "remove_reply").status_code, 403)
                self.assertEqual(self.act(self.mira, thread, "mute", length=1, unit="days").status_code, 200)
                with self.assertRaises(Exception):
                    decisions.remove_thread(thread, self.mira, REASON)  # the decision itself refuses too
                with self.assertRaises(Exception):
                    decisions.lock_thread(thread, self.mira, REASON)
                thread.refresh_from_db()
                reply.refresh_from_db()
                self.assertEqual((thread.status, reply.status), ("published", "published"))
                self.assertEqual(self.act(self.mira, thread, "pin_thread").status_code, 302)
                thread.refresh_from_db()
                self.assertTrue(thread.pinned)
        # A superuser may remove a moderator's thread.
        thread = Thread.objects.get(title="Thread of colleague")
        self.assertEqual(self.act(self.boss, thread, "remove_thread").status_code, 302)
        thread.refresh_from_db()
        self.assertEqual(thread.status, "removed")

    def test_pin_needs_a_moderator(self):
        with self.assertRaises(Exception):
            decisions.pin_thread(self.thread, self.bob, REASON)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.pinned)

    def test_muted_moderator_cannot_act(self):
        self.ban(self.mira, Sanction.Kind.MUTE)
        self.assertEqual(self.act(self.mira, self.thread, "remove_thread").status_code, 403)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.status, "published")

    def test_reports_reach_the_queue_with_the_object(self):
        reply = services.create_reply(self.ann, self.thread, body="A reply somebody reports.")
        self.login(self.bob)
        self.assertEqual(self.client.get(reverse("moderation:report_thread", args=[self.thread.pk])).status_code, 200)
        self.client.post(reverse("moderation:report_thread", args=[self.thread.pk]), {"reason": "spam", "details": "Ads."})
        self.client.post(reverse("moderation:report_thread", args=[self.thread.pk]), {"reason": "spam"})  # once
        self.client.post(reverse("moderation:report_reply", args=[reply.pk]), {"reason": "inappropriate"})
        self.assertEqual(Report.objects.count(), 2)
        thread_report = Report.objects.get(thread=self.thread)
        reply_report = Report.objects.get(reply=reply)
        self.assertEqual((thread_report.kind, thread_report.target_owner, reply_report.kind), ("thread", self.ann, "reply"))
        # Not your own post.
        self.login(self.ann).post(reverse("moderation:report_thread", args=[self.thread.pk]), {"reason": "spam"})
        self.client.post(reverse("moderation:report_reply", args=[reply.pk]), {"reason": "spam"})
        self.assertEqual(Report.objects.count(), 2)

        self.login(self.mira)
        queue = self.client.get(reverse("moderation:queue"), {"kind": "reply"})
        self.assertEqual([r.pk for r in queue.context["reports"]], [reply_report.pk])
        detail = self.client.get(reverse("moderation:report_detail", args=[reply_report.pk]))
        self.assertContains(detail, "A reply somebody reports.")
        self.client.post(reverse("moderation:report_detail", args=[reply_report.pk]),
                         {"action": "remove_reply", "reason": REASON})
        reply.refresh_from_db()
        reply_report.refresh_from_db()
        self.assertEqual((reply.status, reply_report.status), ("removed", "resolved"))
        detail = self.client.get(reverse("moderation:report_detail", args=[thread_report.pk]))
        self.assertContains(detail, "I added the TXT record.")
        self.client.post(reverse("moderation:report_detail", args=[thread_report.pk]), {"action": "dismiss", "reason": REASON})
        thread_report.refresh_from_db()
        self.assertEqual(thread_report.status, "dismissed")

    def test_hidden_things_cannot_be_reported(self):
        reply = services.create_reply(self.ann, self.thread, body="An answer.")
        services.delete_reply(reply)
        self.login(self.bob)
        self.assertEqual(self.client.post(reverse("moderation:report_reply", args=[reply.pk]), {"reason": "spam"}).status_code, 404)
        decisions.remove_thread(self.thread, self.mira, REASON)
        self.assertEqual(self.client.post(reverse("moderation:report_thread", args=[self.thread.pk]), {"reason": "spam"}).status_code, 404)
        self.assertEqual(Report.objects.count(), 0)

    def test_report_has_one_target(self):
        reply = services.create_reply(self.ann, self.thread, body="An answer.")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Report.objects.create(reporter=self.bob, thread=self.thread, reply=reply, target_repr="x", reason="spam")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Report.objects.create(reporter=self.bob, thread=self.thread, target_user=self.ann, target_repr="x", reason="spam")

    def test_restore_is_for_superusers(self):
        reply = services.create_reply(self.bob, self.thread, body="An answer.")
        decisions.remove_reply(reply, self.mira, REASON)
        decisions.remove_thread(self.thread, self.mira, REASON)
        with self.assertRaises(Exception):
            decisions.restore_thread(self.thread, self.mira)
        self.assertTrue(decisions.restore_thread(self.thread, self.boss))
        self.assertTrue(decisions.restore_reply(reply, self.boss))
        self.thread.refresh_from_db()
        self.assertEqual((self.thread.status, self.thread.reply_count), ("published", 1))
        self.assertTrue(Notice.objects.filter(user=self.ann, kind="post_restored").exists())

    def test_admin_pages_open(self):
        services.create_reply(self.bob, self.thread, body="An answer.", images=[_clean()])
        self.client.force_login(self.boss)
        for name in ("board", "thread", "reply", "communityimage"):
            self.assertEqual(self.client.get(reverse(f"admin:community_{name}_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:community_thread_change", args=[self.thread.pk])).status_code, 200)


# ---------- Hidden authors, deletion, export, counters ----------

class HiddenAuthorTests(CommunityTestCase):
    """Дописи прихованих авторів."""
    def test_banned_and_suspended_authors_are_hidden(self):
        cat = old_user("cat")
        own = make_thread(cat, title="A thread by a person who gets banned")
        top = services.create_reply(cat, self.thread, body="Banned words at the top.")
        services.create_reply(self.bob, self.thread, parent=top, body="An answer under it.")
        services.create_reply(cat, self.thread, body="A banned leaf.")
        self.ban(cat)
        self.assertEqual(self.client.get(own.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("community:home")), "A thread by a person who gets banned")
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertNotIn("Banned words", html)
        self.assertNotIn("A banned leaf.", html)
        self.assertIn("[removed]", html)
        self.assertIn("An answer under it.", html)
        self.assertEqual(self.login(self.mira).get(own.get_absolute_url()).status_code, 200)  # moderators still can
        self.assertEqual(self.login(self.bob).post(reverse("community:reply", args=[own.pk]), {"body": "Hi"}).status_code, 404)
        self.assertEqual(self.vote(self.bob, top, json=True).status_code, 404)

        User.objects.filter(pk=self.ann.pk).update(is_suspended=True)
        self.assertEqual(self.client.get(self.thread.get_absolute_url()).status_code, 404)

    def test_recount_repairs_counters_and_drops_hidden_voters(self):
        cat = old_user("cat")
        reply = services.create_reply(self.bob, self.thread, body="An answer.")
        services.create_reply(self.bob, self.thread, body="A deleted one.")
        services.delete_reply(Reply.objects.get(body="A deleted one."))
        for voter in (self.bob, self.mira, cat):
            services.set_vote(voter, self.thread, True)
        services.set_vote(cat, reply, True)
        self.ban(cat)
        Thread.objects.filter(pk=self.thread.pk).update(score=99, reply_count=99)
        Reply.objects.filter(pk=reply.pk).update(score=42)
        out = StringIO()
        call_command("community_daily", stdout=out)
        self.thread.refresh_from_db()
        reply.refresh_from_db()
        self.assertEqual((self.thread.score, self.thread.reply_count, reply.score), (2, 1, 0))
        self.assertIn("Recounted", out.getvalue())


class AccountTests(CommunityTestCase):
    """Видалення й експорт акаунта зі спільнотою."""
    def test_account_deletion(self):
        lonely = services.create_thread(self.ann, self.board, "A thread only Ann wrote in", "Text.", [_clean()])
        services.create_reply(self.ann, lonely, body="Talking to myself.")
        answered = self.thread
        bobs = services.create_reply(self.bob, answered, body="Bob's answer.")
        anns = services.create_reply(self.ann, answered, parent=bobs, body="Ann's thanks.", images=[_clean()])
        elsewhere = make_thread(self.bob, title="A thread by Bob somewhere")
        leaf = services.create_reply(self.ann, elsewhere, body="Ann's leaf reply.")
        services.set_vote(self.ann, elsewhere, True)
        services.set_vote(self.ann, bobs, True)
        images = [lonely.images.get(), anns.images.get()]

        with self.captureOnCommitCallbacks(execute=True):
            entry = delete_account(self.ann)

        self.assertFalse(Thread.objects.filter(pk=lonely.pk).exists())
        answered.refresh_from_db()
        anns.refresh_from_db()
        leaf.refresh_from_db()
        elsewhere.refresh_from_db()
        bobs.refresh_from_db()
        self.assertEqual((answered.author, answered.body), (None, "I added the TXT record."))
        self.assertEqual((anns.author, anns.body, leaf.author, leaf.body), (None, "Ann's thanks.", None, "Ann's leaf reply."))
        self.assertEqual([stored(i) for i in images], [(False, False), (False, False)])
        self.assertEqual(CommunityImage.objects.count(), 0)
        self.assertEqual((Vote.objects.count(), elsewhere.score, bobs.score), (0, 0, 0))
        self.assertEqual(entry.metadata["community_threads_deleted"], 1)
        self.assertEqual(entry.metadata["community_threads_anonymized"], 1)
        self.assertEqual(entry.metadata["community_replies_anonymized"], 2)
        self.assertEqual(entry.metadata["community_images_deleted"], 2)

        response = self.client.get(answered.get_absolute_url())
        self.assertContains(response, "[deleted]")
        self.assertContains(response, "s thanks.")
        self.assertNotContains(response, "/u/ann/")
        self.assertNotContains(response, "@ann")
        self.assertContains(self.client.get(reverse("community:home")), "How do I verify a domain?")
        # Moderators can still remove a post of a deleted account; there is nobody to mute or ban.
        self.assertEqual(self.act(self.mira, anns, "mute", length=1, unit="days").status_code, 200)
        self.assertEqual(self.act(self.mira, anns, "remove_reply").status_code, 302)
        anns.refresh_from_db()
        self.assertEqual(anns.status, "removed")

    def test_deletion_works_while_the_flag_is_off(self):
        services.create_reply(self.bob, self.thread, body="Bob's answer.")
        with override_settings(COMMUNITY_ENABLED=False):
            delete_account(self.ann)
        self.thread.refresh_from_db()
        self.assertIsNone(self.thread.author)

    def test_export_has_community_content(self):
        reply = services.create_reply(self.ann, self.thread, body="My reply.", images=[_clean()])
        Reply.objects.filter(pk=reply.pk).update(sticker_key="thumbs-up")
        other = make_thread(self.bob, title="A thread by Bob somewhere")
        services.set_vote(self.ann, other, True)
        services.create_reply(self.bob, self.thread, body="Bob's private business.")
        decisions.remove_reply(reply, self.mira, REASON)
        data = build_export(self.ann)["community"]
        self.assertEqual([t["title"] for t in data["threads"]], ["How do I verify a domain?"])
        self.assertEqual([(r["text"], r["sticker"], r["status"], r["removed_reason"]) for r in data["replies"]],
                         [("My reply.", "thumbs-up", "removed", REASON)])
        self.assertEqual([v["url"] for v in data["upvotes"]], [other.get_absolute_url()])
        self.assertNotIn("Bob's private business.", str(data))


# ---------- Stage 2a: reply notifications ----------

class NotificationTests(CommunityTestCase):
    """Сповіщення про відповіді."""
    def inbox(self, user):
        return self.login(user).get(reverse("community:notifications"))

    def fresh(self, user):
        return User.objects.get(pk=user.pk)

    def test_reply_to_a_thread_and_to_a_reply(self):
        self.reply(self.bob, body="Wait an hour for DNS.")
        bobs = Reply.objects.get(author=self.bob)
        note = ReplyNotification.objects.get()
        self.assertEqual((note.recipient, note.reply, note.kind, note.read_at), (self.ann, bobs, "thread", None))
        self.assertIsNotNone(self.fresh(self.ann).community_notified_at)

        self.reply(self.ann, parent=bobs.pk, body="Thanks, it worked.")
        note = ReplyNotification.objects.get(recipient=self.bob)
        self.assertEqual(note.kind, "reply")
        self.assertEqual(ReplyNotification.objects.filter(recipient=self.ann).count(), 1)  # not about her own reply

    def test_the_answered_person_hears_even_past_the_depth_limit(self):
        one = services.create_reply(self.bob, self.thread, body="One.")
        two = services.create_reply(self.mira, self.thread, parent=one, body="Two.")
        three = services.create_reply(self.bob, self.thread, parent=two, body="Three.")
        four = services.create_reply(self.ann, self.thread, parent=three, body="Four.")
        self.assertEqual(four.parent, two)  # attached one level up
        self.assertTrue(ReplyNotification.objects.filter(recipient=self.bob, reply=four, kind="reply").exists())
        self.assertFalse(ReplyNotification.objects.filter(recipient=self.mira, reply=four).exists())

    def test_no_notification_for_yourself_or_a_deleted_account(self):
        services.create_reply(self.ann, self.thread, body="Answering my own thread.")
        orphan = make_thread(None, title="A thread of a deleted account")
        services.create_reply(self.bob, orphan, body="Hello?")
        self.assertEqual(ReplyNotification.objects.count(), 0)
        self.assertIsNone(self.fresh(self.ann).community_notified_at)

    def test_inbox_shows_only_your_own(self):
        services.create_reply(self.bob, self.thread, body="For Ann only.")
        other = make_thread(self.mira, title="Mira asks something")
        services.create_reply(self.bob, other, body="For Mira only.")
        response = self.inbox(self.ann)
        self.assertContains(response, "For Ann only.")
        self.assertNotContains(response, "For Mira only.")
        self.assertNotContains(self.inbox(self.boss), "For Ann only.")  # not even a superuser sees someone else's

    def test_opening_the_inbox_marks_read_and_clears_the_mark(self):
        services.create_reply(self.bob, self.thread, body="An answer.")
        page = self.login(self.ann).get("/explore/")
        self.assertContains(page, "user-menu__dot")
        self.assertContains(page, reverse("community:notifications"))
        first = self.inbox(self.ann)
        self.assertContains(first, "notification--new")
        self.assertIsNone(self.fresh(self.ann).community_notified_at)
        self.assertIsNotNone(ReplyNotification.objects.get().read_at)
        self.assertNotContains(self.client.get("/explore/"), "user-menu__dot")
        self.assertNotContains(self.inbox(self.ann), "notification--new")

    def test_the_mark_costs_no_query(self):
        self.client.force_login(self.ann)
        with CaptureQueriesContext(connection) as before:
            self.client.get("/explore/")
        services.create_reply(self.bob, self.thread, body="An answer.")
        with CaptureQueriesContext(connection) as after:
            self.assertContains(self.client.get("/explore/"), "user-menu__dot")
        self.assertEqual(len(after), len(before))

    def test_hidden_replies_drop_out_of_the_inbox(self):
        removed = services.create_reply(self.bob, self.thread, body="Removed by moderators.")
        deleted = services.create_reply(self.mira, self.thread, body="Deleted by the author.")
        cat = old_user("cat")
        services.create_reply(cat, self.thread, body="Written by a banned person.")
        services.create_reply(self.boss, self.thread, body="Still visible.")
        decisions.remove_reply(removed, self.mira, REASON)
        services.delete_reply(deleted)
        self.ban(cat)
        response = self.inbox(self.ann)
        self.assertContains(response, "Still visible.")
        for text in ("Removed by moderators.", "Deleted by the author.", "Written by a banned person."):
            self.assertNotContains(response, text)

    def test_a_reply_by_a_deleted_account_stays_anonymous(self):
        services.create_reply(self.bob, self.thread, body="Bob says hi.")
        delete_account(self.bob)
        response = self.inbox(self.ann)
        self.assertContains(response, "A deleted account replied to your thread")
        self.assertNotContains(response, "@bob")

    def test_recipient_deletion_takes_the_notifications(self):
        services.create_reply(self.bob, self.thread, body="An answer.")
        delete_account(self.ann)
        self.assertEqual(ReplyNotification.objects.count(), 0)

    def test_muted_people_still_read_their_inbox(self):
        services.create_reply(self.bob, self.thread, body="An answer.")
        self.ban(self.ann, Sanction.Kind.MUTE)
        self.assertContains(self.inbox(self.ann), "An answer.")

    def test_anonymous_and_flag_off(self):
        response = self.client.get(reverse("community:notifications"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
        self.client.force_login(self.ann)
        with override_settings(COMMUNITY_ENABLED=False):
            User.objects.filter(pk=self.ann.pk).update(community_notified_at=timezone.now())
            self.assertEqual(self.client.get(reverse("community:notifications")).status_code, 404)
            page = self.client.get("/explore/")
            self.assertNotContains(page, "user-menu__dot")
            self.assertNotContains(page, "/community/")
        self.assertEqual(self.client.post(reverse("community:notifications")).status_code, 405)  # GET only

    def test_inbox_pages_and_constant_queries(self):
        def count():
            with CaptureQueriesContext(connection) as queries:
                self.assertEqual(self.client.get(reverse("community:notifications")).status_code, 200)
            return len(queries)

        self.client.force_login(self.ann)
        self.client.get(reverse("community:notifications"))  # warm up (first request of the session)
        services.create_reply(self.bob, self.thread, body="First.")
        self.ann.refresh_from_db()
        few = count()  # one unread
        for n in range(limits.NOTIFICATIONS_PER_PAGE + 3):
            services.create_reply(old_user(f"user{n}"), self.thread, body=f"Answer number {n}.")
        self.assertEqual(count(), few)  # many unread, same number of queries
        response = self.client.get(reverse("community:notifications"))
        self.assertEqual(len(response.context["items"]), limits.NOTIFICATIONS_PER_PAGE)
        self.assertTrue(response.context["has_next"])
        self.assertEqual(len(self.client.get(reverse("community:notifications"), {"page": 2}).context["items"]), 4)

    def test_daily_command_prunes_old_notifications(self):
        services.create_reply(self.bob, self.thread, body="Old.")
        services.create_reply(self.mira, self.thread, body="New.")
        ReplyNotification.objects.filter(reply__body="Old.").update(created_at=timezone.now() - timedelta(days=91))
        out = StringIO()
        call_command("community_daily", stdout=out)
        self.assertEqual(list(ReplyNotification.objects.values_list("reply__body", flat=True)), ["New."])
        self.assertIn("Deleted 1 old notifications", out.getvalue())

    def test_export_lists_notifications_without_the_other_persons_text(self):
        services.create_reply(self.bob, self.thread, body="Bob's private words.")
        data = build_export(self.ann)["community"]["notifications"]
        self.assertEqual([n["kind"] for n in data], ["thread"])
        self.assertNotIn("private words", str(data))
        self.assertNotIn("bob", str(data))


# ---------- Launch: retired stickers ----------

class RetiredStickerTests(CommunityTestCase):
    """Старі ключі читаються без стікерів, нові не приймаються."""
    def test_legacy_reply_renders_its_text_without_a_sticker(self):
        for key in ("thumbs-up", "retired", "../../evil", '<svg onload="alert(1)">'):
            with self.subTest(key=key):
                reply = services.create_reply(self.bob, self.thread, body="Legacy reply text.")
                Reply.objects.filter(pk=reply.pk).update(sticker_key=key)
                page = self.client.get(self.thread.get_absolute_url())
                self.assertContains(page, "Legacy reply text.")
                self.assertNotContains(page, "stickers/")
                self.assertNotContains(page, "data-picker")

    def test_service_refuses_all_nonempty_keys(self):
        for key in ("thumbs-up", "../../evil"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                services.create_reply(self.bob, self.thread, body="Text.", sticker_key=key)
        self.assertEqual(Reply.objects.count(), 0)

    def test_legacy_notification_uses_text_without_sticker_labels(self):
        reply = services.create_reply(self.bob, self.thread, body="A legacy notification.")
        Reply.objects.filter(pk=reply.pk).update(sticker_key="clap")
        page = self.login(self.ann).get(reverse("community:notifications"))
        self.assertContains(page, "A legacy notification.")
        self.assertNotContains(page, "Sticker:")

    def test_legacy_key_does_not_allow_an_empty_edit(self):
        reply = services.create_reply(self.bob, self.thread, body="Keep this text.")
        Reply.objects.filter(pk=reply.pk).update(sticker_key="clap")
        page = self.login(self.bob).post(reverse("community:reply_edit", args=[reply.pk]), {"body": ""})
        self.assertEqual(page.status_code, 400)
        reply.refresh_from_db()
        self.assertEqual(reply.body, "Keep this text.")

    @override_settings(DEBUG=True)
    def test_styleguide_has_no_sticker_sheet(self):
        page = self.client.get("/styleguide/")
        self.assertNotContains(page, "stickers/")
        self.assertNotContains(page, 'id="stickers"')

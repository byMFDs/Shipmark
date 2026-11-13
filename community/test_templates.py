"""Template comments stay out of the HTML: Django's {# #} is one line only, so longer notes use {% comment %}."""
import re
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from moderation import sanctions
from moderation.models import Sanction
from pages.test_leaks import LeakAssertions

from . import services
from .models import Board, Reply, Thread
from .tests import REASON, CommunityTestCase, _clean, make_thread, old_user

PARTIALS = ["_composer", "_layout", "_media", "_reply", "_vote"]


def comment_snippets():
    """The opening words of every comment in the partials: none of them may reach a page."""
    snippets = []
    for name in PARTIALS:
        source = (Path(settings.BASE_DIR) / "templates" / "community" / f"{name}.html").read_text()
        for body in re.findall(r"\{% comment %\}(.*?)\{% endcomment %\}|\{#(.*?)#\}", source, re.S):
            text = " ".join("".join(body).split())
            if text:
                snippets.append(text[:30])
    return snippets


class StrayCommentTests(CommunityTestCase):
    def test_no_multi_line_hash_comments_left(self):
        for name in PARTIALS:
            source = (Path(settings.BASE_DIR) / "templates" / "community" / f"{name}.html").read_text()
            for body in re.findall(r"\{#(.*?)#\}", source, re.S):
                self.assertNotIn("\n", body, name)

    def test_pages_using_the_partials_show_no_comment_text(self):
        services.create_thread(self.bob, self.board, "Pictures", "See them.", [_clean(), _clean(name="b.png")])
        services.create_reply(self.ann, self.thread, body="With a picture.", images=[_clean()])
        services.create_reply(self.bob, self.thread, body="Thanks.")
        snippets = comment_snippets()
        self.assertGreaterEqual(len(snippets), len(PARTIALS))
        self.client.force_login(self.bob)
        for url in (reverse("community:home"), self.thread.get_absolute_url(), reverse("community:new"),
                    reverse("community:rules"), reverse("community:notifications")):
            html = self.client.get(url).content.decode()
            with self.subTest(url=url):
                self.assertNotIn("{#", html)
                self.assertNotIn("#}", html)
                for snippet in snippets:
                    self.assertNotIn(snippet, html)


class CommunityLeakTests(LeakAssertions, CommunityTestCase):
    """Every community page, for every role, prints no template internals (a view's `block` context
    variable once printed "<Block Node: community_main ...>" on /community/new/)."""

    def setUp(self):
        super().setUp()
        services.create_reply(self.bob, self.thread, body="Thanks.")
        self.locked = make_thread(self.ann, title="A locked thread", status=Thread.Status.LOCKED)
        self.empty_board = Board.objects.exclude(pk=self.board.pk).filter(is_active=True).first()
        self.muted = old_user("mute")
        sanctions.issue(self.muted, Sanction.Kind.MUTE, REASON, self.boss, length=timedelta(days=1))

    def urls(self):
        reply = self.thread.replies.first()
        urls = [
            reverse("community:home"), reverse("community:home") + "?sort=new",
            reverse("community:board", args=[self.board.slug]), self.thread.get_absolute_url(),
            self.locked.get_absolute_url(), reverse("community:new"), reverse("community:rules"),
            reverse("community:notifications"),
            reverse("community:thread_edit", args=[self.thread.pk]),
            reverse("community:thread_delete", args=[self.thread.pk]),
            reverse("community:reply_edit", args=[reply.pk]),
            reverse("community:reply_delete", args=[reply.pk]),
        ]
        if self.empty_board:
            urls.append(reverse("community:board", args=[self.empty_board.slug]))
        return urls

    def test_every_page_for_every_role(self):
        self.check_pages(self.urls(), [None, self.bob, self.ann, self.muted, self.mira, self.boss])

    def test_empty_states(self):
        Reply.objects.all().delete()
        Thread.objects.all().delete()
        self.check_pages([reverse("community:home"), reverse("community:notifications")], [None, self.bob])

    def test_write_block_notice_is_shown_as_text(self):
        """A muted member sees the reason on the new-thread page, not a node object."""
        html = self.login(self.muted).get(reverse("community:new")).content.decode()
        self.assertIn('class="notice"', html)
        self.assertNotIn("Node", html)

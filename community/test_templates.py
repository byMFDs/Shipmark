"""Template comments stay out of the HTML: Django's {# #} is one line only, so longer notes use {% comment %}."""
import re
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from . import services
from .tests import CommunityTestCase, _clean

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

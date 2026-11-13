"""No page may print template internals: node objects, raw tags or comments mean a template bug."""
import re
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts import badges
from accounts.models import User
from config import errors
from projects.models import BuildLogEntry
from projects.tests import make_project, make_user

# What leaks look like: a node repr ("<Block Node: ...", "<TextNode: ..."), a Django traceback or class
# path, or template syntax that was never parsed (a multi-line {# #}, a broken tag).
LEAK_MARKERS = ("<Block Node", "TextNode", "django.template", "{#", "{%", "{{")


def leak_in(html):
    """The first marker found in the page, or None."""
    return next((marker for marker in LEAK_MARKERS if marker in html), None)


class LeakAssertions:
    def assertNoLeak(self, response, label=""):
        html = response.content.decode()
        marker = leak_in(html)
        if marker:
            at = html.index(marker)
            self.fail(f"{label or response.request['PATH_INFO']}: {marker!r} in the page: {html[max(at - 80, 0):at + 120]!r}")

    def check_pages(self, urls, users):
        """Render every url for every user (None = anonymous), following redirects, and check each page."""
        for user in users:
            self.client.logout()
            if user is not None:
                self.client.force_login(user)
            for url in urls:
                with self.subTest(user=getattr(user, "username", "anonymous"), url=url):
                    response = self.client.get(url, follow=True)
                    self.assertLess(response.status_code, 500)
                    self.assertNoLeak(response, url)


class TemplateSourceTests(TestCase):
    def test_no_template_reads_a_variable_named_block(self):
        """Inside {% block %} Django sets `block` to the BlockNode (for block.super), so a view's own `block`
        variable is shadowed and the node is printed. Only `block.super` may be used."""
        pattern = re.compile(r"\{\{\s*block\s*(\||\}\})|\{%\s*(?:el)?if\s+(?:not\s+)?block\b(?!\.)")
        for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                with self.subTest(template=str(path.relative_to(settings.BASE_DIR)), line=number):
                    self.assertIsNone(pattern.search(line), line.strip())

    def test_no_multi_line_hash_comments(self):
        """{# #} is one line only; across lines Django prints it as text."""
        for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            for body in re.findall(r"\{#(.*?)#\}", path.read_text(), re.S):
                with self.subTest(template=str(path.relative_to(settings.BASE_DIR))):
                    self.assertNotIn("\n", body)


class MainPageLeakTests(LeakAssertions, TestCase):
    def setUp(self):
        cache.clear()
        self.owner = make_user("ann", display_name="Ann")
        self.project = make_project(self.owner)
        BuildLogEntry.objects.create(project=self.project, text="Shipped the first version.")
        self.user = make_user("bob")
        self.moderator = make_user("mira")
        badges.grant(self.moderator, "moderator")
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")

    def test_main_pages(self):
        urls = [
            reverse("pages:landing"), reverse("social:feed"), reverse("social:feed") + "?tab=following",
            reverse("social:feed") + "?tab=news", reverse("pages:explore"), reverse("pages:explore") + "?q=tally",
            reverse("accounts:profile", args=["ann"]), self.project.get_absolute_url(),
            reverse("projects:new"), reverse("accounts:settings"), reverse("support:form"),
            reverse("news:list"), reverse("pages:about"), reverse("pages:how_proof_works"),
            *(reverse("pages:legal", args=[slug]) for slug in ("privacy", "terms", "cookies")),
            "/this-page-does-not-exist/",
        ]
        self.check_pages(urls, [None, self.user, self.moderator, self.boss])

    def test_owner_pages(self):
        self.check_pages([reverse("projects:edit", args=["ann", self.project.slug])], [self.owner, self.boss])

    def test_error_pages(self):
        request = RequestFactory().get("/")
        request.user = self.user
        for name, view in (("400", errors.bad_request), ("403", errors.permission_denied),
                           ("404", errors.page_not_found), ("500", errors.server_error)):
            with self.subTest(code=name):
                args = (request,) if name == "500" else (request, None)
                self.assertNoLeak(view(*args), name)

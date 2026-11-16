"""SEO: sitemap.xml, robots.txt, canonical, noindex, JSON-LD і мета-теги."""
import json
import re
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.system import system_user
from community.models import Board
from community.tests import make_thread
from moderation.models import Sanction
from news.models import NewsPost
from projects.models import Project
from projects.tests import make_project, make_user

SITE = "https://shipmark.org"


def locs(response):
    """Усі <loc> з sitemap.xml."""
    return re.findall(r"<loc>([^<]+)</loc>", response.content.decode())


@override_settings(SITE_URL=SITE)
class SitemapTests(TestCase):
    """Що потрапляє в sitemap.xml, а що ні."""
    def setUp(self):
        self.ana = make_user("ana")
        self.shown = make_project(self.ana, name="Shown")
        self.draft = make_project(self.ana, name="Hidden draft", status=Project.Status.DRAFT)
        self.hidden = make_project(self.ana, name="Hidden by admin", status=Project.Status.HIDDEN)
        self.removed = make_project(self.ana, name="Removed one", status=Project.Status.REMOVED)

    def urls(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"].split(";")[0], "application/xml")
        return locs(response)

    def test_static_pages_projects_and_profiles_are_listed_with_the_canonical_host(self):
        urls = self.urls()
        for path in ("/", "/about/", "/how-proof-works/", "/legal/privacy/", "/legal/terms/", "/legal/cookies/",
                     self.shown.get_absolute_url(), "/u/ana/"):
            with self.subTest(path=path):
                self.assertIn(SITE + path, urls)
        self.assertTrue(all(url.startswith(SITE + "/") for url in urls), urls)

    def test_only_published_projects(self):
        urls = self.urls()
        for project in (self.draft, self.hidden, self.removed):
            with self.subTest(project=project.name):
                self.assertNotIn(SITE + project.get_absolute_url(), urls)

    def test_lastmod_is_present_for_projects_profiles_and_news(self):
        NewsPost.objects.create(title="Launch", slug="launch", body="Body", published_at=timezone.now())
        body = self.client.get("/sitemap.xml").content.decode()
        for path in (self.shown.get_absolute_url(), "/u/ana/", "/news/launch/"):
            with self.subTest(path=path):
                self.assertRegex(body, re.escape(f"<loc>{SITE}{path}</loc>") + r"\s*<lastmod>\d{4}-\d{2}-\d{2}")

    def test_suspended_banned_inactive_demo_and_system_accounts_are_left_out(self):
        suspended = make_user("sue", is_suspended=True)
        banned = make_user("ben")
        Sanction.objects.create(user=banned, kind="ban", reason="x")
        inactive = make_user("ian", is_active=False)
        demo = make_user("demo-iryna", email="demo-iryna@example.invalid")
        system = system_user()
        left_out = [make_project(owner, name="Mine") for owner in (suspended, banned, inactive, demo, system)]
        urls = self.urls()
        for project in left_out:
            with self.subTest(owner=project.owner.username):
                self.assertNotIn(SITE + project.get_absolute_url(), urls)
                self.assertNotIn(SITE + f"/u/{project.owner.username}/", urls)

    def test_profile_without_a_published_project_is_not_listed(self):
        make_user("empty")
        make_project(make_user("onlydraft"), status=Project.Status.DRAFT)
        urls = self.urls()
        self.assertNotIn(SITE + "/u/empty/", urls)
        self.assertNotIn(SITE + "/u/onlydraft/", urls)

    def test_news_published_only_and_news_index_appears_with_the_first_post(self):
        self.assertNotIn(SITE + "/news/", self.urls())
        now = timezone.now()
        NewsPost.objects.create(title="Out", slug="out", body="Body", published_at=now)
        NewsPost.objects.create(title="Draft", slug="draft", body="Body")
        NewsPost.objects.create(title="Later", slug="later", body="Body", published_at=now + timedelta(days=2))
        urls = self.urls()
        self.assertIn(SITE + "/news/", urls)
        self.assertIn(SITE + "/news/out/", urls)
        self.assertNotIn(SITE + "/news/draft/", urls)
        self.assertNotIn(SITE + "/news/later/", urls)

    def test_community_threads_only_when_the_flag_is_on(self):
        board = Board.objects.first()
        thread = make_thread(self.ana, board=board)
        removed = make_thread(self.ana, title="Removed thread", board=board, status="removed")
        demo = make_thread(make_user("demo-leo", email="demo-leo@example.invalid"), title="Demo thread", board=board)
        with override_settings(COMMUNITY_ENABLED=False):
            self.assertFalse([u for u in self.urls() if "/community/" in u])
        with override_settings(COMMUNITY_ENABLED=True):
            urls = self.urls()
            self.assertIn(SITE + thread.get_absolute_url(), urls)
            self.assertNotIn(SITE + removed.get_absolute_url(), urls)
            self.assertNotIn(SITE + demo.get_absolute_url(), urls)

    def test_never_lists_private_or_utility_pages(self):
        urls = self.urls()
        for fragment in ("/settings", "/login", "/signup", "/support", "/mod/", "/new/", "/explore", "/feed", "/edit"):
            with self.subTest(fragment=fragment):
                self.assertFalse([u for u in urls if fragment in u], urls)


@override_settings(SITE_URL=SITE)
class RobotsTests(TestCase):
    """robots.txt: публічне дозволено, службове ні, посилання на sitemap."""
    def test_rules_and_sitemap_line(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        text = response.content.decode()
        self.assertIn("User-agent: *", text)
        self.assertIn("Allow: /\n", text)
        self.assertNotIn("Disallow: /\n", text)  # not the whole site
        for path in ("/mod/", "/settings/", "/login/", "/signup/", "/support/sent/", "/admin/", "/_dev/", "/*?q=",
                     "/*?tab=people"):
            with self.subTest(path=path):
                self.assertIn(f"Disallow: {path}\n", text)
        self.assertIn(f"Sitemap: {SITE}/sitemap.xml", text)

    @override_settings(ADMIN_URL="secret-door/")
    def test_the_real_admin_path_is_not_published_in_robots_txt(self):
        self.assertNotIn("secret-door", self.client.get("/robots.txt").content.decode())

    def test_public_pages_are_not_disallowed(self):
        text = self.client.get("/robots.txt").content.decode()
        for path in ("/", "/explore/", "/news/", "/u/ana/", "/about/", "/how-proof-works/", "/legal/privacy/"):
            with self.subTest(path=path):
                rules = [line[len("Disallow: "):] for line in text.splitlines() if line.startswith("Disallow: ")]
                self.assertFalse([r for r in rules if r.rstrip("*") and not r.startswith("/*") and path.startswith(r)], rules)


@override_settings(SITE_URL=SITE)
class CanonicalAndMetaTests(TestCase):
    """Canonical, description, Open Graph і JSON-LD."""
    def setUp(self):
        self.ana = make_user("ana", headline="Building small tools")
        self.project = make_project(self.ana, name="Tallyhook")
        Project.objects.filter(pk=self.project.pk).update(tagline="Count things, calmly")

    def html(self, path):
        return self.client.get(path).content.decode()

    def test_canonical_uses_site_url_and_drops_the_query(self):
        self.assertIn(f'<link rel="canonical" href="{SITE}/">', self.html("/"))
        profile = self.html("/u/ana/?tab=about")
        self.assertIn(f'<link rel="canonical" href="{SITE}/u/ana/">', profile)
        self.assertEqual(profile.count('rel="canonical"'), 1)
        project = self.html(self.project.get_absolute_url())
        self.assertIn(f'<link rel="canonical" href="{SITE}{self.project.get_absolute_url()}">', project)
        self.assertEqual(project.count('rel="canonical"'), 1)

    def test_error_page_has_no_canonical_and_is_a_real_404(self):
        response = self.client.get("/u/nobody/")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('rel="canonical"', response.content.decode())
        self.assertIn('content="noindex"', response.content.decode())
        self.assertEqual(response["X-Robots-Tag"], "noindex")

    def test_one_description_per_page_and_it_differs_by_page_type(self):
        seen = {}
        for name, path in (("landing", "/"), ("project", self.project.get_absolute_url()), ("profile", "/u/ana/"),
                           ("about", "/about/"), ("proof", "/how-proof-works/"), ("privacy", "/legal/privacy/"),
                           ("terms", "/legal/terms/"), ("explore", "/explore/"), ("support", "/support/")):
            html = self.html(path)
            descriptions = re.findall(r'<meta name="description" content="([^"]*)"', html)
            with self.subTest(page=name):
                self.assertEqual(len(descriptions), 1, descriptions)
                self.assertTrue(descriptions[0].strip())
                self.assertLessEqual(len(descriptions[0]), 300)
            seen[name] = descriptions[0]
        self.assertEqual(seen["project"], "Count things, calmly")
        self.assertEqual(seen["profile"], "Building small tools")
        self.assertEqual(len(set(seen.values())), len(seen), seen)

    def test_titles_differ_by_page_type(self):
        titles = {re.search(r"<title>(.*?)</title>", self.html(path), re.S).group(1)
                  for path in ("/", "/about/", "/how-proof-works/", "/legal/privacy/", "/explore/", "/u/ana/",
                               self.project.get_absolute_url())}
        self.assertEqual(len(titles), 7, titles)

    def test_descriptions_are_translated(self):
        for lang in ("uk", "pl", "de", "es", "fr", "pt-br"):
            with self.subTest(lang=lang):
                response = self.client.get("/legal/privacy/", headers={"Accept-Language": lang})
                self.assertContains(response, f'<html lang="{lang}"')
                english = re.search(r'name="description" content="([^"]*)"', self.html("/legal/privacy/")).group(1)
                local = re.search(r'name="description" content="([^"]*)"', response.content.decode()).group(1)
                self.assertNotEqual(local, english)

    def test_open_graph_and_twitter_tags_use_the_canonical_host(self):
        html = self.html(self.project.get_absolute_url())
        self.assertIn(f'<meta property="og:url" content="{SITE}{self.project.get_absolute_url()}">', html)
        self.assertRegex(html, r'<meta property="og:image" content="https://shipmark\.org/static/brand/og-default\.png\?v=')
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
        self.assertIn('<meta property="og:title" content="Tallyhook', html)

    def test_profile_og_image_is_the_avatar_when_the_url_is_stable(self):
        from django.core.files.base import ContentFile
        self.ana.avatar.save("a.webp", ContentFile(b"x"), save=True)
        html = self.html("/u/ana/")
        self.assertIn(f'<meta property="og:image" content="{SITE}{self.ana.avatar.url}">', html)

    def test_signed_media_url_falls_back_to_the_default_image(self):
        from django.core.files.base import ContentFile
        from pages.templatetags.ui import og_media_url
        self.ana.avatar.save("a.webp", ContentFile(b"x"), save=True)

        class Signed:
            url = "https://bucket.example/media/avatars/a.webp?X-Amz-Signature=abc"

            def __bool__(self):
                return True
        self.assertEqual(og_media_url(Signed()), "")
        self.assertEqual(og_media_url(None), "")

    def ld(self, html):
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        return [json.loads(b) for b in blocks]

    def test_home_has_organization_and_website_and_nothing_else(self):
        (data,) = self.ld(self.html("/"))
        kinds = {item["@type"]: item for item in data["@graph"]}
        self.assertEqual(set(kinds), {"Organization", "WebSite"})
        self.assertEqual(kinds["Organization"]["url"], SITE + "/")
        self.assertEqual(kinds["Organization"]["name"], "Shipmark")
        self.assertTrue(kinds["Organization"]["logo"].startswith(SITE + "/static/brand/"))
        self.assertNotIn("sameAs", kinds["Organization"])  # empty social links: the key is left out
        self.assertEqual(kinds["WebSite"], {"@type": "WebSite", "name": "Shipmark", "url": SITE + "/"})

    def test_same_as_appears_only_with_real_links(self):
        from config import branding
        from pages import seo
        with self.settings():
            original = branding.SOCIAL_LINKS
            try:
                branding.SOCIAL_LINKS = {"github": "https://github.com/shipmark", "bad": "javascript:alert(1)"}
                self.assertEqual(seo.organization_ld()["sameAs"], ["https://github.com/shipmark"])
            finally:
                branding.SOCIAL_LINKS = original

    def test_breadcrumbs_on_project_and_profile(self):
        (project_ld,) = self.ld(self.html(self.project.get_absolute_url()))
        names = [(i["position"], i["name"], i["item"]) for i in project_ld["itemListElement"]]
        self.assertEqual(names, [(1, "Shipmark", SITE + "/"), (2, "ana", SITE + "/u/ana/"),
                                 (3, "Tallyhook", SITE + self.project.get_absolute_url())])
        (profile_ld,) = self.ld(self.html("/u/ana/"))
        self.assertEqual([i["name"] for i in profile_ld["itemListElement"]], ["Shipmark", "ana"])

    def test_json_ld_cannot_close_the_script_tag(self):
        from pages.seo import json_ld
        text = json_ld({"name": "</script><script>alert(1)</script>"})
        self.assertNotIn("</script>", text)
        self.assertEqual(json.loads(text)["name"], "</script><script>alert(1)</script>")

    def test_draft_project_page_is_noindex_without_breadcrumbs_or_canonical(self):
        self.client.force_login(self.ana)
        draft = make_project(self.ana, name="Secret", status=Project.Status.DRAFT)
        html = self.html(draft.get_absolute_url())
        self.assertIn('content="noindex"', html)
        self.assertEqual(self.ld(html), [])


class NoindexTests(TestCase):
    """Приватні, службові й тонкі сторінки не індексуються: meta і заголовок."""
    def setUp(self):
        self.ana = make_user("ana")

    def test_private_and_utility_pages_say_noindex(self):
        self.client.force_login(self.ana)
        for path in ("/settings/", "/settings/delete/", "/new/", "/logout/", "/support/sent/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response["X-Robots-Tag"], "noindex")
                if response.status_code == 200:
                    self.assertIn('name="robots" content="noindex"', response.content.decode())
        self.client.logout()
        for path in ("/login/", "/login/cancelled/", "/login/error/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response["X-Robots-Tag"], "noindex")
                self.assertIn('name="robots" content="noindex"', response.content.decode())

    def test_search_results_and_empty_states_are_noindex(self):
        explore = self.client.get("/explore/").content.decode()
        self.assertIn('name="robots" content="noindex, follow"', explore)  # no projects yet: thin
        make_project(self.ana)
        self.assertNotIn('name="robots"', self.client.get("/explore/").content.decode())
        for path in ("/explore/?q=tally", "/explore/?tab=people&q=an", "/explore/?tag=x"):
            with self.subTest(path=path):
                self.assertIn('name="robots" content="noindex, follow"', self.client.get(path).content.decode())

    def test_profile_without_projects_is_noindex_and_with_projects_is_not(self):
        self.assertIn('name="robots" content="noindex, follow"', self.client.get("/u/ana/").content.decode())
        make_project(self.ana)
        self.assertNotIn('name="robots"', self.client.get("/u/ana/").content.decode())

    def test_every_error_response_has_the_header(self):
        for path in ("/u/nobody/", "/no/such/page/", "/news/nope/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response["X-Robots-Tag"], "noindex")

    @override_settings(ADMIN_URL="secret-door/")
    def test_admin_and_moderation_urls_get_the_header(self):
        from config.robots import noindex_header_applies
        from django.http import HttpResponse
        from django.test import RequestFactory
        for path in ("/secret-door/login/", "/mod/", "/settings/"):
            with self.subTest(path=path):
                self.assertTrue(noindex_header_applies(RequestFactory().get(path), HttpResponse()))
        self.assertFalse(noindex_header_applies(RequestFactory().get("/u/ana/"), HttpResponse()))

    def test_public_pages_have_no_noindex_header(self):
        make_project(self.ana)
        for path in ("/", "/about/", "/u/ana/", "/robots.txt"):
            with self.subTest(path=path):
                self.assertNotIn("X-Robots-Tag", self.client.get(path))
        # Django marks the sitemap file itself noindex (the file stays out of search results; its links still count)
        self.assertIn("noindex", self.client.get("/sitemap.xml")["X-Robots-Tag"])


class IconPathTests(TestCase):
    """Іконки за адресами, які запитують пошукові системи."""
    def test_icons_answer_at_the_standard_paths(self):
        for path, target in (("/favicon.ico", "/static/brand/favicon.ico"),
                             ("/apple-touch-icon.png", "/static/brand/apple-touch-icon.png"),
                             ("/apple-touch-icon-precomposed.png", "/static/brand/apple-touch-icon.png")):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response["Location"], target)
                self.assertEqual(self.client.get(target).status_code, 200)

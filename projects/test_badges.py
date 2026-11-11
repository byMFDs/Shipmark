import xml.etree.ElementTree as ET

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from verification.models import RepoLink

from . import badges
from .models import Project
from .tests import make_project, make_user

SVG_NS = "{http://www.w3.org/2000/svg}"


def parse(response):
    return ET.fromstring(response.content)  # raises if the SVG is not well-formed XML


class BadgeResponseTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.project = make_project(self.ana, name="Tallyhook", repo_full_name="ana/tallyhook")
        RepoLink.objects.create(project=self.project, repo_full_name="ana/tallyhook", github_repo_id=1,
                                is_owner=True, checked_at=timezone.now())

    def url(self, project=None):
        project = project or self.project
        return reverse("projects:badge_project", args=[project.owner.username, project.slug])

    def test_project_badge_headers_and_content(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertIn("max-age=3600", response["Cache-Control"])
        self.assertIn("public", response["Cache-Control"])
        root = parse(response)
        self.assertEqual(root.tag, SVG_NS + "svg")
        self.assertIn("Tallyhook", root.get("aria-label"))
        self.assertIn("Repo owner", root.get("aria-label"))

    def test_no_cookies_even_for_a_signed_in_visitor(self):
        self.client.force_login(self.ana)
        for url in (self.url(), reverse("projects:badge_profile", args=["ana"]),
                    reverse("projects:badge_project", args=["nobody", "nothing"])):
            response = self.client.get(url)
            self.assertNotIn("Set-Cookie", response.headers, url)
            self.assertEqual(len(response.cookies), 0, url)
            vary = response.headers.get("Vary", "")
            self.assertNotIn("Cookie", vary, url)
            self.assertNotIn("Accept-Language", vary, url)

    def test_hidden_draft_and_unknown_give_the_same_neutral_badge(self):
        hidden = make_project(self.ana, name="Hidden one", status=Project.Status.HIDDEN)
        draft = make_project(self.ana, name="Draft one", status=Project.Status.DRAFT)
        unknown = self.client.get(reverse("projects:badge_project", args=["ana", "nothing-here"]))
        self.assertEqual(unknown.status_code, 200)
        self.assertIn("not found", unknown.content.decode())
        for project in (hidden, draft):
            response = self.client.get(self.url(project))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, unknown.content)  # nothing tells the cases apart
            self.assertNotIn(project.name, response.content.decode())

    def test_suspended_owner_gives_neutral_badge(self):
        self.ana.is_suspended = True
        self.ana.save()
        self.assertIn("not found", self.client.get(self.url()).content.decode())
        self.assertIn("not found", self.client.get(reverse("projects:badge_profile", args=["ana"])).content.decode())

    def test_username_is_case_insensitive(self):
        url = reverse("projects:badge_project", args=["ANA", self.project.slug])
        self.assertNotIn("not found", self.client.get(url).content.decode())

    def test_profile_badge_counts_hallmarks_of_published_projects_only(self):
        make_project(self.ana, name="Secret", status=Project.Status.DRAFT, repo_full_name="ana/secret")
        response = self.client.get(reverse("projects:badge_profile", args=["ana"]))
        self.assertEqual(response["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertIn("1 hallmark", response.content.decode())
        self.assertNotIn("1 hallmarks", response.content.decode())
        parse(response)

    def test_unknown_profile_is_neutral(self):
        response = self.client.get(reverse("projects:badge_profile", args=["ghost"]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("not found", response.content.decode())

    def test_post_is_not_allowed(self):
        self.assertEqual(self.client.post(self.url()).status_code, 405)


class BadgeSvgTests(TestCase):
    def test_hostile_names_stay_valid_xml(self):
        for name in ('<script>alert(1)</script>', 'a & b "quoted" \'x\'', "ctrl\x00\x08char", "rtl‮evil", "]]> <![CDATA["):
            root = ET.fromstring(badges.project_badge(name, {"live"}))
            self.assertEqual(root.tag, SVG_NS + "svg")
            self.assertNotIn("<script", badges.project_badge(name, set()))

    def test_long_names_are_cut(self):
        svg = badges.project_badge("W" * 200, set())
        self.assertIn("…", svg)
        self.assertLess(float(ET.fromstring(svg).get("width")), 400)

    def test_cyrillic_and_empty_names(self):
        ET.fromstring(badges.project_badge("Тестовий проєкт", {"authored", "live", "steady"}))
        self.assertIn("Project", badges.project_badge("\x00", set()))

    def test_no_external_resources(self):
        svg = badges.project_badge("X", {"authored", "live", "steady"})
        self.assertEqual(svg.count("http"), 1)  # only the xmlns namespace
        for forbidden in ("<image", "@import", "<script", "<foreignObject"):
            self.assertNotIn(forbidden, svg)
        self.assertIn("font-family", svg)


class EmbedPanelTests(TestCase):
    def setUp(self):
        self.ana = make_user("ana")
        self.project = make_project(self.ana, name="Tally [one]")

    def test_owner_sees_snippets_on_project_and_profile(self):
        self.client.force_login(self.ana)
        page = self.client.get(self.project.get_absolute_url())
        self.assertContains(page, "Embed badge")
        self.assertContains(page, "http://testserver/badge/ana/%s.svg" % self.project.slug)
        self.assertEqual(page.context["embed"]["markdown"].count("["), 2)  # only the link and image openers: brackets in the name are dropped
        profile = self.client.get(reverse("accounts:profile", args=["ana"]))
        self.assertContains(profile, "http://testserver/badge/ana.svg")

    def test_others_and_drafts_get_no_panel(self):
        other = make_user("bob")
        self.client.force_login(other)
        self.assertNotContains(self.client.get(self.project.get_absolute_url()), "Embed badge")
        self.assertNotContains(self.client.get(reverse("accounts:profile", args=["ana"])), "Embed badge")
        self.client.force_login(self.ana)
        draft = make_project(self.ana, name="Draft", status=Project.Status.DRAFT)
        self.assertNotContains(self.client.get(draft.get_absolute_url()), "Embed badge")

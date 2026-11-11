"""Landing, explore (search, filters, sorts, hallmark rules), Open Graph tags."""
from datetime import timedelta

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from projects.models import Project, Tag, Tool
from projects.tests import TEMP_MEDIA, make_project, make_shot, make_user
from social.models import Like
from verification.domain import verification_for
from verification.models import DomainVerification, RepoLink, UptimeCheck

from .explore import PAGE_SIZE

EXPLORE = reverse("pages:explore")


class Facts:
    """Helpers that create the facts behind each hallmark."""

    def make_authored(self, project, **extra):
        values = {"repo_full_name": project.repo_full_name, "github_repo_id": project.pk,
                  "checked_at": timezone.now(), "is_owner": True}
        return RepoLink.objects.create(project=project, **{**values, **extra})

    def make_live(self, project, days_ago=0):
        row = verification_for(project, create=True)
        when = timezone.now() - timedelta(days=days_ago)
        row.status, row.verified_at, row.last_confirmed_at = DomainVerification.Status.VERIFIED, when, when
        row.save()

    def make_steady(self, project):
        now = timezone.now()
        UptimeCheck.objects.bulk_create(
            UptimeCheck(project=project, checked_at=now - timedelta(hours=3 * i + 1), ok=True) for i in range(40)
        )

    def names(self, response):
        return [p.name for p in response.context["projects"]]


class LandingTests(Facts, TestCase):
    def setUp(self):
        self.ann = make_user("ann")

    def test_signed_out_sees_hero_proof_and_sign_in(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Less claim.")
        self.assertContains(response, 'class="record specimen drift"')
        self.assertContains(response, "Illustrative project · real verification rules")  # the example says it is made up
        self.assertContains(response, "Sign in with GitHub")
        self.assertContains(response, "Submit your project")
        self.assertContains(response, "How proof works")

    def test_no_code_authorship_claims(self):
        """We check repository ownership, not who wrote the code (en and uk)."""
        for lang, words in (("en", ("Authored", "wrote the code")), ("uk", ("Авторство", "написа"))):
            response = self.client.get("/", headers={"accept-language": lang})
            self.assertContains(response, f'lang="{lang}"')
            for word in words:
                self.assertNotContains(response, word)

    def test_signed_in_goes_to_feed(self):
        self.client.force_login(self.ann)
        self.assertRedirects(self.client.get("/"), reverse("social:feed"), fetch_redirect_response=False)

    def test_recent_shows_only_visible_projects(self):
        make_project(self.ann, name="Shown")
        make_project(self.ann, name="Draft one", status=Project.Status.DRAFT)
        make_project(self.ann, name="Hidden one", status=Project.Status.HIDDEN)
        make_project(make_user("bad", is_suspended=True), name="Suspended one")
        response = self.client.get("/")
        self.assertEqual([p.name for p in response.context["recent"]], ["Shown"])
        self.assertNotContains(response, "Illustrative projects")  # never mixed with real ones

    def test_empty_strip_falls_back(self):
        self.assertContains(self.client.get("/"), "Illustrative projects")

    def test_query_count_does_not_grow_with_projects(self):
        make_project(self.ann, name="One")
        with CaptureQueriesContext(connection) as few:
            self.client.get("/")
        for i in range(5):
            make_project(self.ann, name=f"More {i}")
        with CaptureQueriesContext(connection) as many:
            self.client.get("/")
        self.assertEqual(len(few), len(many))


class ExploreFilterTests(Facts, TestCase):
    def setUp(self):
        self.ann = make_user("ann")
        self.webhooks = make_project(self.ann, name="Tallyhook")
        self.notes = make_project(self.ann, name="Quill")
        Project.objects.filter(pk=self.webhooks.pk).update(tagline="Replay webhooks without a tunnel")
        Project.objects.filter(pk=self.notes.pk).update(tagline="Notes for meetings")

    def test_lists_published_only(self):
        make_project(self.ann, name="Draft one", status=Project.Status.DRAFT)
        make_project(self.ann, name="Hidden one", status=Project.Status.HIDDEN)
        make_project(make_user("bad", is_suspended=True), name="Suspended one")
        response = self.client.get(EXPLORE)
        self.assertEqual(sorted(self.names(response)), ["Quill", "Tallyhook"])
        self.assertEqual(response.context["total"], 2)

    def test_search_name_and_tagline_ignoring_case(self):
        self.assertEqual(self.names(self.client.get(EXPLORE, {"q": "tally"})), ["Tallyhook"])
        self.assertEqual(self.names(self.client.get(EXPLORE, {"q": "WEBHOOKS"})), ["Tallyhook"])
        self.assertEqual(self.names(self.client.get(EXPLORE, {"q": "  for   meetings "})), ["Quill"])
        self.assertContains(self.client.get(EXPLORE, {"q": "nothing like this"}), "No published projects match")

    def test_tag_and_tool_filters(self):
        tag = Tag.objects.create(name="devtools", slug="devtools")
        tool = Tool.objects.first()
        self.webhooks.tags.add(tag)
        self.notes.built_with.add(tool)
        self.assertEqual(self.names(self.client.get(EXPLORE, {"tag": "devtools"})), ["Tallyhook"])
        self.assertEqual(self.names(self.client.get(EXPLORE, {"tool": tool.slug})), ["Quill"])
        self.assertEqual(self.names(self.client.get(EXPLORE, {"tag": "devtools", "tool": tool.slug})), [])
        self.assertIn(tag, self.client.get(EXPLORE).context["tags"])

    def test_invalid_values_are_ignored(self):
        response = self.client.get(EXPLORE, {"sort": "drop table", "hallmark": "used", "page": "x", "q": "a" * 500})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["params"]["sort"], "newest")
        self.assertEqual(response.context["params"]["hallmark"], "")

    def test_filters_stay_in_the_form(self):
        response = self.client.get(EXPLORE, {"q": "tally", "hallmark": "live", "sort": "liked"})
        self.assertContains(response, 'value="tally"')
        self.assertContains(response, '<option value="live" selected>')
        self.assertContains(response, '<option value="liked" selected>')
        self.assertContains(response, "Clear filters")


class ExploreHallmarkTests(Facts, TestCase):
    """The filter and the sort must agree with compute_hallmarks, including the edge cases."""

    def setUp(self):
        ann = make_user("ann")
        self.a = make_project(ann, name="Owned", repo_full_name="ann/owned")
        self.stale = make_project(ann, name="Stale", repo_full_name="ann/new-name")
        self.few = make_project(ann, name="Few commits", repo_full_name="bob/lib")
        self.live = make_project(ann, name="Live", live_url="https://live.example.com/")
        self.old = make_project(ann, name="Old live", live_url="https://old.example.com/")
        self.steady = make_project(ann, name="Steady", live_url="https://steady.example.com/",
                                   repo_full_name="ann/steady")
        make_project(ann, name="Nothing")
        self.make_authored(self.a)
        self.make_authored(self.stale, repo_full_name="ann/old-name")  # link left over from another repo
        self.make_authored(self.few, is_owner=False, user_commit_count=9)
        self.make_live(self.live)
        self.make_live(self.old, days_ago=40)  # not confirmed in 35 days
        self.make_authored(self.steady)
        self.make_live(self.steady)
        self.make_steady(self.steady)

    def test_authored_filter(self):
        self.assertEqual(sorted(self.names(self.client.get(EXPLORE, {"hallmark": "authored"}))), ["Owned", "Steady"])

    def test_live_filter(self):
        self.assertEqual(sorted(self.names(self.client.get(EXPLORE, {"hallmark": "live"}))), ["Live", "Steady"])

    def test_steady_filter(self):
        response = self.client.get(EXPLORE, {"hallmark": "steady"})
        self.assertEqual(self.names(response), ["Steady"])
        self.assertEqual(response.context["total"], 1)

    def test_most_proven_sort(self):
        names = self.names(self.client.get(EXPLORE, {"sort": "proven"}))
        self.assertEqual(names[0], "Steady")  # 3 marks
        self.assertEqual(set(names[1:3]), {"Owned", "Live"})  # 1 mark each, newest first
        self.assertEqual(names[1:3], ["Live", "Owned"])
        self.assertEqual(len(names), 7)

    def test_filter_with_search_and_sort(self):
        response = self.client.get(EXPLORE, {"hallmark": "live", "sort": "proven", "q": "live"})
        self.assertEqual(self.names(response), ["Live"])

    def test_query_count_does_not_grow_with_projects(self):
        def count():
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(EXPLORE, {"sort": "proven", "hallmark": "authored"})
            return len(ctx)
        before = count()
        owner = make_user("cat")
        for i in range(6):
            project = make_project(owner, name=f"Extra {i}", repo_full_name=f"cat/r{i}")
            self.make_authored(project, github_repo_id=1000 + i)
        self.assertEqual(count(), before)


class ExploreSortAndPagesTests(Facts, TestCase):
    def setUp(self):
        self.ann = make_user("ann")

    def test_newest_first(self):
        old = make_project(self.ann, name="Old")
        Project.objects.filter(pk=old.pk).update(launched_at=timezone.now() - timedelta(days=3))
        make_project(self.ann, name="New")
        self.assertEqual(self.names(self.client.get(EXPLORE)), ["New", "Old"])

    def test_most_liked(self):
        quiet = make_project(self.ann, name="Quiet")
        loved = make_project(self.ann, name="Loved")
        Project.objects.filter(pk=loved.pk).update(launched_at=timezone.now() - timedelta(days=3))
        for name in ("b", "c"):
            Like.objects.create(user=make_user(name), project=loved)
        Like.objects.create(user=make_user("gone", is_suspended=True), project=quiet)  # does not count
        self.assertEqual(self.names(self.client.get(EXPLORE, {"sort": "liked"})), ["Loved", "Quiet"])

    def test_pages_keep_the_filters(self):
        for i in range(PAGE_SIZE + 1):
            make_project(self.ann, name=f"Tool {i}")
        first = self.client.get(EXPLORE, {"q": "tool"})
        self.assertEqual(len(first.context["projects"]), PAGE_SIZE)
        self.assertContains(first, "?q=tool&amp;page=2")
        second = self.client.get(EXPLORE, {"q": "tool", "page": 2})
        self.assertEqual(len(second.context["projects"]), 1)
        self.assertContains(second, 'rel="prev"')
        self.assertEqual(self.client.get(EXPLORE, {"q": "tool", "page": 3}).status_code, 404)

    def test_proven_pages(self):
        for i in range(PAGE_SIZE + 2):
            make_project(self.ann, name=f"P {i}")
        second = self.client.get(EXPLORE, {"sort": "proven", "page": 2})
        self.assertEqual(len(second.context["projects"]), 2)
        self.assertFalse(second.context["has_next"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class OpenGraphTests(TestCase):
    def setUp(self):
        self.ann = make_user("ann", bio="I build small tools.")
        self.project = make_project(self.ann)

    def og(self, url, prop):
        html = self.client.get(url).content.decode()
        self.assertEqual(html.count(f'property="{prop}"'), 1, f"{url} {prop}")
        return html

    def test_every_public_page_has_one_set_of_tags(self):
        for url in ("/", EXPLORE, reverse("accounts:profile", args=["ann"]), self.project.get_absolute_url()):
            for prop in ("og:title", "og:description", "og:url", "og:type", "og:image"):
                self.og(url, prop)

    def test_project_uses_first_screenshot(self):
        shot = make_shot(self.project)
        make_shot(self.project, order=1)
        html = self.og(self.project.get_absolute_url(), "og:image")
        self.assertIn(f'<meta property="og:image" content="http://testserver{shot.image.url}">', html)
        self.assertIn(f'<meta property="og:image:width" content="{shot.width}">', html)

    def test_project_without_screenshot_uses_default(self):
        html = self.og(self.project.get_absolute_url(), "og:image")
        self.assertIn("brand/og-default.png", html)
        self.assertIn('<meta property="og:description" content="A tagline">', html)

    def test_profile_type_and_bio(self):
        html = self.og(reverse("accounts:profile", args=["ann"]), "og:type")
        self.assertIn('<meta property="og:type" content="profile">', html)
        self.assertIn('<meta property="og:description" content="I build small tools.">', html)

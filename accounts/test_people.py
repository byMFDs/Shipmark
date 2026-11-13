"""People search on Discover (/explore/?tab=people): ranking, limits, hidden accounts, follow rules, escaping,
privacy, rate limit and a fixed number of queries. Rules in accounts/people.py."""
import logging
from datetime import timedelta

from allauth.socialaccount.models import SocialAccount
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts import badges, people
from accounts.models import User
from accounts.system import SYSTEM_USERNAME
from moderation import sanctions
from moderation.models import Sanction
from projects.models import Project
from projects.tests import make_project, make_user
from social.models import Follow
from verification.models import RepoLink

URL = reverse("pages:explore")


def find(client, q, **extra):
    return client.get(URL, {"tab": "people", "q": q, **extra})


def names(response):
    return [p.username for p in response.context["results"]]


class PeopleSearchTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")


class RankingTests(PeopleSearchTestCase):
    def test_prefix_matches_come_first_then_contains_each_alphabetical(self):
        for name in ("joanna", "hannah", "annabel", "anna", "bob"):
            make_user(name)
        self.assertEqual(names(find(self.client, "ann")), ["anna", "annabel", "hannah", "joanna"])

    def test_case_and_a_leading_at_sign_do_not_matter(self):
        make_user("anna")
        self.assertEqual(names(find(self.client, "ANN")), ["anna"])
        self.assertEqual(names(find(self.client, " @Ann ")), ["anna"])

    def test_username_only_not_display_name_or_headline(self):
        make_user("zed", display_name="Anna Smith", headline="anna fan")
        self.assertEqual(names(find(self.client, "anna")), [])


class LimitTests(PeopleSearchTestCase):
    def test_minimum_length(self):
        make_user("ab")
        response = find(self.client, "a")
        self.assertEqual(response.context["problem"], "short")
        self.assertEqual(response.context["results"], [])
        self.assertContains(response, "Type at least 2 characters")
        self.assertEqual(names(find(self.client, "ab")), ["ab"])

    def test_an_empty_query_lists_nobody(self):
        for i in range(3):
            make_user(f"user{i}")
        for q in ("", "   ", "@"):
            with self.subTest(q=q):
                response = find(self.client, q)
                self.assertEqual(response.context["results"], [])
                self.assertContains(response, "Find someone by their username")

    def test_twenty_per_page_plain_link_pagination(self):
        for i in range(25):
            make_user(f"maker{i:02d}")
        first = find(self.client, "maker")
        self.assertEqual(len(names(first)), 20)
        self.assertTrue(first.context["has_next"])
        self.assertContains(first, 'rel="next"')
        second = find(self.client, "maker", page=2)
        self.assertEqual(names(second), [f"maker{i:02d}" for i in range(20, 25)])
        self.assertFalse(second.context["has_next"])
        self.assertEqual(find(self.client, "maker", page=3).status_code, 404)

    def test_a_bad_page_number_is_page_one(self):
        make_user("maker")
        self.assertEqual(names(find(self.client, "maker", page="x")), ["maker"])


class HiddenAccountTests(PeopleSearchTestCase):
    def test_hidden_accounts_never_appear(self):
        make_user("ann-visible")
        make_user("ann-suspended", is_suspended=True)
        make_user("ann-inactive", is_active=False)
        banned = make_user("ann-banned")
        sanctions.issue(banned, Sanction.Kind.BAN, "Spam in every post, again.", self.boss, length=timedelta(days=1))
        make_user("demo-ann", email="demo-ann@example.invalid")
        gone = make_user("ann-deleted")
        gone.delete()
        self.assertEqual(names(find(self.client, "ann")), ["ann-visible"])

    def test_a_muted_account_is_still_findable(self):
        muted = make_user("ann-muted")
        sanctions.issue(muted, Sanction.Kind.MUTE, "Rude replies to several people.", self.boss, length=timedelta(days=1))
        self.assertEqual(names(find(self.client, "ann")), ["ann-muted"])

    def test_the_system_account_is_not_listed(self):
        self.assertTrue(User.objects.filter(username=SYSTEM_USERNAME).exists())
        self.assertEqual(names(find(self.client, SYSTEM_USERNAME[:4])), [])

    def test_a_real_person_whose_name_starts_with_demo_is_listed(self):
        make_user("demo-day", email="me@real.test")
        self.assertEqual(names(find(self.client, "demo")), ["demo-day"])


class EscapingTests(PeopleSearchTestCase):
    def test_underscore_is_a_literal_not_a_wildcard(self):
        make_user("a_b")
        make_user("axb")
        self.assertEqual(names(find(self.client, "a_")), ["a_b"])

    def test_wildcards_and_regex_signs_match_nobody(self):
        make_user("anna")
        for q in ("%%", "a%", "an%a", "a*", ".*", "^a", "a|b", "[a]", "a b", "a\\", "an'a", "a\"b"):
            with self.subTest(q=q):
                response = find(self.client, q)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["results"], [])
                self.assertEqual(response.context["problem"], "chars")

    def test_too_long_matches_nobody(self):
        make_user("anna")
        self.assertEqual(find(self.client, "a" * 41).context["problem"], "chars")

    def test_the_query_is_escaped_in_the_page(self):
        response = find(self.client, "<script>x")
        self.assertNotContains(response, "<script>x")


class RowTests(PeopleSearchTestCase):
    def setUp(self):
        super().setUp()
        self.ann = make_user("ann", display_name="Ann Lee", headline="Builds small tools", email="ann.secret@example.com")
        SocialAccount.objects.create(user=self.ann, provider="github", uid="98765431", extra_data={"login": "ann-gh"})
        badges.grant(self.ann, "moderator")
        project = make_project(self.ann, repo_full_name="ann/tally")
        RepoLink.objects.create(project=project, repo_full_name="ann/tally", github_repo_id=1, is_owner=True,
                                checked_at=timezone.now())
        make_project(self.ann, name="Second")
        make_project(self.ann, name="Draft", status=Project.Status.DRAFT)
        self.bob = make_user("bob")

    def test_public_fields_and_counts(self):
        response = find(self.client, "ann")
        person = response.context["results"][0]
        self.assertEqual(person.project_count, 2)  # the draft does not count
        self.assertEqual(person.hallmark_count, 1)  # Repo owner on the first project
        html = response.content.decode()
        for text in ("Ann Lee", "@ann", "Builds small tools", "2 projects", 'data-badge="moderator"',
                     reverse("accounts:profile", args=["ann"])):
            self.assertIn(text, html)

    def test_hallmarks_are_counted_like_on_the_profile(self):
        from accounts.profile import profile_projects, profile_stats

        expected = profile_stats(self.ann, profile_projects(self.ann))["hallmarks"]
        self.assertEqual(find(self.client, "ann").context["results"][0].hallmark_count, expected)

    def test_never_email_or_github_id(self):
        html = find(self.client, "ann").content.decode()
        self.assertNotIn("ann.secret@example.com", html)
        self.assertNotIn("98765431", html)

    def test_anonymous_sees_sign_in_to_follow(self):
        html = find(self.client, "ann").content.decode()
        self.assertIn("Sign in to follow", html)
        self.assertNotIn(reverse("social:follow", args=["ann"]), html)

    def test_own_row_says_you(self):
        self.client.force_login(self.ann)
        response = find(self.client, "ann")
        self.assertContains(response, "person-row__you")
        self.assertNotContains(response, reverse("social:follow", args=["ann"]))

    def test_signed_in_gets_the_follow_form_and_its_state(self):
        self.client.force_login(self.bob)
        self.assertContains(find(self.client, "ann"), reverse("social:follow", args=["ann"]))
        Follow.objects.create(follower=self.bob, following=self.ann)
        response = find(self.client, "ann")
        self.assertTrue(response.context["results"][0].followed)
        self.assertContains(response, 'aria-pressed="true"')

    def test_following_from_the_results_goes_back_to_them(self):
        self.client.force_login(self.bob)
        back = f"{URL}?tab=people&q=ann"
        response = self.client.post(reverse("social:follow", args=["ann"]), {"next": back})
        self.assertRedirects(response, back, fetch_redirect_response=False)
        self.assertTrue(Follow.objects.filter(follower=self.bob, following=self.ann).exists())

    def test_a_muted_person_cannot_follow_and_gets_the_usual_message(self):
        sanctions.issue(self.bob, Sanction.Kind.MUTE, "Rude replies to several people.", self.boss, length=timedelta(days=1))
        self.client.force_login(self.bob)
        response = self.client.post(reverse("social:follow", args=["ann"]), headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("muted", response.json()["message"])
        self.assertFalse(Follow.objects.exists())


class QueryCountTests(PeopleSearchTestCase):
    def count(self, q):
        with CaptureQueriesContext(connection) as ctx:
            response = find(self.client, q)
        self.assertEqual(response.status_code, 200)
        return len(ctx.captured_queries)

    def make(self, prefix, n):
        for i in range(n):
            person = make_user(f"{prefix}{i:02d}")
            make_project(person, name=f"P{i}")
            if i % 2:
                badges.grant(person, "official")

    def test_the_same_number_of_queries_for_2_and_15_people(self):
        self.make("few", 2)
        self.make("many", 15)
        for who in (None, self.boss):
            with self.subTest(user=who and who.username):
                if who:
                    self.client.force_login(who)
                self.assertEqual(self.count("few"), self.count("many"))

    def test_fixed_count(self):
        self.make("many", 15)
        self.count("many")  # warm caches that are not per request (content types, site)
        with self.assertNumQueries(self.count("many")):
            find(self.client, "many")


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class RateLimitTests(PeopleSearchTestCase):
    def test_anonymous_visitors_are_limited(self):
        make_user("anna")
        for _ in range(people.RATE_LIMIT_ANON):
            self.assertEqual(find(self.client, "ann").status_code, 200)
        response = find(self.client, "ann")
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Too many searches", status_code=429)
        self.assertEqual(response.context["results"], [])

    def test_accounts_have_their_own_limit(self):
        for _ in range(people.RATE_LIMIT_ANON + 1):
            find(self.client, "ann")
        self.client.force_login(self.boss)
        self.assertEqual(find(self.client, "ann").status_code, 200)

    def test_empty_and_short_queries_do_not_count(self):
        for _ in range(people.RATE_LIMIT_ANON + 5):
            find(self.client, "a")
        self.assertEqual(find(self.client, "ann").status_code, 200)

    def test_the_cache_key_holds_no_address_and_no_query(self):
        find(self.client, "secretname", REMOTE_ADDR="203.0.113.9")
        keys = [k for k in cache._cache if "people_search" in k]  # LocMemCache internals, test only
        self.assertTrue(keys)
        self.assertFalse(any("203.0.113.9" in k or "secretname" in k for k in keys))


class LogTests(PeopleSearchTestCase):
    def test_the_query_is_never_logged(self):
        records = []

        class Keep(logging.Handler):
            def emit(self, record):
                records.append(self.format(record))

        handler = Keep(level=logging.DEBUG)
        root = logging.getLogger()
        root.addHandler(handler)
        old = root.level
        root.setLevel(logging.DEBUG)
        try:
            with override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}):
                for _ in range(people.RATE_LIMIT_ANON + 2):  # also the 429, which Django logs
                    find(self.client, "zqxwv")
                find(self.client, "zqxwv", page=9)  # and a 404
        finally:
            root.removeHandler(handler)
            root.setLevel(old)
        self.assertTrue(records)
        self.assertFalse([r for r in records if "zqxwv" in r])


class PageTests(PeopleSearchTestCase):
    def test_tabs_and_the_projects_tab_still_works(self):
        owner = make_user("ann")
        make_project(owner, name="Tallyhook")
        projects = self.client.get(URL, {"q": "tally"})
        self.assertEqual(projects.context["tab"], "projects")
        self.assertContains(projects, "Tallyhook")
        self.assertContains(projects, f'href="{URL}?tab=people"')
        self.assertEqual(find(self.client, "ann").context["tab"], "people")

    def test_header_search_submits_to_people(self):
        html = self.client.get(reverse("pages:landing")).content.decode()
        self.assertIn('class="site-search', html)
        self.assertIn('name="tab" value="people"', html)

    def test_people_pages_are_not_indexed(self):
        self.assertContains(find(self.client, "ann"), 'name="robots" content="noindex, follow"')

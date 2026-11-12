from datetime import timedelta

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from projects.models import BuildLogEntry, Project
from projects.tests import TEMP_MEDIA, make_project, make_shot, make_user

from . import queries
from .models import Follow, Like
from .views import FOLLOW_LIMIT, LIKE_LIMIT

JSON = {"HTTP_ACCEPT": "application/json"}


def follow_url(user, name="follow"):
    return reverse(f"social:{name}", args=[user.username])


def like_url(project, name="like"):
    return reverse(f"social:{name}", args=[project.owner.username, project.slug])


class SocialTestCase(TestCase):
    def setUp(self):
        cache.clear()  # rate limits live in the cache
        self.me = make_user("me")
        self.ana = make_user("ana")
        self.project = make_project(self.ana)


class ConstraintTests(SocialTestCase):
    def test_follow_pair_is_unique(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.me, following=self.ana)

    def test_database_refuses_self_follow(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.me, following=self.me)

    def test_like_pair_is_unique(self):
        Like.objects.create(user=self.me, project=self.project)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Like.objects.create(user=self.me, project=self.project)

    def test_follow_is_one_direction(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        Follow.objects.create(follower=self.ana, following=self.me)  # allowed: the reverse pair is another row
        self.assertEqual(Follow.objects.count(), 2)


class FollowTests(SocialTestCase):
    def test_follow_and_unfollow_json(self):
        self.client.force_login(self.me)
        data = self.client.post(follow_url(self.ana), **JSON).json()
        self.assertEqual(data, {"ok": True, "pressed": True, "count": 1})
        data = self.client.post(follow_url(self.ana, "unfollow"), **JSON).json()
        self.assertEqual(data, {"ok": True, "pressed": False, "count": 0})
        self.assertFalse(Follow.objects.exists())

    def test_repeating_a_request_changes_nothing(self):
        self.client.force_login(self.me)
        for _ in range(3):
            self.client.post(follow_url(self.ana), **JSON)
        self.assertEqual(Follow.objects.count(), 1)
        self.client.post(follow_url(self.ana, "unfollow"), **JSON)
        self.assertEqual(self.client.post(follow_url(self.ana, "unfollow"), **JSON).status_code, 200)

    def test_plain_post_redirects_back(self):
        self.client.force_login(self.me)
        profile = reverse("accounts:profile", args=[self.ana.username])
        response = self.client.post(follow_url(self.ana))
        self.assertRedirects(response, profile, fetch_redirect_response=False)
        self.assertTrue(Follow.objects.filter(follower=self.me, following=self.ana).exists())

    def test_next_is_followed_only_on_this_site(self):
        self.client.force_login(self.me)
        ok = self.client.post(follow_url(self.ana), {"next": "/feed/?tab=latest"})
        self.assertEqual(ok["Location"], "/feed/?tab=latest")
        evil = self.client.post(follow_url(self.ana), {"next": "https://evil.example/x"})
        self.assertEqual(evil["Location"], reverse("accounts:profile", args=[self.ana.username]))

    def test_cannot_follow_yourself(self):
        self.client.force_login(self.me)
        response = self.client.post(follow_url(self.me), **JSON)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Follow.objects.exists())

    def test_signed_out(self):
        self.assertEqual(self.client.post(follow_url(self.ana), **JSON).status_code, 401)
        response = self.client.post(follow_url(self.ana))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response["Location"])
        self.assertFalse(Follow.objects.exists())

    def test_get_is_not_allowed(self):
        self.client.force_login(self.me)
        self.assertEqual(self.client.get(follow_url(self.ana)).status_code, 405)

    def test_suspended_or_unknown_target_is_404(self):
        self.client.force_login(self.me)
        bad = make_user("bad", is_suspended=True)
        self.assertEqual(self.client.post(follow_url(bad), **JSON).status_code, 404)
        self.assertEqual(self.client.post(reverse("social:follow", args=["nobody"]), **JSON).status_code, 404)

    def test_suspended_user_cannot_follow(self):
        self.me.is_suspended = True
        self.me.save()
        self.client.force_login(self.me)
        self.assertEqual(self.client.post(follow_url(self.ana), **JSON).status_code, 403)
        self.assertFalse(Follow.objects.exists())

    def test_rate_limit(self):
        self.client.force_login(self.me)
        limit = FOLLOW_LIMIT[0]
        for _ in range(limit):
            self.assertEqual(self.client.post(follow_url(self.ana), **JSON).status_code, 200)
        response = self.client.post(follow_url(self.ana), **JSON)
        self.assertEqual(response.status_code, 429)
        self.assertFalse(response.json()["ok"])

    def test_follower_count_ignores_suspended_followers(self):
        bad = make_user("bad", is_suspended=True)
        Follow.objects.create(follower=self.me, following=self.ana)
        Follow.objects.create(follower=bad, following=self.ana)
        self.assertEqual(queries.follower_count(self.ana), 1)

    def test_profile_shows_button_and_real_count(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        self.client.force_login(self.me)
        response = self.client.get(reverse("accounts:profile", args=["ana"]))
        self.assertContains(response, 'id="followers-count" data-count>1<')
        self.assertContains(response, "data-social-form")
        mine = self.client.get(reverse("accounts:profile", args=["me"]))
        self.assertNotContains(mine, "data-social-form")  # no button on your own profile


class LikeTests(SocialTestCase):
    def test_like_and_unlike_json(self):
        self.client.force_login(self.me)
        self.assertEqual(self.client.post(like_url(self.project), **JSON).json(), {"ok": True, "pressed": True, "count": 1})
        self.assertEqual(self.client.post(like_url(self.project, "unlike"), **JSON).json(), {"ok": True, "pressed": False, "count": 0})

    def test_repeating_a_like_counts_once(self):
        self.client.force_login(self.me)
        for _ in range(3):
            self.client.post(like_url(self.project), **JSON)
        self.assertEqual(Like.objects.count(), 1)

    def test_cannot_like_own_project(self):
        # Decision: self-likes are refused. A like is a signal from someone else.
        self.client.force_login(self.ana)
        response = self.client.post(like_url(self.project), **JSON)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Like.objects.exists())

    def test_own_project_page_shows_count_without_button(self):
        Like.objects.create(user=self.me, project=self.project)
        self.client.force_login(self.ana)
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "1 like")
        self.assertNotContains(response, "data-social-form")

    def test_other_peoples_unpublished_projects_are_404(self):
        self.client.force_login(self.me)
        draft = make_project(self.ana, name="Draft", status=Project.Status.DRAFT)
        hidden = make_project(self.ana, name="Hidden", status=Project.Status.HIDDEN)
        for project in (draft, hidden):
            self.assertEqual(self.client.post(like_url(project), **JSON).status_code, 404)
        self.assertFalse(Like.objects.exists())

    def test_project_of_suspended_owner_is_404(self):
        self.ana.is_suspended = True
        self.ana.save()
        self.client.force_login(self.me)
        self.assertEqual(self.client.post(like_url(self.project), **JSON).status_code, 404)

    def test_signed_out(self):
        self.assertEqual(self.client.post(like_url(self.project), **JSON).status_code, 401)
        self.assertEqual(self.client.post(like_url(self.project)).status_code, 302)
        self.assertFalse(Like.objects.exists())

    def test_suspended_user_cannot_like(self):
        self.me.is_suspended = True
        self.me.save()
        self.client.force_login(self.me)
        self.assertEqual(self.client.post(like_url(self.project), **JSON).status_code, 403)
        self.assertFalse(Like.objects.exists())

    def test_rate_limit(self):
        self.client.force_login(self.me)
        for _ in range(LIKE_LIMIT[0]):
            self.assertEqual(self.client.post(like_url(self.project), **JSON).status_code, 200)
        self.assertEqual(self.client.post(like_url(self.project), **JSON).status_code, 429)

    def test_likes_of_suspended_users_do_not_count(self):
        bad = make_user("bad", is_suspended=True)
        Like.objects.create(user=self.me, project=self.project)
        Like.objects.create(user=bad, project=self.project)
        self.assertEqual(queries.like_state(self.project, self.me), (1, True))
        row = queries.with_social(Project.objects.filter(pk=self.project.pk), self.me).get()
        self.assertEqual((row.like_count, row.liked), (1, True))

    def test_project_page_has_button(self):
        self.client.force_login(self.me)
        self.assertContains(self.client.get(self.project.get_absolute_url()), "data-social-form")
        self.client.logout()  # signed out: a link to sign in, not a form
        response = self.client.get(self.project.get_absolute_url())
        self.assertNotContains(response, "data-social-form")
        self.assertContains(response, reverse("account_login"))


class FeedTests(SocialTestCase):
    def feed(self, tab=None, page=None, **extra):
        params = {k: v for k, v in (("tab", tab), ("page", page)) if v is not None}
        return self.client.get(reverse("social:feed"), params, **extra)

    def names(self, response):
        return [i.obj.name for i in response.context["items"] if i.kind == "project"]

    def test_signed_out_sees_for_you_only(self):
        for response in (self.feed(), self.feed("following")):
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["tab"], "foryou")
            self.assertEqual(self.names(response), ["Tallyhook"])
            self.assertNotContains(response, 'class="feed-nav__link" href="/feed/?tab=following"')
            self.assertNotContains(response, 'class="feed-tabs__link" href="/feed/?tab=following"')

    def test_signed_in_defaults_to_for_you_and_can_open_following(self):
        self.client.force_login(self.me)
        response = self.feed()
        self.assertEqual(response.context["tab"], "foryou")
        self.assertEqual(self.names(response), ["Tallyhook"])
        self.assertContains(response, "?tab=following")
        response = self.feed("following")
        self.assertEqual(response.context["tab"], "following")
        self.assertContains(response, "Nothing here yet")

    def test_latest_hides_drafts_hidden_and_suspended(self):
        make_project(self.ana, name="Draft", status=Project.Status.DRAFT)
        make_project(self.ana, name="Hidden", status=Project.Status.HIDDEN)
        bad = make_user("bad", is_suspended=True)
        make_project(bad, name="FromBad")
        self.assertEqual(self.names(self.feed("latest")), ["Tallyhook"])

    def test_latest_is_newest_first(self):
        old = make_project(self.ana, name="Old")
        Project.objects.filter(pk=old.pk).update(launched_at=timezone.now() - timedelta(days=5))
        make_project(self.ana, name="New")
        self.assertEqual(self.names(self.feed("latest")), ["New", "Tallyhook", "Old"])

    def test_project_without_launch_date_is_still_listed(self):
        Project.objects.filter(pk=self.project.pk).update(launched_at=None)
        self.assertEqual(self.names(self.feed("latest")), ["Tallyhook"])

    def test_following_shows_only_people_you_follow(self):
        bob = make_user("bob")
        make_project(bob, name="NotFollowed")
        Follow.objects.create(follower=self.me, following=self.ana)
        self.client.force_login(self.me)
        self.assertEqual(self.names(self.feed("following")), ["Tallyhook"])

    def test_following_includes_updates_but_not_launch_entries(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        update = BuildLogEntry.objects.create(project=self.project, text="Shipped **webhooks**")
        BuildLogEntry.objects.create(project=self.project, text="We launched", kind=BuildLogEntry.Kind.LAUNCH)
        self.client.force_login(self.me)
        response = self.feed("following")
        entries = [i.obj for i in response.context["items"] if i.kind == "entry"]
        self.assertEqual(entries, [update])
        self.assertContains(response, "<strong>webhooks</strong>")
        self.assertEqual(response.context["items"][0].kind, "entry")  # newer than the project itself

    def test_following_excludes_suspended_and_unpublished(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        BuildLogEntry.objects.create(project=self.project, text="Visible update")
        draft = make_project(self.ana, name="Draft", status=Project.Status.DRAFT)
        BuildLogEntry.objects.create(project=draft, text="Secret draft update")
        self.client.force_login(self.me)
        response = self.feed("following")
        self.assertContains(response, "Visible update")
        self.assertNotContains(response, "Secret draft update")
        self.assertNotIn("Draft", self.names(response))

        self.ana.is_suspended = True
        self.ana.save()
        response = self.feed("following")
        self.assertEqual(list(response.context["items"]), [])
        self.assertNotContains(response, "Visible update")

    def test_follow_by_a_suspended_user_shows_nothing(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        self.me.is_suspended = True
        self.me.save()
        self.client.force_login(self.me)
        self.assertEqual(self.names(self.feed("following")), [])

    def test_pagination_pages_and_links(self):
        for n in range(queries.PAGE_SIZE + 4):  # plus the setUp project: PAGE_SIZE + 5 in total
            make_project(self.ana, name=f"P{n}")
        first = self.feed("latest")
        self.assertEqual(len(first.context["items"]), queries.PAGE_SIZE)
        self.assertEqual(first.context["next_url"], "/feed/?sort=newest&page=2")  # "latest" = For you, newest first
        self.assertContains(first, 'rel="next"')
        self.assertNotContains(first, 'rel="prev"')
        second = self.feed("latest", 2)
        self.assertEqual(len(second.context["items"]), 5)
        self.assertEqual(second.context["next_url"], "")
        self.assertContains(second, 'rel="prev"')
        self.assertNotContains(second, 'rel="next"')
        self.assertFalse({i.obj.pk for i in first.context["items"]} & {i.obj.pk for i in second.context["items"]})

    def test_pagination_in_the_merged_following_feed(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        for n in range(queries.PAGE_SIZE + 5):
            BuildLogEntry.objects.create(project=self.project, text=f"Update {n}")
        self.client.force_login(self.me)
        seen = []
        for page in (1, 2):
            response = self.feed("following", page)
            seen += [(i.kind, i.obj.pk) for i in response.context["items"]]
        self.assertEqual(len(seen), queries.PAGE_SIZE + 5 + 1)  # all updates and the project, none twice
        self.assertEqual(len(set(seen)), len(seen))

    def test_bad_page_numbers(self):
        self.assertEqual(self.feed("latest", "abc").context["page"], 1)
        self.assertEqual(self.feed("latest", 0).context["page"], 1)
        self.assertEqual(self.feed("latest", queries.MAX_PAGE + 1).status_code, 404)

    def test_load_more_returns_json(self):
        for n in range(queries.PAGE_SIZE):
            make_project(self.ana, name=f"P{n}")
        response = self.feed("latest", 2, **JSON)
        data = response.json()
        self.assertEqual(data["next_url"], "")
        self.assertIn("data-feed-item", data["html"])
        self.assertNotIn("<html", data["html"])

    def test_cards_show_like_state(self):
        Like.objects.create(user=self.me, project=self.project)
        self.client.force_login(self.me)
        item = self.feed("latest").context["items"][0].obj
        self.assertEqual((item.like_count, item.liked), (1, True))


FOLLOWING_QUERIES = 12


@override_settings(MEDIA_ROOT=TEMP_MEDIA)  # make_shot stores real files
class FeedQueryCountTests(SocialTestCase):
    """The feed must be a fixed number of queries, however many projects are on the page."""

    def populate(self, n):
        for i in range(n):
            project = make_project(self.ana, name=f"Plate {i}")
            make_shot(project)
            Like.objects.create(user=self.me, project=project)
            BuildLogEntry.objects.create(project=project, text=f"Update {i}")

    def count_queries(self, params):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse("social:feed"), params)
        self.assertEqual(response.status_code, 200)
        return len(ctx)

    def test_latest_tab_is_constant(self):
        self.client.force_login(self.me)
        self.populate(2)
        few = self.count_queries({"tab": "latest"})
        self.populate(15)
        self.assertEqual(self.count_queries({"tab": "latest"}), few)

    def test_following_tab_is_constant(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        self.client.force_login(self.me)
        self.populate(2)
        few = self.count_queries({"tab": "following"})
        self.populate(15)
        self.assertEqual(self.count_queries({"tab": "following"}), few)

    def test_exact_query_counts(self):
        Follow.objects.create(follower=self.me, following=self.ana)
        self.populate(5)
        self.client.force_login(self.me)
        # Signed in: session, user, the user's active sanctions (ban check) | projects, screenshots, domain checks,
        # owners' badges | tags, tools (filter panel), latest news | the user's badges and unread notices (header).
        with self.assertNumQueries(12):
            self.client.get(reverse("social:feed"), {"tab": "latest"})
        # Following: no filter panel (no tags, tools), but build-log entries and their owners' badges.
        with self.assertNumQueries(FOLLOWING_QUERIES):
            self.client.get(reverse("social:feed"), {"tab": "following"})
        self.client.logout()
        with self.assertNumQueries(7):  # no session, user, sanctions, header badges, notices
            self.client.get(reverse("social:feed"))

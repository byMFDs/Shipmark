"""The /feed/ page (stage 4): tabs, filters in the URL, the "For you" ranking, cards, exclusions, query counts."""
import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts import badges
from accounts.models import User
from moderation import sanctions
from news.models import NewsPost
from projects.models import BuildLogEntry, Project, Tag, Tool
from projects.proof import compute_hallmarks
from projects.test_proof import ProofTestCase
from projects.tests import TEMP_MEDIA, image_file, make_project, make_shot, make_user
from verification.models import DomainVerification, RepoLink
from verification.uptime import with_uptime

from . import feed as feeds
from . import ranking
from .models import Follow, Like
from .queries import PAGE_SIZE, project_cards


def names(response):
    return [i.obj.name for i in response.context["items"] if i.kind == "project"]


def age(project, **delta):
    """Move the launch back in time (event_at is launched_at, or created_at without one)."""
    Project.objects.filter(pk=project.pk).update(launched_at=timezone.now() - timedelta(**delta))
    return Project.objects.get(pk=project.pk)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class FeedCase(ProofTestCase):
    """ProofTestCase gives `self.owner` (ann) and a project with a repo and a live URL, plus the proof helpers."""

    def get(self, **params):
        return self.client.get(reverse("social:feed"), params)

    def project_of(self, owner, name, **extra):
        return make_project(owner, name=name, **extra)

    def likers(self, project, count):
        for n in range(count):
            Like.objects.create(user=make_user(f"liker-{project.pk}-{n}"), project=project)

    def followers(self, person, count):
        for n in range(count):
            Follow.objects.create(follower=make_user(f"fan-{person.pk}-{n}"), following=person)


# ---------- URL parameters ----------

class ParameterTests(FeedCase):
    def test_default_tab_is_for_you_for_everyone(self):
        self.assertEqual(self.get().context["tab"], "foryou")
        self.client.force_login(self.owner)
        self.assertEqual(self.get().context["tab"], "foryou")
        self.assertEqual(self.get(tab="following").context["tab"], "following")
        self.assertEqual(self.get(tab="news").context["tab"], "news")

    def test_following_needs_an_account(self):
        self.assertEqual(self.get(tab="following").context["tab"], "foryou")

    def test_old_latest_name_means_for_you_newest_first(self):
        response = self.get(tab="latest")
        self.assertEqual((response.context["tab"], response.context["params"]["sort"]), ("foryou", "newest"))

    def test_bad_values_are_ignored_not_errors(self):
        for params in ({"tab": "zzz"}, {"sort": "zzz"}, {"range": "1y"}, {"mark": "gold"}, {"page": "abc"},
                       {"page": "-3"}, {"page": "0"}, {"tag": "x" * 500}, {"tool": "../etc"}):
            response = self.get(**params)
            self.assertEqual(response.status_code, 200, params)
        self.assertEqual(self.get(page="abc").context["page"], 1)

    def test_page_past_the_limit_is_404(self):
        self.assertEqual(self.get(page="51").status_code, 404)
        self.assertEqual(self.get(page="50").status_code, 200)

    def test_urls_carry_only_non_default_values(self):
        params = {"tab": "foryou", "tag": "", "tool": "", "mark": "", "range": "all", "sort": "popular", "page": 1}
        self.assertEqual(feeds.feed_url(params), "/feed/")
        self.assertEqual(feeds.feed_url(params, page=2), "/feed/?page=2")
        self.assertEqual(feeds.feed_url({**params, "tag": "ai", "range": "7d", "sort": "newest"}, page=3),
                         "/feed/?tag=ai&range=7d&sort=newest&page=3")
        self.assertEqual(feeds.feed_url({**params, "tab": "news", "tag": "ai"}), "/feed/?tab=news")  # filters are For you's


# ---------- Filters ----------

class FilterTests(FeedCase):
    def setUp(self):
        super().setUp()
        self.ai, _created = Tag.objects.get_or_create(slug="ai", defaults={"name": "ai"})
        self.cli, _created = Tag.objects.get_or_create(slug="cli", defaults={"name": "cli"})
        self.claude = Tool.objects.get(slug="claude-code")
        self.cursor = Tool.objects.get(slug="cursor")
        self.a = self.project_of(self.owner, "Alpha")
        self.b = self.project_of(self.owner, "Beta")
        self.a.tags.add(self.ai)
        self.a.built_with.add(self.claude)
        self.b.tags.add(self.cli)
        self.b.built_with.add(self.cursor)
        self.project.delete()  # the ProofTestCase project would be a third row

    def test_tag_and_tool(self):
        self.assertEqual(sorted(names(self.get(tag="ai"))), ["Alpha"])
        self.assertEqual(sorted(names(self.get(tag="cli"))), ["Beta"])
        self.assertEqual(sorted(names(self.get(tool="claude-code"))), ["Alpha"])
        self.assertEqual(sorted(names(self.get(tool="cursor", tag="ai"))), [])  # both must match
        self.assertEqual(sorted(names(self.get())), ["Alpha", "Beta"])

    def test_time_range(self):
        age(self.a, hours=2)
        age(self.b, days=3)
        old = age(self.project_of(self.owner, "Older"), days=20)
        oldest = age(self.project_of(self.owner, "Oldest"), days=60)
        self.assertEqual(sorted(names(self.get(range="24h", sort="newest"))), ["Alpha"])
        self.assertEqual(sorted(names(self.get(range="7d"))), ["Alpha", "Beta"])
        self.assertEqual(sorted(names(self.get(range="30d"))), ["Alpha", "Beta", "Older"])
        self.assertEqual(sorted(names(self.get(range="all"))), ["Alpha", "Beta", "Older", "Oldest"])
        self.assertTrue(old.pk and oldest.pk)

    def test_newest_sort_is_by_launch_time(self):
        age(self.a, days=2)
        age(self.b, hours=1)
        self.likers(self.a, 5)
        self.assertEqual(names(self.get(sort="newest")), ["Beta", "Alpha"])
        self.assertEqual(names(self.get(sort="popular")), ["Alpha", "Beta"])  # five likes beat a day of freshness

    def test_hallmark_filter_is_exact(self):
        self.a.repo_full_name, self.a.live_url = "ann/alpha", "https://alpha.example/"
        self.a.save()
        self.link(self.a, is_owner=True)
        self.verify(self.a)
        self.b.live_url = "https://beta.example/"
        self.b.save()
        self.verify(self.b, confirmed_days_ago=40)  # confirmed too long ago: not Live
        self.assertEqual(names(self.get(mark="authored")), ["Alpha"])
        self.assertEqual(names(self.get(mark="live")), ["Alpha"])
        self.assertEqual(names(self.get(mark="steady")), [])
        self.checks(ok=40, project=self.a)
        self.assertEqual(names(self.get(mark="steady")), ["Alpha"])
        for item in self.get(mark="live").context["items"]:
            self.assertTrue(item.obj.hallmarks["live"].earned)

    def test_filters_and_pagination_links_work_without_js(self):
        for n in range(PAGE_SIZE + 3):
            project = self.project_of(self.owner, f"Tagged {n}")
            project.tags.add(self.ai)
        response = self.get(tag="ai", sort="newest", range="30d")
        self.assertEqual(response.context["next_url"], "/feed/?tag=ai&range=30d&sort=newest&page=2")
        self.assertContains(response, 'rel="next"')
        html = response.content.decode()
        self.assertIn('<form class="feed-filters" method="get" action="/feed/">', html)
        for field in ("sort", "range", "mark", "tag", "tool"):
            self.assertIn(f'name="{field}"', html)
        self.assertRegex(html, r'<option value="ai" selected>')
        self.assertContains(response, "Clear filters")
        second = self.get(tag="ai", sort="newest", range="30d", page=2)
        self.assertEqual(len(second.context["items"]), 4)  # 3 new ones and Alpha, which also has the tag
        self.assertContains(second, 'rel="prev"')

    def test_nothing_matching_says_so_and_offers_to_clear(self):
        response = self.get(tag="no-such-tag")
        self.assertContains(response, "No projects match")
        self.assertContains(response, "Clear filters")

    def test_filters_belong_to_for_you_only(self):
        self.client.force_login(self.owner)
        for tab in ("following", "news"):
            self.assertNotContains(self.get(tab=tab), 'name="sort"')
        self.assertContains(self.get(), 'name="sort"')

    def test_filtered_pages_are_not_indexed(self):
        self.assertNotContains(self.get(), "noindex")
        self.assertContains(self.get(tag="ai"), 'content="noindex, follow"')
        self.assertContains(self.get(page=2), 'content="noindex, follow"')


# ---------- Ranking ----------

class RankingTests(FeedCase):
    def score_of(self, *projects):
        now = timezone.now()
        rows = ranking.with_score(project_cards(Project.objects.filter(pk__in=[p.pk for p in projects]), AnonymousUser()), now)
        return {row.name: row.score for row in rows}

    def setUp(self):
        super().setUp()
        self.project.delete()

    def test_formula_in_whole_numbers(self):
        """(2 likes + followers/5 + 3 marks + 1) x decay, times 10 for likes/followers/marks and times 2 for the decay."""
        fresh = self.project_of(self.owner, "Fresh")
        liked = self.project_of(make_user("bob"), "Liked")
        self.likers(liked, 1)
        old = age(self.project_of(make_user("cy"), "Old"), days=45)
        week = age(self.project_of(make_user("di"), "Week"), days=5)
        three_days = age(self.project_of(make_user("ed"), "Three"), days=2)
        scores = self.score_of(fresh, liked, old, week, three_days)
        self.assertEqual(scores["Fresh"], (0 + 0 + 0 + 10) * 16)
        self.assertEqual(scores["Liked"], (20 + 10) * 16)
        self.assertEqual(scores["Old"], 10 * 1)
        self.assertEqual(scores["Week"], 10 * 4)
        self.assertEqual(scores["Three"], 10 * 8)

    def test_followers_count_up_to_a_cap(self):
        self.followers(self.owner, 3)
        project = self.project_of(self.owner, "Followed")
        self.assertEqual(self.score_of(project)["Followed"], (2 * 3 + 10) * 16)
        with mock.patch.object(ranking, "FOLLOWER_CAP", 2):
            self.assertEqual(self.score_of(project)["Followed"], (2 * 2 + 10) * 16)

    def test_suspended_accounts_do_not_count(self):
        project = self.project_of(self.owner, "Liked")
        Like.objects.create(user=make_user("ghost", is_suspended=True), project=project)
        Follow.objects.create(follower=make_user("ghost2", is_suspended=True), following=self.owner)
        self.assertEqual(self.score_of(project)["Liked"], 10 * 16)

    def test_marks_add_points(self):
        project = self.project_of(self.owner, "Proven", live_url="https://example.com/", repo_full_name="ann/tally")
        self.link(project, is_owner=True)
        self.verify(project)
        self.assertEqual(self.score_of(project)["Proven"], (30 * 2 + 10) * 16)

    def test_a_popular_older_project_beats_a_fresh_empty_one_but_not_forever(self):
        fresh = self.project_of(self.owner, "Fresh")
        liked_two_days = age(self.project_of(make_user("bob"), "Liked2d"), days=2)
        self.likers(liked_two_days, 5)  # (100 + 10) * 8 = 880 > 160
        liked_old = age(self.project_of(make_user("cy"), "LikedOld"), days=60)
        self.likers(liked_old, 5)  # (100 + 10) * 1 = 110 < 160
        self.assertEqual(names(self.get()), ["Liked2d", "Fresh", "LikedOld"])

    def test_ties_are_broken_by_launch_then_id_and_pages_never_overlap(self):
        for n in range(PAGE_SIZE + 6):
            self.project_of(make_user(f"u{n}"), f"P{n}")
        first, second = self.get(), self.get(page=2)
        seen = [i.obj.pk for i in first.context["items"]] + [i.obj.pk for i in second.context["items"]]
        self.assertEqual(len(seen), PAGE_SIZE + 6)
        self.assertEqual(len(set(seen)), len(seen))
        self.assertEqual(seen, [i.obj.pk for i in self.get().context["items"]] + [i.obj.pk for i in self.get(page=2).context["items"]])


class MarkParityTests(FeedCase):
    """The SQL marks used for ranking against compute_hallmarks (the definition). SQL may only err upwards."""

    def setUp(self):
        super().setUp()
        self.project.delete()
        self.cases = {}

    def case(self, name, **kwargs):
        project = self.project_of(make_user(f"o-{name}"), name, **kwargs)
        self.cases[name] = project
        return project

    def build(self):
        ok = self.case("repo_owner", repo_full_name="a/one"); self.link(ok, is_owner=True)
        tok = self.case("repo_token", repo_full_name="a/two"); self.link(tok, is_owner=False, token_file_found=True)
        no = self.case("repo_neither", repo_full_name="a/three"); self.link(no, is_owner=False)
        rev = self.case("repo_review", repo_full_name="a/four"); self.link(rev, is_owner=True, review_state="needs_review")
        rec = self.case("repo_recheck", repo_full_name="a/five"); self.link(rec, is_owner=True, review_state="needs_recheck")
        app = self.case("repo_approved", repo_full_name="a/six"); self.link(app, is_owner=False, token_file_found=True, review_state="approved")
        stale = self.case("repo_renamed", repo_full_name="a/seven"); self.link(stale, is_owner=True, repo_full_name="a/old-name")
        low = self.case("repo_case", repo_full_name="A/Eight"); self.link(low, is_owner=True, repo_full_name="a/eight")
        self.case("nothing")
        live = self.case("live", live_url="https://live.example/"); self.verify(live)
        old = self.case("live_old", live_url="https://old.example/"); self.verify(old, confirmed_days_ago=36)
        edge = self.case("live_35", live_url="https://edge.example/"); self.verify(edge, confirmed_days_ago=34)
        pend = self.case("live_pending", live_url="https://pend.example/"); self.verify(pend, status=DomainVerification.Status.PENDING)
        fail = self.case("live_failed", live_url="https://fail.example/"); self.verify(fail, status=DomainVerification.Status.FAILED)
        nourl = self.case("live_no_url", live_url="https://nourl.example/"); self.verify(nourl)
        Project.objects.filter(pk=nourl.pk).update(live_url="")
        for name, total, ok_count, verified in (("steady_40", 40, 40, True), ("steady_39", 39, 39, True),
                                                ("steady_95", 40, 38, True), ("steady_92", 40, 37, True),
                                                ("steady_nolive", 40, 40, False), ("steady_big", 100, 95, True),
                                                ("steady_big_low", 100, 94, True)):
            project = self.case(name, live_url=f"https://{name.replace('_', '-')}.example/")
            if verified:
                self.verify(project)
            self.checks(ok=ok_count, failed=total - ok_count, project=project)
        everything = self.case("everything", repo_full_name="a/all", live_url="https://all.example/")
        self.link(everything, is_owner=True); self.verify(everything); self.checks(ok=45, project=everything)

    def sql_marks(self):
        now = timezone.now()
        qs = ranking.with_marks(with_uptime(Project.objects.filter(pk__in=[p.pk for p in self.cases.values()]), now), now)
        return {p.name: p.marks for p in qs}

    def test_sql_matches_compute_hallmarks(self):
        self.build()
        sql = self.sql_marks()
        for name, project in self.cases.items():
            exact = compute_hallmarks(self.fresh(project)).earned_count
            self.assertEqual(sql[name], exact, name)
        self.assertEqual(sql["everything"], 3)
        self.assertEqual(sql["steady_95"], 2)  # exactly 95% passes
        self.assertEqual(sql["steady_92"], 1)
        self.assertEqual(sql["steady_big_low"], 1)

    def test_the_only_known_difference_is_a_changed_domain(self):
        """A verified row for an old domain still counts in SQL; compute_hallmarks compares the live URL's host."""
        project = self.case("moved", live_url="https://first.example/")
        self.verify(project)
        Project.objects.filter(pk=project.pk).update(live_url="https://second.example/")
        self.assertEqual(self.sql_marks()["moved"], 1)
        self.assertEqual(compute_hallmarks(self.fresh(project)).earned_count, 0)
        self.assertEqual(names(self.get(mark="live")), [])  # the filter itself uses the exact rule


# ---------- Cards ----------

class CardTests(FeedCase):
    def setUp(self):
        super().setUp()
        self.me = make_user("me")
        self.project.delete()
        self.p = self.project_of(self.owner, "Quillbox")
        self.p.tagline = "Replay webhooks <b>fast</b>"
        self.p.save()

    def test_cover_uses_the_small_thumbnail(self):
        shot = make_shot(self.p)
        self.assertTrue(shot.thumb)
        html = self.get().content.decode()
        self.assertIn(f'src="{shot.thumb.url}"', html)
        self.assertNotIn(f'src="{shot.image.url}"', html)
        self.assertIn(f'width="{shot.thumb_width}" height="{shot.thumb_height}"', html)
        self.assertIn('loading="lazy"', html)

    def test_cover_falls_back_to_the_full_image_while_there_is_no_thumbnail(self):
        shot = make_shot(self.p)
        Project.objects.filter(pk=self.p.pk).update()
        type(shot).objects.filter(pk=shot.pk).update(thumb="", thumb_width=0, thumb_height=0)
        self.assertIn(f'src="{shot.image.url}"', self.get().content.decode())

    def test_no_cover_no_image(self):
        self.assertNotContains(self.get(), "feed-card__cover")

    def test_owner_badges_name_tagline_marks_and_time(self):
        badges.grant(self.owner, "official")
        self.p.repo_full_name = "ann/q"
        self.p.save()
        self.link(self.p, is_owner=True)
        html = self.get().content.decode()
        self.assertIn("user-mark--official", html)
        self.assertIn("@ann", html)
        self.assertIn("Quillbox", html)
        self.assertIn("Replay webhooks &lt;b&gt;fast&lt;/b&gt;", html)  # escaped
        self.assertNotIn("<b>fast</b>", html)
        self.assertIn("Repo owner", html)
        self.assertRegex(html, r'<time datetime="[^"]+" title="[^"]+">')

    def test_latest_update_snippet_is_sanitized_and_skips_the_launch_entry(self):
        BuildLogEntry.objects.create(project=self.p, text="Launched it", kind="launch")
        BuildLogEntry.objects.create(project=self.p, text="Older **update**")
        BuildLogEntry.objects.create(project=self.p, text="Newest <script>alert(1)</script> [x](javascript:alert(1)) `code`")
        html = self.get().content.decode()
        self.assertIn("Latest update", html)
        self.assertIn("Newest", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("javascript:", html)
        self.assertIn("<code>code</code>", html)
        self.assertNotIn("Older", html)
        self.assertNotIn("Launched it", html)

    def test_like_and_follow_state_for_a_signed_in_viewer(self):
        Follow.objects.create(follower=self.me, following=self.owner)
        Like.objects.create(user=self.me, project=self.p)
        self.client.force_login(self.me)
        html = self.get().content.decode()
        self.assertIn(f'data-url-off="{reverse("social:unfollow", args=["ann"])}"', html)
        self.assertRegex(html, r'aria-pressed="true"[^>]*>\s*<span data-label[^>]*>Following')
        self.assertRegex(html, r'aria-pressed="true"[^>]*>\s*<span data-label[^>]*>Liked')
        self.assertIn("data-social-form", html)  # social.js makes both optimistic

    def test_signed_out_sees_links_to_sign_in_not_forms(self):
        html = self.get().content.decode()
        self.assertIn(reverse("account_login"), html)
        self.assertNotIn("data-social-form", html)

    def test_own_project_has_no_follow_button(self):
        self.client.force_login(self.owner)
        html = self.get().content.decode()
        self.assertNotIn(reverse("social:follow", args=["ann"]), html)
        self.assertIn("social-note", html)  # the like count as text

    def test_moderate_menu_only_for_moderators(self):
        act = reverse("moderation:act_project", args=[self.p.pk])
        mod = make_user("mira")
        badges.grant(mod, "moderator")
        self.client.force_login(mod)
        self.assertContains(self.get(), act)
        self.client.force_login(self.me)
        self.assertNotContains(self.get(), act)


# ---------- What must never show ----------

class ExclusionTests(FeedCase):
    def setUp(self):
        super().setUp()
        self.project.delete()
        self.me = make_user("me")
        self.boss = make_user("boss", is_superuser=True)
        self.visible = self.project_of(self.owner, "Visible")

    def hidden_ones(self):
        draft = self.project_of(self.owner, "Draft", status=Project.Status.DRAFT)
        hidden = self.project_of(self.owner, "Hidden", status=Project.Status.HIDDEN)
        removed = self.project_of(self.owner, "Removed", status=Project.Status.REMOVED)
        suspended = make_user("sus", is_suspended=True)
        from_suspended = self.project_of(suspended, "FromSuspended")
        banned = make_user("ban")
        from_banned = self.project_of(banned, "FromBanned")
        sanctions.issue(banned, "ban", "Fake proof, repeatedly.", self.boss, length=timedelta(days=3))
        return [draft, hidden, removed, from_suspended, from_banned], [suspended, banned]

    def test_for_you_excludes_them_in_every_variant(self):
        self.hidden_ones()
        for params in ({}, {"sort": "newest"}, {"range": "24h"}, {"tab": "latest"}):
            self.assertEqual(names(self.get(**params)), ["Visible"], params)

    def test_filters_exclude_them_too(self):
        projects, _people = self.hidden_ones()
        tag = Tag.objects.create(name="shared", slug="shared")
        for project in projects + [self.visible]:
            project.tags.add(tag)
        self.assertEqual(names(self.get(tag="shared")), ["Visible"])

    def test_hallmark_filter_excludes_them(self):
        projects, _people = self.hidden_ones()
        for project in projects + [self.visible]:
            project.live_url = f"https://{project.slug}.example/"
            project.save()
            self.verify(project)
        self.assertEqual(names(self.get(mark="live")), ["Visible"])

    def test_following_excludes_them_and_their_updates(self):
        projects, people = self.hidden_ones()
        for person in [self.owner, *people]:
            Follow.objects.create(follower=self.me, following=person)
        for project in projects:
            BuildLogEntry.objects.create(project=project, text=f"secret {project.name}")
        BuildLogEntry.objects.create(project=self.visible, text="public note")
        self.client.force_login(self.me)
        response = self.get(tab="following")
        self.assertEqual(names(response), ["Visible"])
        html = response.content.decode()
        self.assertIn("public note", html)
        self.assertNotIn("secret", html)

    def test_a_banned_persons_tags_do_not_appear_in_the_filter(self):
        _projects, people = self.hidden_ones()
        banned = next(p for p in people if p.username == "ban")
        secret = Tag.objects.create(name="bannedonly", slug="bannedonly")
        Project.objects.get(owner=banned).tags.add(secret)
        self.assertNotContains(self.get(), "bannedonly")

    def test_a_mute_does_not_hide_anything(self):
        sanctions.issue(self.owner, "mute", "Spam, against the rules.", self.boss, length=timedelta(days=1))
        self.assertEqual(names(self.get()), ["Visible"])

    def test_a_banned_owner_is_gone_from_load_more_json_too(self):
        self.hidden_ones()
        data = json.loads(self.client.get(reverse("social:feed"), HTTP_ACCEPT="application/json").content)
        self.assertIn("Visible", data["html"])
        for word in ("FromBanned", "FromSuspended", "Removed", "Hidden", "Draft"):
            self.assertNotIn(word, data["html"])


# ---------- Load more ----------

class LoadMoreTests(FeedCase):
    def test_json_has_html_and_the_next_link(self):
        self.project.delete()
        for n in range(PAGE_SIZE + 2):
            self.project_of(make_user(f"u{n}"), f"P{n}")
        response = self.client.get(reverse("social:feed"), HTTP_ACCEPT="application/json")
        data = json.loads(response.content)
        self.assertEqual(data["html"].count("data-feed-item"), PAGE_SIZE)
        self.assertEqual(data["next_url"], "/feed/?page=2")
        second = json.loads(self.client.get(data["next_url"], HTTP_ACCEPT="application/json").content)
        self.assertEqual(second["html"].count("data-feed-item"), 2)
        self.assertEqual(second["next_url"], "")

    def test_the_page_has_the_load_more_link_and_the_script(self):
        self.project.delete()
        for n in range(PAGE_SIZE + 1):
            self.project_of(make_user(f"u{n}"), f"P{n}")
        response = self.get()
        self.assertContains(response, "data-load-more")
        self.assertContains(response, "js/feed.js")


# ---------- News tab ----------

class NewsTabTests(FeedCase):
    def setUp(self):
        super().setUp()
        now = timezone.now()
        self.live = NewsPost.objects.create(title="Hello world", slug="hello", body="First **post**", published_at=now - timedelta(days=1))
        self.pinned = NewsPost.objects.create(title="Read me first", slug="first", body="Pinned", pinned=True, published_at=now - timedelta(days=9))
        NewsPost.objects.create(title="Secret draft", slug="draft", body="x")
        NewsPost.objects.create(title="Not yet", slug="later", body="x", published_at=now + timedelta(days=2))

    def test_lists_only_published_official_posts_pinned_first(self):
        response = self.get(tab="news")
        self.assertEqual([i.obj.title for i in response.context["items"]], ["Read me first", "Hello world"])
        self.assertNotContains(response, "Secret draft")
        self.assertNotContains(response, "Not yet")

    def test_byline_is_shipmark_with_the_official_badge_and_links_to_the_post(self):
        html = self.get(tab="news").content.decode()
        self.assertIn("news-byline__name\">Shipmark", html)
        self.assertIn("user-mark--official", html)
        self.assertIn(reverse("news:detail", args=["hello"]), html)

    def test_anonymous_visitors_can_read_it(self):
        self.assertEqual(self.get(tab="news").status_code, 200)

    def test_user_projects_never_appear_on_the_news_tab(self):
        self.assertNotContains(self.get(tab="news"), self.project.name if self.project.pk else "zzz")
        self.assertEqual(names(self.get(tab="news")), [])

    def test_the_side_panel_shows_the_latest_three_posts_elsewhere_but_not_on_news(self):
        for n in range(4):
            NewsPost.objects.create(title=f"Extra {n}", slug=f"extra-{n}", body="x", published_at=timezone.now() - timedelta(hours=n))
        response = self.get()
        self.assertEqual(len(response.context["latest_news"]), 3)
        self.assertContains(response, "Latest news")
        self.assertEqual(self.get(tab="news").context["latest_news"], [])

    def test_news_json_for_load_more(self):
        data = json.loads(self.client.get(reverse("social:feed"), {"tab": "news"}, HTTP_ACCEPT="application/json").content)
        self.assertIn("Hello world", data["html"])
        self.assertIn("Shipmark", data["html"])


# ---------- Page structure ----------

class StructureTests(FeedCase):
    def test_three_columns_a_nav_and_sticky_tabs(self):
        self.client.force_login(self.owner)
        html = self.get().content.decode()
        for cls in ("feed-layout", "feed-nav", "feed-main", "feed-side", "feed-tabs"):
            self.assertIn(cls, html)
        self.assertIn(reverse("pages:explore"), html)  # Explore stays, as its own item
        self.assertIn('class="feed-nav__link" href="/feed/?tab=news"', html)

    def test_explore_is_untouched_and_in_the_header(self):
        self.assertEqual(self.client.get(reverse("pages:explore")).status_code, 200)
        self.assertContains(self.get(), 'class="site-nav__link" href="/explore/"')
        self.assertContains(self.get(), 'class="site-nav__link" href="/news/"')

    def test_empty_states_have_no_dashed_frame(self):
        self.project.delete()
        response = self.get()
        self.assertContains(response, "empty empty--plain")
        css = open("static/css/components.css", encoding="utf-8").read()
        self.assertIn(".empty--plain { border: 0;", css)

    def test_one_h1_and_labelled_controls(self):
        html = self.get().content.decode()
        self.assertEqual(html.count("<h1"), 1)
        for field in ("sort", "range", "mark", "tag", "tool"):
            self.assertIn(f'for="f-d-{field}"', html)
            self.assertIn(f'for="f-m-{field}"', html)


# ---------- No N+1 ----------

class QueryCountTests(FeedCase):
    """The number of queries does not depend on the number of cards."""

    def populate(self, count, start=0):
        for n in range(start, start + count):
            owner = make_user(f"owner{n}")
            badges.grant(owner, "moderator") if n % 3 == 0 else None
            project = self.project_of(owner, f"Card {n}")
            make_shot(project)
            BuildLogEntry.objects.create(project=project, text=f"update {n}")
            self.likers(project, 1)

    def queries(self, **params):
        with CaptureQueriesContext(connection) as ctx:
            response = self.get(**params)
        self.assertEqual(response.status_code, 200)
        return len(ctx)

    def follow_all(self, me):
        for owner in User.objects.filter(username__startswith="owner"):
            Follow.objects.get_or_create(follower=me, following=owner)

    def test_constant_for_every_tab_and_filter_path(self):
        self.project.delete()
        me = make_user("me")
        variants = [{}, {"sort": "newest"}, {"tag": "x"}, {"range": "7d"}, {"mark": "live"}, {"tab": "following"}, {"tab": "news"}]
        for who in ("anonymous", "signed in"):
            if who == "signed in":
                self.client.force_login(me)
            self.populate(2)
            self.follow_all(me)
            few = {tuple(v.items()): self.queries(**v) for v in variants}
            self.populate(12, start=2)
            self.follow_all(me)
            many = {tuple(v.items()): self.queries(**v) for v in variants}
            self.assertEqual(few, many, who)
            self.client.logout()
            User.objects.filter(username__startswith="owner").delete()  # projects, follows and likes go with them

    def test_the_hallmark_filter_path_is_constant_too(self):
        self.project.delete()
        for n in range(3):
            project = self.project_of(make_user(f"o{n}"), f"P{n}", live_url=f"https://p{n}.example/")
            self.verify(project)
        few = self.queries(mark="live")
        for n in range(3, 15):
            project = self.project_of(make_user(f"o{n}"), f"P{n}", live_url=f"https://p{n}.example/")
            self.verify(project)
        self.assertEqual(self.queries(mark="live"), few)

    def test_json_load_more_is_constant(self):
        self.project.delete()
        self.populate(2)
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse("social:feed"), HTTP_ACCEPT="application/json")
        few = len(ctx)
        self.populate(15, start=2)
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse("social:feed"), HTTP_ACCEPT="application/json")
        self.assertEqual(len(ctx), few)

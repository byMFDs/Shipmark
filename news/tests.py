"""Official news: only the admin writes it (superusers, or staff with the news permissions)."""
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from moderation.models import AuditLog

from .models import NewsPost


def post_data(**extra):
    data = {"title": "Domain checks are faster", "slug": "faster-domain-checks", "body": "We **changed** it.",
            "published_at_0": "", "published_at_1": ""}
    data.update(extra)
    return data


class NewsModelTests(TestCase):
    def test_published_drafts_and_scheduled(self):
        now = timezone.now()
        live = NewsPost.objects.create(title="A", slug="a", body="x", published_at=now - timedelta(minutes=1))
        NewsPost.objects.create(title="B", slug="b", body="x")  # draft
        NewsPost.objects.create(title="C", slug="c", body="x", published_at=now + timedelta(days=1))  # scheduled
        self.assertEqual(list(NewsPost.objects.published(now)), [live])
        self.assertTrue(live.is_published(now))

    def test_pinned_first(self):
        now = timezone.now()
        old = NewsPost.objects.create(title="Old", slug="old", body="x", published_at=now - timedelta(days=9), pinned=True)
        new = NewsPost.objects.create(title="New", slug="new", body="x", published_at=now)
        self.assertEqual(list(NewsPost.objects.published()), [old, new])

    def test_body_is_sanitized(self):
        post = NewsPost(title="x", slug="x", body='Hi <script>alert(1)</script> [link](javascript:alert(1))')
        self.assertNotIn("<script", post.body_html)
        self.assertNotIn("javascript:", post.body_html)


class NewsAdminTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        self.add_url = reverse("admin:news_newspost_add")

    def test_superuser_writes_and_it_is_logged(self):
        self.client.force_login(self.boss)
        response = self.client.post(self.add_url, post_data())
        self.assertEqual(response.status_code, 302)
        post = NewsPost.objects.get()
        self.assertEqual(post.created_by, self.boss)
        self.assertIsNone(post.published_at)
        self.assertTrue(AuditLog.objects.filter(action="news.created", actor=self.boss).exists())
        local = timezone.localtime()
        response = self.client.post(reverse("admin:news_newspost_change", args=[post.pk]), post_data(
            published_at_0=local.strftime("%Y-%m-%d"), published_at_1=local.strftime("%H:%M:%S")))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(AuditLog.objects.filter(action="news.published").count(), 1)
        self.assertTrue(AuditLog.objects.filter(action="news.updated").exists())

    def test_plain_staff_cannot_write(self):
        staff = User.objects.create_user("clerk", password="x", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.add_url).status_code, 403)
        self.assertEqual(self.client.post(self.add_url, post_data()).status_code, 403)
        self.assertFalse(NewsPost.objects.exists())

    def test_staff_with_the_permission_can_write(self):
        editor = User.objects.create_user("editor", password="x", is_staff=True)
        editor.user_permissions.set(Permission.objects.filter(
            content_type__app_label="news", codename__in=["add_newspost", "change_newspost", "view_newspost"]))
        self.client.force_login(editor)
        response = self.client.post(self.add_url, post_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NewsPost.objects.get().created_by, editor)

    def test_no_public_write_endpoint(self):
        self.client.force_login(User.objects.create_user("ana", password="x"))
        for url in ("/news/", "/news/new/", "/news/faster-domain-checks/edit/"):
            self.assertIn(self.client.post(url, post_data()).status_code, (403, 404, 405))
        self.assertFalse(NewsPost.objects.exists())


# ---------- Public pages (stage 4) ----------

class PublicNewsTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.pinned = NewsPost.objects.create(title="Read me first", slug="first", body="Pinned **news**", pinned=True,
                                              published_at=now - timedelta(days=20))
        self.newer = NewsPost.objects.create(title="Newer post", slug="newer", body="Body of the **newer** post. " * 30,
                                             published_at=now - timedelta(days=1))
        self.draft = NewsPost.objects.create(title="Secret draft", slug="draft", body="x")
        self.later = NewsPost.objects.create(title="Scheduled", slug="later", body="x", published_at=now + timedelta(days=3))

    def test_everyone_can_read_the_list_and_a_post(self):
        for url in (reverse("news:list"), self.newer.get_absolute_url()):
            self.assertEqual(self.client.get(url).status_code, 200, url)  # anonymous
        self.client.force_login(User.objects.create_user("ann", password="x"))
        self.assertEqual(self.client.get(reverse("news:list")).status_code, 200)

    def test_list_has_published_posts_only_pinned_first(self):
        response = self.client.get(reverse("news:list"))
        self.assertEqual([p.slug for p in response.context["posts"]], ["first", "newer"])
        self.assertNotContains(response, "Secret draft")
        self.assertNotContains(response, "Scheduled")

    def test_drafts_scheduled_and_unknown_posts_are_404_for_everyone(self):
        staff = User.objects.create_superuser("boss", "b@example.com", "pw")
        for who in (None, staff):
            if who:
                self.client.force_login(who)
            for slug in ("draft", "later", "nope"):
                self.assertEqual(self.client.get(reverse("news:detail", args=[slug])).status_code, 404, (who, slug))

    def test_a_scheduled_post_appears_when_its_time_comes(self):
        NewsPost.objects.filter(pk=self.later.pk).update(published_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get(reverse("news:detail", args=["later"])).status_code, 200)

    def test_byline_is_shipmark_with_the_official_badge(self):
        for url in (reverse("news:list"), self.newer.get_absolute_url()):
            html = self.client.get(url).content.decode()
            self.assertIn('news-byline__name">Shipmark', html, url)
            self.assertIn("user-mark--official", html, url)
            self.assertNotIn("boss", html)  # the staff member who wrote it stays internal

    def test_open_graph_and_meta_for_a_post(self):
        html = self.client.get(self.newer.get_absolute_url()).content.decode()
        self.assertIn('<meta property="og:type" content="article">', html)
        self.assertIn('og:title" content="Newer post · Shipmark"', html)
        self.assertIn('property="article:published_time"', html)
        self.assertRegex(html, r'og:description" content="Body of the newer post\. ')
        self.assertIn('<link rel="canonical" href="http', html)
        self.assertIn('property="og:image"', html)

    def test_body_is_markdown_and_sanitized(self):
        post = NewsPost.objects.create(title="Mixed", slug="mixed", published_at=timezone.now(),
                                       body="Hi **there**\n\n<script>alert(1)</script>\n\n[bad](javascript:alert(1)) <img src=x onerror=alert(2)>")
        html = self.client.get(post.get_absolute_url()).content.decode()
        self.assertIn("<strong>there</strong>", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("javascript:", html)
        self.assertNotIn("<img src=x", html)  # raw HTML is shown as inert text, never as an element
        self.assertIn("&lt;img src=x onerror=alert(2)&gt;", html)

    def test_titles_are_escaped(self):
        post = NewsPost.objects.create(title="<b>Bold</b> & co", slug="esc", body="x", published_at=timezone.now())
        html = self.client.get(reverse("news:list")).content.decode()
        self.assertIn("&lt;b&gt;Bold&lt;/b&gt; &amp; co", html)
        self.assertNotIn("<b>Bold</b>", html)
        self.assertEqual(post.excerpt, "x")

    def test_excerpt_is_plain_text_up_to_200_characters(self):
        excerpt = self.newer.excerpt
        self.assertLessEqual(len(excerpt), 200)
        self.assertTrue(excerpt.endswith("…"))
        self.assertNotIn("*", excerpt)
        self.assertNotIn("<", excerpt)

    def test_pagination_with_plain_links(self):
        for n in range(11):
            NewsPost.objects.create(title=f"Extra {n}", slug=f"extra-{n}", body="x", published_at=timezone.now() - timedelta(hours=n + 1))
        first = self.client.get(reverse("news:list"))
        self.assertEqual(len(first.context["posts"]), 10)
        self.assertContains(first, 'rel="next"')
        self.assertNotContains(first, "noindex")
        second = self.client.get(reverse("news:list"), {"page": 2})
        self.assertEqual(len(second.context["posts"]), 3)
        self.assertContains(second, 'rel="prev"')
        self.assertContains(second, "noindex")
        self.assertEqual(self.client.get(reverse("news:list"), {"page": 3}).status_code, 404)
        self.assertEqual(self.client.get(reverse("news:list"), {"page": 101}).status_code, 404)
        self.assertEqual(self.client.get(reverse("news:list"), {"page": "x"}).status_code, 200)

    def test_nothing_can_be_written_through_the_site(self):
        self.client.force_login(User.objects.create_superuser("boss", "b@example.com", "pw"))
        for url in (reverse("news:list"), self.newer.get_absolute_url()):
            for method in ("post", "put", "patch", "delete"):
                self.assertEqual(getattr(self.client, method)(url, {"title": "x"}).status_code, 405, (method, url))
        self.assertEqual(NewsPost.objects.count(), 4)

    def test_no_empty_state_frame_and_a_message_when_there_is_no_news(self):
        NewsPost.objects.all().delete()
        response = self.client.get(reverse("news:list"))
        self.assertContains(response, "No news yet")
        self.assertContains(response, "empty empty--plain")

    def test_queries_do_not_grow_with_the_number_of_posts(self):
        def count(url):
            with CaptureQueriesContext(connection) as ctx:
                self.assertEqual(self.client.get(url).status_code, 200)
            return len(ctx)

        few = (count(reverse("news:list")), count(self.newer.get_absolute_url()))
        for n in range(9):
            NewsPost.objects.create(title=f"More {n}", slug=f"more-{n}", body="x", published_at=timezone.now() - timedelta(hours=n + 2))
        self.assertEqual((count(reverse("news:list")), count(self.newer.get_absolute_url())), few)
        with self.assertNumQueries(3):  # a visitor without a session: the posts, the system account, its badges
            self.client.get(reverse("news:list"))

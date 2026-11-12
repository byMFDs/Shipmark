"""Official news: only the admin writes it (superusers, or staff with the news permissions)."""
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
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

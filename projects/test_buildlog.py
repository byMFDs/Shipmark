from datetime import timedelta

from django.core.cache import cache
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation

from .models import LOG_ENTRIES_PER_DAY, BuildLogEntry, Project
from .rendering import render_log_markdown
from .tests import make_project, make_user

JSON = {"HTTP_ACCEPT": "application/json"}


def add_url(project):
    return reverse("projects:log_add", args=[project.owner.username, project.slug])


def delete_url(entry):
    p = entry.project
    return reverse("projects:log_delete", args=[p.owner.username, p.slug, entry.pk])


class BuildLogTestCase(TestCase):
    """Спільні дані для тестів журналу збірки."""
    def setUp(self):
        cache.clear()  # rate limits live in the cache
        self.owner = make_user("owner")
        self.other = make_user("other")
        self.project = make_project(self.owner)

    def entry(self, text="Shipped webhooks", project=None, **extra):
        return BuildLogEntry.objects.create(project=project or self.project, text=text, **extra)


class PermissionTests(BuildLogTestCase):
    """Хто може писати в журнал."""
    def test_owner_adds_entry_with_plain_post(self):
        self.client.force_login(self.owner)
        response = self.client.post(add_url(self.project), {"text": "First update"})
        self.assertRedirects(response, self.project.get_absolute_url() + "#build-log", fetch_redirect_response=False)
        self.assertEqual(self.project.log_entries.get().text, "First update")

    def test_owner_adds_entry_with_json(self):
        self.client.force_login(self.owner)
        response = self.client.post(add_url(self.project), {"text": "Added **search**"}, **JSON)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertIn("<strong>search</strong>", data["html"])
        self.assertIn("Delete entry", data["html"])
        self.assertTrue(data["can_launch"])

    def test_other_user_and_anonymous_cannot_add_or_delete(self):
        entry = self.entry()
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(add_url(self.project), {"text": "Hijack"}).status_code, 404)
        self.assertEqual(self.client.post(delete_url(entry)).status_code, 404)
        self.client.logout()
        response = self.client.post(add_url(self.project), {"text": "Hijack"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
        self.assertEqual(self.client.post(delete_url(entry)).status_code, 302)
        self.assertEqual(list(self.project.log_entries.values_list("text", flat=True)), ["Shipped webhooks"])

    def test_entry_of_another_project_is_not_reachable_through_my_project(self):
        theirs = self.entry(project=make_project(self.other, "Theirs"))
        self.client.force_login(self.owner)
        url = reverse("projects:log_delete", args=[self.owner.username, self.project.slug, theirs.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(BuildLogEntry.objects.filter(pk=theirs.pk).exists())

    def test_owner_deletes_entry(self):
        entry = self.entry()
        self.client.force_login(self.owner)
        response = self.client.post(delete_url(entry), **JSON)
        self.assertEqual(response.json()["ok"], True)
        self.assertFalse(BuildLogEntry.objects.filter(pk=entry.pk).exists())

    def test_get_is_not_allowed(self):
        entry = self.entry()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(add_url(self.project)).status_code, 405)
        self.assertEqual(self.client.get(delete_url(entry)).status_code, 405)

    def test_suspended_owner_cannot_write(self):
        entry = self.entry()
        self.owner.is_suspended = True
        self.owner.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(add_url(self.project), {"text": "x"}).status_code, 403)
        self.assertEqual(self.client.post(delete_url(entry)).status_code, 403)
        self.assertEqual(self.project.log_entries.count(), 1)

    def test_draft_log_is_invisible_to_others(self):
        draft = make_project(self.owner, "Draft", Project.Status.DRAFT)
        self.entry("Secret plan", project=draft)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)


class LaunchTests(BuildLogTestCase):
    """Запис «запуск»."""
    def test_launch_entry_sets_launched_at(self):
        old = timezone.now() - timedelta(days=30)
        Project.objects.filter(pk=self.project.pk).update(launched_at=old)
        self.client.force_login(self.owner)
        data = self.client.post(add_url(self.project), {"text": "We are live", "is_launch": "on"}, **JSON).json()
        self.assertTrue(data["ok"])
        self.assertFalse(data["can_launch"])
        entry = self.project.log_entries.get()
        self.assertEqual(entry.kind, BuildLogEntry.Kind.LAUNCH)
        self.project.refresh_from_db()
        self.assertEqual(self.project.launched_at, entry.created_at)
        self.assertIn("Launched", data["launched_html"])

    def test_only_one_launch_per_project(self):
        self.entry("Launch", kind=BuildLogEntry.Kind.LAUNCH)
        self.client.force_login(self.owner)
        response = self.client.post(add_url(self.project), {"text": "Again", "is_launch": "on"}, **JSON)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already has a launch entry", response.json()["message"])
        self.assertEqual(self.project.log_entries.count(), 1)

    def test_deleting_launch_keeps_date_and_allows_a_new_launch(self):
        self.client.force_login(self.owner)
        self.client.post(add_url(self.project), {"text": "Launch", "is_launch": "on"})
        self.project.refresh_from_db()
        launched_at = self.project.launched_at
        entry = self.project.log_entries.get()
        data = self.client.post(delete_url(entry), **JSON).json()
        self.assertTrue(data["can_launch"])
        self.project.refresh_from_db()
        self.assertEqual(self.project.launched_at, launched_at)

    def test_launch_on_draft_survives_publish(self):
        draft = make_project(self.owner, "Draft", Project.Status.DRAFT)
        self.client.force_login(self.owner)
        self.client.post(add_url(draft), {"text": "Launch", "is_launch": "on"})
        draft.refresh_from_db()
        launched_at = draft.launched_at
        self.assertIsNotNone(launched_at)
        self.client.post(reverse("projects:publish", args=[self.owner.username, draft.slug]))
        draft.refresh_from_db()
        self.assertEqual(draft.launched_at, launched_at)


class LimitTests(BuildLogTestCase):
    """Ліміти журналу."""
    def post(self, text="Update", **extra):
        return self.client.post(add_url(self.project), {"text": text}, **extra)

    def test_text_is_required_and_at_most_500_chars(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.post("   ", **JSON).status_code, 400)
        self.assertEqual(self.post("x" * 501, **JSON).status_code, 400)
        self.assertEqual(self.post("x" * 500, **JSON).status_code, 200)
        self.assertEqual(self.project.log_entries.count(), 1)

    def test_plain_post_error_shows_page_with_text_kept(self):
        self.client.force_login(self.owner)
        response = self.post("x" * 501)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "x" * 501, status_code=400)  # the textarea keeps the text

    def test_ten_entries_a_day_per_project(self):
        self.client.force_login(self.owner)
        for _ in range(LOG_ENTRIES_PER_DAY):
            self.assertEqual(self.post(**JSON).status_code, 200)
        response = self.post(**JSON)
        self.assertEqual(response.status_code, 429)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(self.project.log_entries.count(), LOG_ENTRIES_PER_DAY)
        # Another project of the same owner has its own limit.
        other = make_project(self.owner, "Second")
        self.assertEqual(self.client.post(add_url(other), {"text": "Hi"}, **JSON).status_code, 200)

    def test_deleting_entries_does_not_refund_the_limit(self):
        self.client.force_login(self.owner)
        for _ in range(LOG_ENTRIES_PER_DAY):
            self.post()
        self.project.log_entries.all().delete()
        self.assertEqual(self.post(**JSON).status_code, 429)

    def test_db_count_holds_when_the_cache_is_empty(self):
        for _ in range(LOG_ENTRIES_PER_DAY):
            self.entry()
        self.client.force_login(self.owner)
        self.assertEqual(self.post(**JSON).status_code, 429)

    def test_entries_older_than_a_day_do_not_count(self):
        for _ in range(LOG_ENTRIES_PER_DAY):
            self.entry()
        self.project.log_entries.update(created_at=timezone.now() - timedelta(days=1, minutes=1))
        self.client.force_login(self.owner)
        self.assertEqual(self.post(**JSON).status_code, 200)


class SanitizingTests(BuildLogTestCase):
    """Очищення тексту запису."""
    def test_allowed_inline_markdown(self):
        html = render_log_markdown("**bold** *italic* `code` [site](https://example.com)")
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<em>italic</em>", html)
        self.assertIn("<code>code</code>", html)
        self.assertIn('href="https://example.com"', html)
        self.assertIn('rel="nofollow ugc noopener"', html)

    def test_html_and_scripts_are_text(self):
        html = render_log_markdown('<script>alert(1)</script><img src=x onerror=alert(1)><b onclick="x">b</b>')
        self.assertNotIn("<script", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<b ", html)
        self.assertIn("&lt;script&gt;", html)

    def test_dangerous_links_and_images_are_dropped(self):
        html = render_log_markdown("[a](javascript:alert(1)) [b](data:text/html,x) ![c](https://example.com/c.png)")
        self.assertNotIn("javascript:", html)
        self.assertNotIn("data:", html)
        self.assertNotIn("<img", html)

    def test_block_syntax_stays_text(self):
        html = render_log_markdown("# Title\n- item\n> quote\n\n```\ncode\n```")
        for tag in ("<h", "<ul", "<li", "<blockquote", "<pre"):
            self.assertNotIn(tag, html)
        self.assertIn("# Title", html)

    def test_page_shows_sanitized_entry_to_visitors(self):
        self.entry('<script>alert("x")</script> **ok**')
        response = self.client.get(self.project.get_absolute_url())
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertContains(response, "<strong>ok</strong>")
        self.assertNotContains(response, "Delete entry")  # visitors get no controls
        self.assertNotContains(response, 'data-log-form')


class TimelineTests(BuildLogTestCase):
    """Порядок записів."""
    def test_newest_first_and_hidden_for_visitors_when_empty(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertNotContains(response, 'id="build-log"')
        old = self.entry("Older entry")
        BuildLogEntry.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=3))
        self.entry("Newer entry")
        content = self.client.get(self.project.get_absolute_url()).content.decode()
        self.assertLess(content.index("Newer entry"), content.index("Older entry"))
        self.assertIn("3\xa0days ago", content)

    def test_owner_sees_form_and_empty_state(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "data-log-form")
        self.assertContains(response, "No entries yet.")

    def test_ago_filter_is_localized(self):
        template = Template("{% load ui %}{{ a|ago }}|{{ b|ago }}")
        context = Context({"a": timezone.now(), "b": timezone.now() - timedelta(days=2, hours=5)})
        self.assertEqual(template.render(context), "just now|2\xa0days ago")
        with translation.override("uk"):
            self.assertIn("тому", template.render(context))

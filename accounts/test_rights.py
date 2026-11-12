"""Legal pages, Terms re-acceptance, data export and account deletion (CLAUDE.md section 12)."""
import json

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from config import branding
from moderation.models import AuditLog, Report
from projects.models import BuildLogEntry, Project
from social.models import Follow, Like

from .usernames import generate_username, is_taken

User = get_user_model()


def make_user(username, **extra):
    extra.setdefault("terms_version_accepted", settings.TERMS_VERSION)
    return User.objects.create_user(username=username, password="x", **extra)


def make_project(owner, slug, status=Project.Status.PUBLISHED, **extra):
    return Project.objects.create(owner=owner, name=slug.title(), slug=slug, tagline=f"{slug} tagline", status=status, **extra)


class LegalPageTests(TestCase):
    def test_pages_exist_in_both_languages_with_brand_details(self):
        for slug in ("privacy", "terms", "cookies"):
            for lang in ("en", "uk"):
                response = self.client.get(f"/legal/{slug}/", HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(response.status_code, 200, (slug, lang))
                self.assertContains(response, branding.CONTACT_EMAIL)
                self.assertNotContains(response, "{{")  # every placeholder filled
                self.assertContains(response, "Draft" if lang == "en" else "Чернетка")

    def test_other_content_pages_are_not_legal_pages(self):
        self.assertEqual(self.client.get("/legal/about/").status_code, 404)
        self.assertEqual(self.client.get("/legal/nope/").status_code, 404)

    def test_footer_links_to_all_three(self):
        response = self.client.get("/explore/")
        for slug in ("privacy", "terms", "cookies"):
            self.assertContains(response, f'href="/legal/{slug}/"')


class TermsReacceptanceTests(TestCase):
    def setUp(self):
        self.user = make_user("alice", terms_version_accepted="2000-01-01")
        self.client.force_login(self.user)
        self.accept_url = reverse("accounts:accept_terms")

    def test_current_version_is_not_asked(self):
        self.user.terms_version_accepted = settings.TERMS_VERSION
        self.user.save()
        self.assertEqual(self.client.get("/settings/").status_code, 200)

    def test_account_without_any_version_is_not_asked(self):
        # Staff made with createsuperuser never went through signup.
        self.user.terms_version_accepted = ""
        self.user.save()
        self.assertEqual(self.client.get("/settings/").status_code, 200)

    @override_settings(TERMS_VERSION="2099-01-01")
    def test_bump_forces_reacceptance(self):
        self.user.terms_version_accepted = "2026-11-10"
        self.user.save()
        response = self.client.get("/settings/?tab=1")
        self.assertRedirects(response, f"{self.accept_url}?next=%2Fsettings%2F%3Ftab%3D1", fetch_redirect_response=False)
        # Writes are blocked too.
        response = self.client.post("/settings/", {"display_name": "Changed"})
        self.assertRedirects(response, self.accept_url, fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "")

        # Without the checkbox nothing changes.
        response = self.client.post(self.accept_url, {"next": "/settings/"})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.terms_version_accepted, "2026-11-10")

        response = self.client.post(self.accept_url, {"terms": "on", "next": "/settings/"})
        self.assertRedirects(response, "/settings/", fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.terms_version_accepted, "2099-01-01")
        self.assertIsNotNone(self.user.terms_accepted_at)
        self.assertEqual(self.client.get("/settings/").status_code, 200)

    @override_settings(TERMS_VERSION="2099-01-01")
    def test_pages_that_stay_open(self):
        self.assertEqual(self.client.get("/legal/terms/").status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:delete")).status_code, 200)
        self.assertEqual(self.client.get(self.accept_url).status_code, 200)
        self.assertEqual(self.client.post(reverse("accounts:export")).status_code, 200)

    @override_settings(TERMS_VERSION="2099-01-01")
    def test_badges_do_not_read_the_session(self):
        response = self.client.get("/badge/alice.svg")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Cookie", response.get("Vary", ""))

    @override_settings(TERMS_VERSION="2099-01-01")
    def test_next_must_be_on_this_site(self):
        response = self.client.post(self.accept_url, {"terms": "on", "next": "https://evil.example/"})
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL), fetch_redirect_response=False)

    def test_signed_out_visitors_are_not_affected(self):
        self.client.logout()
        self.assertEqual(self.client.get("/explore/").status_code, 200)


class ExportTests(TestCase):
    def setUp(self):
        cache.clear()
        self.alice = make_user("alice", email="alice@example.com", display_name="Alice", github_login="alice-gh")
        self.bob = make_user("bob", email="bob-private@example.com", about="bob secret bio")
        self.mine = make_project(self.alice, "alice-app")
        self.my_draft = make_project(self.alice, "alice-draft", status=Project.Status.DRAFT)
        BuildLogEntry.objects.create(project=self.mine, text="Shipped v1")
        self.bobs = make_project(self.bob, "bob-app", description="bob description")
        self.bobs_draft = make_project(self.bob, "bob-hidden-draft", status=Project.Status.DRAFT)
        BuildLogEntry.objects.create(project=self.bobs, text="bob log entry")
        Like.objects.create(user=self.alice, project=self.bobs)
        Like.objects.create(user=self.bob, project=self.mine)  # Bob's like: not Alice's data
        Follow.objects.create(follower=self.alice, following=self.bob)
        carol = make_user("carol")
        Follow.objects.create(follower=self.bob, following=carol)
        Report.objects.create(reporter=self.bob, target_user=self.alice, target_repr="alice", reason="spam", details="bob report")
        SocialAccount.objects.create(user=self.bob, provider="github", uid="999", extra_data={"login": "bob-gh"})
        EmailAddress.objects.create(user=self.bob, email="bob-other@example.com", primary=False, verified=True)
        self.url = reverse("accounts:export")

    def export(self):
        self.client.force_login(self.alice)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        return response, json.loads(response.content)

    def test_requires_login_and_post(self):
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_is_a_download(self):
        response, _ = self.export()
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertIn("alice", response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_contains_own_data(self):
        _, data = self.export()
        self.assertEqual(data["profile"]["username"], "alice")
        self.assertEqual(data["profile"]["email"], "alice@example.com")
        self.assertEqual({p["slug"] for p in data["projects"]}, {"alice-app", "alice-draft"})
        app = next(p for p in data["projects"] if p["slug"] == "alice-app")
        self.assertEqual([e["text"] for e in app["build_log"]], ["Shipped v1"])
        self.assertEqual(data["likes"][0]["project"], "bob/bob-app")
        self.assertEqual([f["username"] for f in data["following"]], ["bob"])

    def test_contains_only_own_data(self):
        response, data = self.export()
        body = response.content.decode()
        for foreign in ("bob-private@example.com", "bob secret bio", "bob description", "bob log entry",
                        "bob-hidden-draft", "bob report", "bob-gh", "bob-other@example.com", "carol"):
            self.assertNotIn(foreign, body, foreign)
        self.assertEqual(len(data["likes"]), 1)
        self.assertEqual(data["reports_made"], [])
        self.assertEqual(data["github"], {"accounts": [], "email_addresses": []})

    def test_query_count_does_not_grow_with_projects(self):
        self.client.force_login(self.alice)
        # 13 + the ban check (active sanctions) + sanctions and notices + skills, links and pins in the export
        # + community: images, threads, replies, upvotes, notifications
        with self.assertNumQueries(24):
            self.client.post(self.url)
        for i in range(5):
            p = make_project(self.alice, f"more-{i}")
            BuildLogEntry.objects.create(project=p, text="x")
        with self.assertNumQueries(24):
            self.client.post(self.url)

    def test_rate_limited(self):
        self.client.force_login(self.alice)
        for _ in range(10):
            self.client.post(self.url)
        self.assertRedirects(self.client.post(self.url), reverse("accounts:settings"), fetch_redirect_response=False)


class DeleteAccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.alice = make_user("alice", email="alice@example.com", github_login="alice-gh")
        self.bob = make_user("bob")
        self.project = make_project(self.alice, "alice-app")
        make_project(self.alice, "alice-draft", status=Project.Status.DRAFT)
        BuildLogEntry.objects.create(project=self.project, text="Shipped")
        self.bobs = make_project(self.bob, "bob-app")
        Like.objects.create(user=self.alice, project=self.bobs)
        Like.objects.create(user=self.bob, project=self.project)
        Follow.objects.create(follower=self.alice, following=self.bob)
        Follow.objects.create(follower=self.bob, following=self.alice)
        self.report = Report.objects.create(reporter=self.alice, project=self.bobs, target_repr="bob/bob-app", reason="spam")
        SocialAccount.objects.create(user=self.alice, provider="github", uid="4242", extra_data={"login": "alice-gh"})
        self.url = reverse("accounts:delete")
        self.client.force_login(self.alice)

    def test_page_explains_and_asks_for_username(self):
        response = self.client.get(self.url)
        self.assertContains(response, "cannot be undone")
        self.assertContains(response, 'name="confirm"')

    def test_wrong_username_deletes_nothing(self):
        for value in ("", "bob", "alic"):
            response = self.client.post(self.url, {"confirm": value})
            self.assertEqual(response.status_code, 200, value)
        self.assertTrue(User.objects.filter(pk=self.alice.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.bob.pk).exists())
        self.assertEqual(Project.objects.count(), 3)

    def test_requires_login(self):
        self.client.logout()
        self.client.post(self.url, {"confirm": "alice"})
        self.assertTrue(User.objects.filter(pk=self.alice.pk).exists())

    def test_deletion_removes_everything_and_frees_username(self):
        alice_id = self.alice.pk
        response = self.client.post(self.url, {"confirm": " Alice "})
        self.assertRedirects(response, reverse("pages:landing"), fetch_redirect_response=False)

        self.assertFalse(User.objects.filter(pk=alice_id).exists())
        self.assertFalse(Project.objects.filter(owner_id=alice_id).exists())
        self.assertFalse(BuildLogEntry.objects.filter(project__slug="alice-app").exists())
        self.assertFalse(Like.objects.filter(user_id=alice_id).exists())
        self.assertFalse(Like.objects.filter(project__slug="alice-app").exists())
        self.assertFalse(Follow.objects.filter(follower_id=alice_id).exists())
        self.assertFalse(Follow.objects.filter(following_id=alice_id).exists())
        self.assertFalse(SocialAccount.objects.filter(uid="4242").exists())
        # Bob and his project are untouched.
        self.assertTrue(Project.objects.filter(pk=self.bobs.pk).exists())

        # Signed out.
        self.assertNotIn("_auth_user_id", self.client.session)

        # Username is free again.
        self.assertFalse(is_taken("alice"))
        self.assertEqual(generate_username("alice"), "alice")
        User.objects.create_user(username="alice", password="x", github_login="alice-gh")

    def test_reports_made_are_anonymized_and_kept(self):
        self.client.post(self.url, {"confirm": "alice"})
        self.report.refresh_from_db()
        self.assertIsNone(self.report.reporter)
        self.assertEqual(self.report.project, self.bobs)

    def test_writes_audit_log_without_personal_data(self):
        alice_id = self.alice.pk
        self.client.post(self.url, {"confirm": "alice"})
        entry = AuditLog.objects.get(action="account.deleted")
        self.assertEqual(entry.target_id, str(alice_id))
        self.assertIsNone(entry.actor)
        self.assertEqual(entry.metadata, {
            "projects_deleted": 2, "reports_anonymized": 1, "community_images_deleted": 0,
            "community_threads_deleted": 0, "community_threads_anonymized": 0, "community_replies_anonymized": 0,
        })
        self.assertNotIn("alice", entry.target_repr)
        self.assertNotIn("alice", json.dumps(entry.metadata))

    def test_suspended_user_can_still_delete(self):
        self.alice.is_suspended = True
        self.alice.save()
        self.client.post(self.url, {"confirm": "alice"})
        self.assertFalse(User.objects.filter(username="alice").exists())

    def test_rate_limited(self):
        for _ in range(10):
            self.client.post(self.url, {"confirm": "wrong"})
        response = self.client.post(self.url, {"confirm": "alice"})
        self.assertContains(response, "Too many attempts")
        self.assertTrue(User.objects.filter(username="alice").exists())

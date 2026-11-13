"""Support form, anti-spam, private attachments, the inbox notification, the admin inbox, retention and rights."""
import io
import os
import time
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.deletion import delete_account
from accounts.export import build_export
from moderation.models import AuditLog
from projects.tests import make_user

from . import antispam
from .models import SupportAttachment, SupportMessage
from .notify import build_email
from .storage import private_storage

FORM = "/support/"
BODY = "The badge on my project page shows the wrong date since yesterday."


def png(name="shot.png", size=(60, 40)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def text_file(name="error.log", content=b"Traceback (most recent call last):\n  line 1\n"):
    return SimpleUploadedFile(name, content, content_type="text/plain")


class SupportTestCase(TestCase):
    def setUp(self):
        cache.clear()

    def data(self, **extra):
        payload = {"category": "bug", "subject": "Badge date", "body": BODY, "email": "ann@example.com",
                   "started": antispam.issue_token(time.time() - 10)}
        payload.update(extra)
        return payload

    def send(self, client=None, **extra):
        client = client or self.client
        with self.captureOnCommitCallbacks(execute=True):
            return client.post(FORM, self.data(**extra), REMOTE_ADDR="203.0.113.5")


class FormPageTests(SupportTestCase):
    def test_page_explains_topics_and_is_honest_about_replies(self):
        page = self.client.get(FORM)
        self.assertEqual(page.status_code, 200)
        for text in ("We read every message.", "We cannot promise to reply to all.", "Your email is used only to reply.",
                     "Idea or feedback", "Account or privacy", 'name="website"', 'name="started"'):
            self.assertContains(page, text)
        self.assertContains(page, 'enctype="multipart/form-data"')
        self.assertContains(page, "css/pages/support.css")

    def test_reference_from_an_error_page_is_prefilled_and_cleaned(self):
        page = self.client.get(FORM, {"category": "bug", "ref": "ab12cd34"})
        self.assertContains(page, 'value="ab12cd34"')
        self.assertContains(page, "from the error page")
        bad = self.client.get(FORM, {"ref": '"><script>alert(1)</script>'})
        self.assertNotContains(bad, "<script>alert(1)")
        self.assertNotContains(bad, "from the error page")

    def test_signed_in_email_is_prefilled(self):
        user = make_user("ann", email="ann@example.com")
        self.client.force_login(user)
        self.assertContains(self.client.get(FORM), 'value="ann@example.com"')

    def test_footer_links_to_support(self):
        self.assertContains(self.client.get("/explore/"), f'href="{reverse("support:form")}">Support</a>')

    def test_open_for_people_who_must_accept_new_terms(self):
        user = make_user("old", terms_version_accepted="2000-01-01")
        self.client.force_login(user)
        self.assertEqual(self.client.get(FORM).status_code, 200)


class SendingTests(SupportTestCase):
    def test_a_message_is_saved_without_ip_or_browser_details(self):
        response = self.send()
        self.assertRedirects(response, reverse("support:sent"))
        message = SupportMessage.objects.get()
        self.assertEqual((message.category, message.email, message.status), ("bug", "ann@example.com", "new"))
        self.assertIsNone(message.user)
        stored = " ".join(str(getattr(message, f.attname)) for f in SupportMessage._meta.fields)
        self.assertNotIn("203.0.113.5", stored)
        self.assertFalse({"ip", "ip_address", "user_agent"} & {f.name for f in SupportMessage._meta.fields})

    def test_signed_in_without_email_uses_the_account_address(self):
        user = make_user("ann", email="ann@example.com")
        self.client.force_login(user)
        self.send(email="")
        message = SupportMessage.objects.get()
        self.assertEqual((message.user, message.email), (user, "ann@example.com"))

    def test_signed_out_needs_an_email(self):
        response = self.send(email="")
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Add your email", status_code=400)
        self.assertFalse(SupportMessage.objects.exists())

    def test_length_limits_and_category(self):
        for extra in ({"body": "short"}, {"body": "x" * 4001}, {"category": "nonsense"}, {"subject": "s" * 121}):
            with self.subTest(**{k: v[:20] for k, v in extra.items()}):
                self.assertEqual(self.send(**extra).status_code, 400)
        self.assertFalse(SupportMessage.objects.exists())

    def test_sent_page_is_designed_and_honest(self):
        page = self.client.get(reverse("support:sent"))
        self.assertContains(page, "Message sent")
        self.assertContains(page, "we cannot promise to reply to all")
        self.assertContains(page, "support-sent__stamp")
        self.assertContains(self.client.get(reverse("support:sent"), {"again": "1"}), "We already have this message")


class AntiSpamTests(SupportTestCase):
    def test_honeypot_pretends_success_and_stores_nothing(self):
        with override_settings(SUPPORT_INBOX_EMAIL="inbox@example.com"):
            response = self.send(website="http://spam.example")
        self.assertRedirects(response, reverse("support:sent"))
        self.assertFalse(SupportMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_too_fast_and_forged_or_old_tokens_are_refused(self):
        cases = {
            "fast": antispam.issue_token(time.time() - 1),
            "forged": "abc:def",
            "missing": "",
            "old": antispam.issue_token(time.time() - antispam.TOKEN_MAX_AGE - 60),
        }
        for name, token in cases.items():
            with self.subTest(case=name):
                if name == "old":  # signing checks the age from its own timestamp
                    with mock.patch("django.core.signing.time.time", return_value=time.time() + antispam.TOKEN_MAX_AGE + 60):
                        response = self.send(started=token)
                else:
                    response = self.send(started=token)
                self.assertEqual(response.status_code, 400)
        self.assertFalse(SupportMessage.objects.exists())

    def test_token_rules(self):
        now = time.time()
        self.assertEqual(antispam.token_problem(antispam.issue_token(now - 3.5), now=now), "")
        self.assertEqual(antispam.token_problem(antispam.issue_token(now - 2), now=now), "fast")
        self.assertEqual(antispam.token_problem("garbage", now=now), "expired")

    def test_three_an_hour_per_session(self):
        for n in range(3):
            self.assertEqual(self.send(body=f"{BODY} Number {n}.").status_code, 302)
        response = self.send(body=f"{BODY} Number 4.")
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Please wait an hour", status_code=400)
        self.assertEqual(SupportMessage.objects.count(), 3)

    def test_the_hashed_address_limits_new_sessions_too(self):
        for n in range(3):
            client = self.client_class()
            self.assertEqual(self.send(client, body=f"{BODY} From client {n}.").status_code, 302)
        self.assertEqual(self.send(self.client_class(), body=f"{BODY} One more.").status_code, 400)

    @override_settings(CLIENT_IP_HEADER="HTTP_X_REAL_IP")
    def test_the_proxy_header_is_used_when_configured(self):
        request = mock.Mock(META={"HTTP_X_REAL_IP": "198.51.100.9", "REMOTE_ADDR": "127.0.0.1"})
        self.assertEqual(antispam.client_ip(request), "198.51.100.9")

    def test_daily_limit(self):
        keys = ["s:x", "ip:y"]
        cache.set("support:rl:day:ip:y", 10, 60)
        self.assertTrue(antispam.is_limited(keys))
        cache.set("support:rl:day:ip:y", 9, 60)
        self.assertFalse(antispam.is_limited(keys))

    def test_the_ip_is_never_a_cache_key_in_clear(self):
        key = antispam.ip_key("203.0.113.5")
        self.assertNotIn("203", key)
        self.assertEqual(len(key), 32)
        self.assertNotEqual(key, antispam.ip_key("203.0.113.6"))

    def test_duplicates_are_kept_once(self):
        self.assertRedirects(self.send(), reverse("support:sent"))
        response = self.send(body=BODY.upper() + "  ")
        self.assertRedirects(response, reverse("support:sent") + "?again=1")
        self.assertEqual(SupportMessage.objects.count(), 1)


class AttachmentTests(SupportTestCase):
    def test_images_are_re_encoded_and_text_kept_as_text_in_private_storage(self):
        response = self.send(attachments=[png(), text_file(), text_file("notes.txt", "Привіт, світ".encode())])
        self.assertEqual(response.status_code, 302)
        items = list(SupportAttachment.objects.order_by("pk"))
        self.assertEqual([a.kind for a in items], ["image", "text", "text"])
        self.assertTrue(items[0].file.name.endswith(".webp"))
        self.assertTrue(items[1].file.name.endswith(".txt"))
        for item in items:
            path = item.file.path
            self.assertTrue(path.startswith(str(settings.SUPPORT_ROOT)))
            self.assertFalse(path.startswith(str(settings.MEDIA_ROOT)))
            self.assertTrue(os.path.exists(path))
            with self.assertRaises(ValueError):
                item.file.url  # no public address, ever
        with Image.open(items[0].file.path) as stored:
            self.assertEqual(stored.format, "WEBP")
        self.assertEqual(items[2].file.read().decode(), "Привіт, світ")

    def test_other_types_and_fakes_are_refused(self):
        bad = {
            "svg": SimpleUploadedFile("x.svg", b"<svg onload='alert(1)'/>", content_type="image/svg+xml"),
            "pdf": SimpleUploadedFile("x.pdf", b"%PDF-1.4", content_type="application/pdf"),
            "html": SimpleUploadedFile("x.html", b"<script></script>", content_type="text/html"),
            "fake png": SimpleUploadedFile("x.png", b"not an image", content_type="image/png"),
            "binary txt": SimpleUploadedFile("x.txt", b"\x00\x01\x02" * 100, content_type="text/plain"),
            "big txt": SimpleUploadedFile("x.log", b"a" * (200 * 1024 + 1), content_type="text/plain"),
        }
        for name, upload in bad.items():
            with self.subTest(file=name):
                self.assertEqual(self.send(body=f"{BODY} {name}", attachments=[upload]).status_code, 400)
        self.assertFalse(SupportMessage.objects.exists())

    def test_at_most_three_files(self):
        response = self.send(attachments=[text_file(f"{n}.txt") for n in range(4)])
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Attach at most 3 files.", status_code=400)

    def test_download_only_for_staff_with_the_permission(self):
        self.send(attachments=[text_file()])
        item = SupportAttachment.objects.get()
        url = reverse("support:attachment", args=[item.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        ordinary = make_user("bob")
        staff = make_user("staff", is_staff=True)
        for user in (ordinary, staff):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 404)
        staff.user_permissions.add(Permission.objects.get(codename="view_supportmessage"))
        staff = type(staff).objects.get(pk=staff.pk)  # fresh permission cache
        self.client.force_login(staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("sandbox", response["Content-Security-Policy"])
        self.assertEqual(b"".join(response.streaming_content).decode(), "Traceback (most recent call last):\n  line 1\n")

    def test_storage_is_swappable_by_settings(self):
        self.assertIs(type(private_storage()).__name__, "PrivateStorage")
        self.assertEqual(settings.STORAGES["support"]["BACKEND"], "support.storage.PrivateStorage")


@override_settings(SUPPORT_INBOX_EMAIL="inbox@example.com", DEFAULT_FROM_EMAIL="site@example.com")
class NotificationTests(SupportTestCase):
    def test_plain_text_email_after_the_commit(self):
        self.send(subject="Hello\r\nBcc: victim@example.com", attachments=[png()])
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        message = SupportMessage.objects.get()
        self.assertEqual(email.to, ["inbox@example.com"])
        self.assertEqual(email.reply_to, ["ann@example.com"])
        self.assertEqual(email.subject, f"[{'Shipmark'} support] Bug #{message.pk}")
        self.assertNotIn("\n", email.subject)
        self.assertIn(BODY, email.body)
        self.assertIn("Attachments: 1", email.body)
        self.assertEqual(email.attachments, [])
        self.assertEqual(email.content_subtype, "plain")
        self.assertNotIn("victim", email.extra_headers.get("Bcc", ""))
        self.assertEqual(email.bcc, [])

    def test_a_failing_mail_server_does_not_lose_the_message(self):
        with mock.patch("django.core.mail.EmailMessage.send", side_effect=OSError("connection refused")):
            with self.assertLogs("support.notify", level="ERROR") as logs:
                response = self.send()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SupportMessage.objects.count(), 1)
        self.assertNotIn(BODY, "\n".join(logs.output))  # the log line has no message text

    @override_settings(SUPPORT_INBOX_EMAIL="")
    def test_no_inbox_no_email(self):
        self.send()
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(SupportMessage.objects.count(), 1)

    def test_email_is_english_whatever_the_page_language(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uk"
        self.send(category="account")
        self.assertIn("Account or privacy", mail.outbox[0].subject)
        self.assertIn("Open in the admin:", build_email(SupportMessage.objects.get()).body)


class ErrorPageTests(SupportTestCase):
    def test_404_and_500_link_to_support_with_the_request_id(self):
        response = self.client.get("/no-such-page/")
        self.assertContains(response, "Report a problem", status_code=404)
        self.assertContains(response, "/support/?category=bug&amp;ref=" + response["X-Request-ID"], status_code=404)
        with override_settings(DEBUG=True):
            preview = self.client.get("/_dev/errors/500/")
        self.assertContains(preview, "Report a problem")
        self.assertContains(preview, "/support/?category=bug&amp;ref=")


class AdminInboxTests(SupportTestCase):
    def setUp(self):
        super().setUp()
        self.boss = type(make_user("x")).objects.create_superuser("boss", "boss@example.com", "pw")
        self.message = SupportMessage.objects.create(email="ann@example.com", category="bug", body=BODY)
        self.list_url = reverse("admin:support_supportmessage_changelist")
        self.change_url = reverse("admin:support_supportmessage_change", args=[self.message.pk])

    def test_staff_without_permission_cannot_open_the_inbox(self):
        staff = make_user("staff", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.list_url).status_code, 403)
        dashboard = self.client.get(reverse("admin:index"))
        self.assertNotContains(dashboard, "Unread support messages")

    def test_superuser_sees_the_count_opens_and_it_becomes_read(self):
        self.client.force_login(self.boss)
        self.assertContains(self.client.get(reverse("admin:index")), "Unread support messages")
        page = self.client.get(self.change_url)
        self.assertContains(page, "mailto:ann@example.com?subject=")
        self.assertContains(page, "Reply by email")
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, "read")
        self.assertTrue(AuditLog.objects.filter(action="support.status", target_id=str(self.message.pk)).exists())

    def test_status_actions_are_logged(self):
        self.client.force_login(self.boss)
        response = self.client.post(self.list_url, {"action": "mark_closed", "_selected_action": [self.message.pk]})
        self.assertEqual(response.status_code, 302)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, "closed")
        self.assertTrue(AuditLog.objects.filter(action="support.status", metadata__status="closed").exists())

    def test_nobody_can_add_messages_in_the_admin(self):
        self.client.force_login(self.boss)
        self.assertEqual(self.client.get(reverse("admin:support_supportmessage_add")).status_code, 403)


class RetentionAndRightsTests(SupportTestCase):
    def test_prune_deletes_old_closed_messages_with_files(self):
        self.send(attachments=[text_file()])
        old = SupportMessage.objects.get()
        path = old.attachments.get().file.path
        SupportMessage.objects.filter(pk=old.pk).update(status="closed", created_at=timezone.now() - timedelta(days=400))
        keep_open = SupportMessage.objects.create(email="a@example.com", category="bug", body=BODY,
                                                  created_at=timezone.now() - timedelta(days=400))
        keep_new = SupportMessage.objects.create(email="b@example.com", category="bug", body=BODY, status="closed")
        with self.captureOnCommitCallbacks(execute=True):
            call_command("prune_support", stdout=io.StringIO())
        self.assertEqual(set(SupportMessage.objects.values_list("pk", flat=True)), {keep_open.pk, keep_new.pk})
        self.assertFalse(os.path.exists(path))

    def test_export_contains_own_messages_only(self):
        user = make_user("ann", email="ann@example.com")
        self.client.force_login(user)
        self.send(email="", attachments=[text_file()])
        SupportMessage.objects.create(email="other@example.com", category="bug", body="Someone else entirely here.")
        SupportMessage.objects.filter(user=user).update(internal_note="Staff only")
        exported = build_export(user)["support_messages"]
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]["message"], BODY)
        self.assertEqual(exported[0]["attachments"][0]["kind"], "text")
        self.assertNotIn("Staff only", str(exported))

    def test_account_deletion_removes_messages_and_files(self):
        user = make_user("ann", email="ann@example.com")
        self.client.force_login(user)
        self.send(email="", attachments=[text_file()])
        path = SupportAttachment.objects.get().file.path
        self.client.logout()
        cache.clear()
        self.send(email="ANN@example.com", body=f"{BODY} Sent while signed out.")
        other = SupportMessage.objects.create(email="other@example.com", category="bug", body=BODY)
        with self.captureOnCommitCallbacks(execute=True):
            entry = delete_account(user)
        self.assertEqual(list(SupportMessage.objects.values_list("pk", flat=True)), [other.pk])
        self.assertFalse(os.path.exists(path))
        self.assertEqual(entry.metadata["support_messages_deleted"], 2)

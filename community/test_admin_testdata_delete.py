"""Production-like admin lifecycle and adversarial deletion requests on isolated databases."""
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from accounts.system import system_user
from pages.stats import count_people, public_user_count
from . import services, testdata_tools as tools
from .models import Reply, Thread, TestDataObject, TestDataFile
from .test_admin_testdata import MediaMixin, profile_post, png


class ProductionAdminTests(MediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        setting = override_settings(DEBUG=False, SETTINGS_MODULE="config.settings.prod",
                                    SITE_URL="https://shipmark.example", TEST_DATA_ADMIN_ENABLED=True)
        setting.enable()
        self.addCleanup(setting.disable)
        self.client.force_login(self.boss)

    def sample(self):
        ann = self.add_test_user("sample-one", avatar_file=png())
        bob = self.add_test_user("sample-two")
        self.assertEqual(self.add_thread(ann).status_code, 302)
        thread = Thread.objects.get(author=ann)
        self.assertEqual(self.add_reply(bob, thread).status_code, 302)
        return ann, bob, thread, thread.replies.get()

    def remove(self, model, pk=None, **data):
        name = model + ("_delete" if pk else "_cleanup")
        url = self.admin_url(name, *([pk] if pk else []))
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(url, {"confirm": "yes", **data})

    def test_create_edit_delete_reply_then_thread_then_account(self):
        ann, bob, thread, reply = self.sample()
        response = self.client.post(self.admin_url("testaccount_change", ann.pk), profile_post(ann.username, display_name="Міра"))
        self.assertEqual(response.status_code, 302)
        response = self.client.post(self.admin_url("testthread_change", thread.pk), {"title": "Оновлена тема", "body": "Оновлений текст"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(self.admin_url("testreply_change", reply.pk), {"body": "Оновлена відповідь"})
        self.assertEqual(response.status_code, 302)
        thread.refresh_from_db()
        self.assertEqual(thread.body, "Оновлений текст")
        preview = self.client.get(self.admin_url("testreply_delete", reply.pk))
        self.assertContains(preview, "Підтвердити видалення")
        self.assertTrue(Reply.objects.filter(pk=reply.pk).exists())
        self.assertEqual(self.remove("testreply", reply.pk).status_code, 302)
        thread.refresh_from_db()
        self.assertEqual(thread.reply_count, 0)
        self.assertEqual(thread.last_activity_at, thread.created_at)
        self.assertEqual(self.remove("testthread", thread.pk).status_code, 302)
        self.assertTrue(User.objects.filter(pk=ann.pk).exists())
        self.assertEqual(self.remove("testaccount", ann.pk).status_code, 302)
        self.assertFalse(ann.avatar.storage.exists(ann.avatar.name))
        self.assertTrue(User.objects.filter(pk=bob.pk).exists())

    def test_bulk_and_full_cleanup_preserve_control(self):
        ann, bob, thread, reply = self.sample()
        real = services.create_thread(self.real, self.board, "Control thread", "Keep")
        listing = self.admin_url("testaccount_changelist")
        self.assertContains(self.client.get(listing), "Очистити весь тестовий набір")
        response = self.client.post(listing, {"action": "remove_selected_test_data", "_selected_action": [ann.pk, bob.pk]})
        self.assertEqual(response.status_code, 302)
        preview = self.client.get(response.url)
        self.assertContains(preview, "Підтвердити видалення")
        self.assertContains(preview, f"community.reply #{reply.pk}")
        token = preview.context["selection"]
        self.assertEqual(self.remove("testaccount", selection=token).status_code, 302)
        self.assertFalse(User.objects.filter(pk__in=[ann.pk, bob.pk]).exists())
        self.assertTrue(Thread.objects.filter(pk=real.pk).exists())
        self.assertTrue(User.objects.filter(pk=system_user().pk).exists())
        self.assertEqual(public_user_count(), count_people())
        self.assertEqual(self.remove("testaccount").status_code, 302)

    def test_real_dependency_added_after_preview_blocks_everything(self):
        ann, bob, thread, reply = self.sample()
        self.assertContains(self.client.get(self.admin_url("testaccount_cleanup")), "Підтвердити видалення")
        real_reply = services.create_reply(self.real, thread, parent=reply, body="Keep this real answer")
        for model, pk in (("testreply", reply.pk), ("testthread", thread.pk), ("testaccount", ann.pk), ("testaccount", None)):
            response = self.remove(model, pk)
            self.assertContains(response, "Очищення заблоковано")
            self.assertContains(response, str(real_reply.pk))
        self.assertTrue(User.objects.filter(pk=ann.pk).exists())
        self.assertTrue(ann.avatar.storage.exists(ann.avatar.name))
        self.assertEqual(thread.replies.count(), 2)

    def test_permissions_flag_system_and_untracked_targets(self):
        ann, bob, thread, reply = self.sample()
        for person in (self.real, system_user()):
            response = self.remove("testaccount", person.pk)
            self.assertContains(response, "Очищення заблоковано")
            self.assertTrue(User.objects.filter(pk=person.pk).exists())
        Thread.objects.filter(pk=thread.pk).update(pinned=True)
        self.assertContains(self.remove("testthread", thread.pk), "Очищення заблоковано")
        with override_settings(TEST_DATA_ADMIN_ENABLED=False):
            self.assertEqual(self.client.get(self.admin_url("testaccount_changelist")).status_code, 403)
            self.assertEqual(self.remove("testaccount").status_code, 403)
            self.assertEqual(self.client.post(self.admin_url("testaccount_add"), profile_post("forbidden")).status_code, 403)
        staff = User.objects.create_user("staff-person", is_staff=True)
        staff.user_permissions.set(Permission.objects.all())
        self.client.force_login(staff)
        for url in (self.admin_url("testaccount_cleanup"), self.admin_url("testaccount_delete", ann.pk),
                    self.admin_url("testthread_add"), self.admin_url("testreply_add")):
            self.assertEqual(self.client.post(url, {"confirm": "yes"}).status_code, 403)
        self.assertTrue(User.objects.filter(pk=ann.pk).exists())

    def test_full_cleanup_file_failure_can_be_retried(self):
        ann, bob, thread, reply = self.sample()
        with patch.object(ann.avatar.storage, "delete", side_effect=OSError("Unavailable storage")):
            self.assertEqual(self.remove("testaccount").status_code, 302)
        self.assertFalse(TestDataObject.objects.exists())
        self.assertTrue(TestDataFile.objects.filter(pending_delete=True).exists())
        self.assertTrue(ann.avatar.storage.exists(ann.avatar.name))
        self.assertEqual(self.remove("testaccount").status_code, 302)
        self.assertFalse(TestDataFile.objects.exists())
        self.assertFalse(ann.avatar.storage.exists(ann.avatar.name))

    def test_nested_reply_and_votes_recount_only_surviving_test_content(self):
        from .models import Vote
        ann, bob, thread, reply = self.sample()
        child = tools.create_reply(ann, thread, parent=reply, body="Nested test reply")
        services.set_vote(ann, reply, True)
        tools.register(Vote.objects.get(reply=reply), tools.admin_run())
        services.set_vote(bob, thread, True)
        tools.register(Vote.objects.get(thread=thread), tools.admin_run())
        self.assertEqual(self.remove("testreply", reply.pk).status_code, 302)
        self.assertFalse(Reply.objects.filter(pk__in=[reply.pk, child.pk]).exists())
        thread.refresh_from_db()
        self.assertEqual((thread.reply_count, thread.score), (0, 1))
        self.assertEqual(self.remove("testaccount", bob.pk).status_code, 302)
        thread.refresh_from_db()
        self.assertEqual(thread.score, 0)
        self.assertTrue(User.objects.filter(pk=ann.pk).exists())

    def test_shared_file_and_external_vote_block_deletion(self):
        ann, bob, thread, reply = self.sample()
        self.real.avatar = ann.avatar.name
        self.real.save(update_fields=["avatar"])
        self.assertContains(self.remove("testaccount", ann.pk), "Shared file")
        self.real.avatar = ""
        self.real.save(update_fields=["avatar"])
        services.set_vote(self.real, thread, True)
        self.assertContains(self.remove("testthread", thread.pk), "Нетестова залежність")
        self.assertTrue(Thread.objects.filter(pk=thread.pk).exists())

    def test_confirmation_requires_csrf_and_signed_selection(self):
        from django.test import Client
        ann, bob, thread, reply = self.sample()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.boss)
        url = self.admin_url("testaccount_cleanup")
        self.assertEqual(client.post(url, {"confirm": "yes"}).status_code, 403)
        self.assertEqual(self.client.post(url, {"confirm": "yes", "selection": "forged"}).status_code, 403)
        self.assertTrue(User.objects.filter(pk=ann.pk).exists())

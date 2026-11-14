"""Support email through SMTP (POLISH3 stage 5a), with smtplib mocked: nothing leaves the machine.

The notice goes through the real SMTP backend (TLS, login, send); a refused login or a dead server never loses the
saved message; `send_test_email` prints the settings without the password and explains failures; production gets
a system check warning and the admin inbox a banner when mail cannot arrive.
"""
import smtplib
import time
from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from projects.tests import make_user

from . import antispam
from .checks import support_email_check
from .mailcheck import email_problems
from .models import SupportMessage

SECRET = "abcdefghijklmnop"
GMAIL = {
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": "smtp.gmail.com", "EMAIL_PORT": 587, "EMAIL_USE_TLS": True,
    "EMAIL_HOST_USER": "sender@example.com", "EMAIL_HOST_PASSWORD": SECRET,
    "DEFAULT_FROM_EMAIL": "Shipmark <sender@example.com>", "SUPPORT_INBOX_EMAIL": "inbox@example.com",
}


def mock_smtp():
    """Patches smtplib.SMTP as Django's backend uses it; returns (patcher, server mock)."""
    patcher = mock.patch("django.core.mail.backends.smtp.smtplib.SMTP")
    server = patcher.start().return_value
    server.sendmail.return_value = {}
    return patcher, server


@override_settings(**GMAIL)
class SmtpNoticeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.patcher, self.server = mock_smtp()
        self.addCleanup(self.patcher.stop)

    def send_form(self):
        data = {"category": "bug", "subject": "Badge", "body": "The badge shows the wrong date since yesterday.",
                "email": "ann@example.com", "started": antispam.issue_token(time.time() - 10)}
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post("/support/", data, REMOTE_ADDR="203.0.113.5")

    def test_notice_goes_through_tls_login_and_send(self):
        self.assertEqual(self.send_form().status_code, 302)
        self.server.starttls.assert_called_once()
        self.server.login.assert_called_once_with("sender@example.com", SECRET)
        sender, recipients, raw = self.server.sendmail.call_args.args
        self.assertIn("sender@example.com", sender)
        self.assertEqual(recipients, ["inbox@example.com"])
        self.assertIn(b"Reply-To: ann@example.com", raw)

    def test_refused_login_keeps_the_message_and_logs_without_secrets(self):
        self.server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")
        with self.assertLogs("support.notify", level="ERROR") as logs:
            response = self.send_form()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SupportMessage.objects.count(), 1)
        self.assertIn("SMTPAuthenticationError", logs.output[0])
        self.assertNotIn(SECRET, "\n".join(logs.output))

    def test_dead_server_keeps_the_message(self):
        with mock.patch("django.core.mail.backends.smtp.smtplib.SMTP", side_effect=ConnectionRefusedError()):
            with self.assertLogs("support.notify", level="ERROR"):
                response = self.send_form()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SupportMessage.objects.count(), 1)

    @override_settings(SUPPORT_INBOX_EMAIL="")
    def test_no_inbox_is_logged_not_silent(self):
        with self.assertLogs("support.notify", level="WARNING") as logs:
            self.send_form()
        self.assertIn("SUPPORT_INBOX_EMAIL is empty", logs.output[0])
        self.server.sendmail.assert_not_called()
        self.assertEqual(SupportMessage.objects.count(), 1)


@override_settings(**GMAIL)
class SendTestEmailTests(TestCase):
    def setUp(self):
        self.patcher, self.server = mock_smtp()
        self.addCleanup(self.patcher.stop)

    def run_command(self, *args):
        out = StringIO()
        call_command("send_test_email", *args, stdout=out)
        return out.getvalue()

    def test_sends_to_the_inbox_and_hides_the_password(self):
        out = self.run_command()
        self.assertIn("Sent to inbox@example.com", out)
        self.assertIn("(set, hidden)", out)
        self.assertNotIn(SECRET, out)
        self.assertEqual(self.server.sendmail.call_args.args[1], ["inbox@example.com"])

    def test_refused_login_is_explained_without_the_password(self):
        self.server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")
        with self.assertRaises(CommandError) as raised:
            self.run_command()
        self.assertIn("app password", str(raised.exception))
        self.assertNotIn(SECRET, str(raised.exception))

    def test_no_recipient_or_bad_address(self):
        with override_settings(SUPPORT_INBOX_EMAIL=""), self.assertRaises(CommandError):
            self.run_command()
        with self.assertRaises(CommandError):
            self.run_command("--to", "not an address")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_console_backend_says_it_does_not_reach_the_mailbox_and_smtp_flag_uses_smtp(self):
        with mock.patch("sys.stdout", new_callable=StringIO):  # the console backend prints the email itself
            out = self.run_command()
        self.assertIn("does not reach inbox@example.com", out)
        self.server.sendmail.assert_not_called()
        self.assertIn("Sent to", self.run_command("--smtp"))
        self.server.sendmail.assert_called_once()


class EmailWarningTests(TestCase):
    @override_settings(**GMAIL)
    def test_complete_gmail_setup_has_no_problems(self):
        self.assertEqual(email_problems(), [])
        with override_settings(DEBUG=False):
            self.assertEqual(support_email_check(None), [])

    @override_settings(DEBUG=False, EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="localhost",
                       EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="", SUPPORT_INBOX_EMAIL="",
                       DEFAULT_FROM_EMAIL="webmaster@localhost")
    def test_production_without_smtp_config_warns(self):
        warnings = support_email_check(None)
        text = " ".join(w.msg for w in warnings)
        self.assertEqual(len(warnings), 3)
        self.assertIn("SUPPORT_INBOX_EMAIL", text)
        self.assertIn("EMAIL_HOST", text)
        self.assertIn("DEFAULT_FROM_EMAIL", text)
        with override_settings(DEBUG=True):
            self.assertEqual(support_email_check(None), [])  # dev prints emails on purpose

    @override_settings(**{**GMAIL, "EMAIL_HOST_PASSWORD": ""})
    def test_login_without_password(self):
        self.assertTrue(any("EMAIL_HOST_PASSWORD is empty" in p for p in email_problems()))

    @override_settings(SUPPORT_INBOX_EMAIL="", EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_admin_inbox_shows_a_banner(self):
        boss = type(make_user("x")).objects.create_superuser("boss", "boss@example.com", "pw")
        self.client.force_login(boss)
        response = self.client.get(reverse("admin:support_supportmessage_changelist"))
        self.assertContains(response, "New messages do not reach the support mailbox")
        with override_settings(**GMAIL):
            response = self.client.get(reverse("admin:support_supportmessage_changelist"))
        self.assertNotContains(response, "New messages do not reach the support mailbox")

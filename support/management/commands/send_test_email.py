"""Команда send_test_email: тестовий лист і пояснення, що не так з поштою.

`python manage.py send_test_email [--to ADDRESS] [--smtp]`: send one test email the way the support notice is sent,
print the settings in use (the password only as set / not set) and say in plain words what is wrong when it fails.

--smtp uses the SMTP backend even when the settings say console (dev): to try the real Gmail setup from a laptop.
Exit code 1 when the email was not handed to the mail server.
"""
import smtplib
import socket
import ssl

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.utils import timezone

from config import branding
from support.mailcheck import LOCAL_BACKENDS, SMTP_BACKEND, describe, email_problems

# What each failure usually means, most specific first.
HINTS = (
    (smtplib.SMTPAuthenticationError, "The server refused the login. Gmail: EMAIL_HOST_USER must be the full address and "
                                      "EMAIL_HOST_PASSWORD a 16-letter app password (needs 2-step verification), "
                                      "not the account password."),
    (smtplib.SMTPSenderRefused, "The server refused the sender. DEFAULT_FROM_EMAIL must be the sending account's address."),
    (smtplib.SMTPRecipientsRefused, "The server refused the recipient address."),
    (smtplib.SMTPNotSupportedError, "The server does not support this. Port 587 needs EMAIL_USE_TLS=true."),
    (ssl.SSLError, "TLS failed. Gmail: EMAIL_PORT=587 with EMAIL_USE_TLS=true."),
    (socket.gaierror, "The host name does not resolve. Check EMAIL_HOST (Gmail: smtp.gmail.com)."),
    (ConnectionRefusedError, "Nothing answers on that host and port. Check EMAIL_HOST and EMAIL_PORT."),
    (TimeoutError, "No answer in time. Check EMAIL_PORT (587) and whether the server's firewall allows outgoing SMTP."),
    (smtplib.SMTPServerDisconnected, "The server closed the connection. Check EMAIL_PORT and EMAIL_USE_TLS."),
)


class Command(BaseCommand):
    """Надсилає тестовий лист і пояснює помилки."""
    help = "Send a test email like the support notice and explain what is wrong when it fails."

    def add_arguments(self, parser):
        parser.add_argument("--to", default="", help="Recipient (default: SUPPORT_INBOX_EMAIL).")
        parser.add_argument("--smtp", action="store_true", help="Use SMTP even when EMAIL_BACKEND is the console (dev).")

    def handle(self, *args, to="", smtp=False, **options):
        backend = SMTP_BACKEND if smtp else settings.EMAIL_BACKEND
        self.stdout.write("Email settings in use:")
        for line in describe(backend):
            self.stdout.write(f"  {line}")

        problems = email_problems(backend)
        for problem in problems:
            self.stdout.write(self.style.WARNING(f"! {problem}"))

        to = to or settings.SUPPORT_INBOX_EMAIL
        if not to:
            raise CommandError("No recipient: pass --to ADDRESS or set SUPPORT_INBOX_EMAIL.")
        try:
            validate_email(to)
        except ValidationError:
            raise CommandError(f"Not an email address: {to!r}") from None

        stamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        email = EmailMessage(
            subject=f"[{branding.SITE_NAME} support] Test email",
            body=f"This is a test from `manage.py send_test_email` ({stamp}).\n"
                 "If you can read it, support notices reach this mailbox.",
            from_email=settings.DEFAULT_FROM_EMAIL, to=[to],
            connection=get_connection(backend, fail_silently=False),
        )
        try:
            email.send(fail_silently=False)
        except Exception as error:  # noqa: BLE001 - every failure is explained, none is a crash
            hint = next((text for kind, text in HINTS if isinstance(error, kind)), "See the error above.")
            raise CommandError(f"Not sent: {type(error).__name__}: {error}\n{hint}") from None

        if backend in LOCAL_BACKENDS:
            self.stdout.write(self.style.WARNING(
                f"Handed to the {backend.rsplit('.', 2)[-2]} backend, which {LOCAL_BACKENDS[backend]}: it does not reach "
                f"{to}. To try the real mailbox from here: fill the EMAIL_* values in .env and add --smtp."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Sent to {to}. Check the inbox (and the spam folder) in a minute."))

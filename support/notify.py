"""The plain-text email to the support inbox about a new message. Best effort: it runs after the commit, so the
message is saved even when sending fails (the failure is logged without the message text).

No attachments and no HTML: the email says that a message arrived and links to the admin, where staff read it.
The subject is built from our own words and the category; the person's subject goes in the body, so nothing a
visitor typed can reach a mail header. Reply-To is the address the form validated (EmailField refuses line breaks).
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import translation

from config import branding
from config.site import absolute_url

from .models import SupportMessage

logger = logging.getLogger(__name__)


def build_email(message):
    with translation.override("en"):
        category = str(message.get_category_display())
        subject = f"[{branding.SITE_NAME} support] {category} #{message.pk}"
        admin_link = absolute_url(reverse("admin:support_supportmessage_change", args=[message.pk]))
        lines = [
            f"New support message #{message.pk} ({category}).",
            "",
            f"From: {message.email}" + (f" (@{message.user.username})" if message.user_id else " (not signed in)"),
            f"Subject: {message.subject or '-'}",
            f"Reference: {message.reference or '-'}",
            f"Attachments: {message.attachments.count()} (open them in the admin)",
            "",
            message.body,
            "",
            f"Open in the admin: {admin_link}",
            "Reply to this email to answer the person directly.",
        ]
    return EmailMessage(
        subject=subject, body="\n".join(lines), from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.SUPPORT_INBOX_EMAIL], reply_to=[message.email],
    )


def notify_inbox(message_id):
    """Returns True when the email was handed to the mail server. Never raises."""
    if not settings.SUPPORT_INBOX_EMAIL:
        return False
    try:
        message = SupportMessage.objects.select_related("user").get(pk=message_id)
        build_email(message).send(fail_silently=False)
        return True
    except Exception as error:  # noqa: BLE001 - a mail problem must never lose the message or break the page
        logger.error("support notification failed for message %s: %s", message_id, type(error).__name__)
        return False

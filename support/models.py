"""Звернення з /support/ без IP і даних браузера.

Messages sent through /support/. No IP address and no browser details are stored (docs/DATA_INVENTORY.md)."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .storage import private_storage

MIN_BODY = 10
MAX_BODY = 4000
MAX_SUBJECT = 120
MAX_ATTACHMENTS = 3


class SupportMessage(models.Model):
    """Звернення в підтримку."""
    class Category(models.TextChoices):
        BUG = "bug", _("Bug")
        IDEA = "idea", _("Idea or feedback")
        PRAISE = "praise", _("Praise")
        ACCOUNT = "account", _("Account or privacy")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        NEW = "new", _("New")
        READ = "read", _("Read")
        ANSWERED = "answered", _("Answered")
        CLOSED = "closed", _("Closed")

    # Deleted with the account (accounts/deletion.py also deletes messages sent signed out from the same address).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="support_messages",
    )
    email = models.EmailField(_("email"), help_text=_("Used only to reply."))
    category = models.CharField(_("category"), max_length=10, choices=Category.choices)
    subject = models.CharField(_("subject"), max_length=MAX_SUBJECT, blank=True)
    body = models.TextField(_("message"), max_length=MAX_BODY)
    # The request id from an error page ("Report a problem"), so staff can find the error log line.
    reference = models.CharField(_("reference"), max_length=32, blank=True)
    status = models.CharField(_("status"), max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)
    internal_note = models.TextField(_("internal note"), blank=True, help_text=_("Only staff see this."))
    created_at = models.DateTimeField(_("sent"), default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("support message")
        verbose_name_plural = _("support messages")

    def __str__(self):
        return (self.subject or self.body)[:80]


def attachment_path(instance, filename):
    """Випадкова назва файлу вкладення.

    Random name; the extension comes from what the file became (webp or txt), never from the upload."""
    now = timezone.now()
    extension = "txt" if instance.kind == SupportAttachment.Kind.TEXT else "webp"
    return f"{now:%Y}/{now:%m}/{uuid.uuid4().hex}.{extension}"


class SupportAttachment(models.Model):
    """Вкладення до звернення (у приватному сховищі)."""
    class Kind(models.TextChoices):
        IMAGE = "image", _("Image")
        TEXT = "text", _("Text")

    message = models.ForeignKey(SupportMessage, on_delete=models.CASCADE, related_name="attachments")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    file = models.FileField(upload_to=attachment_path, storage=private_storage, max_length=200)
    name = models.CharField(_("original name"), max_length=100, blank=True)  # cleaned, for staff only
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pk"]
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    def __str__(self):
        return self.name or self.file.name

    @property
    def download_name(self):
        stem = self.name.rsplit(".", 1)[0] if self.name else f"attachment-{self.pk}"
        return f"{stem or 'attachment'}.{'txt' if self.kind == self.Kind.TEXT else 'webp'}"

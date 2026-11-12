from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

MAX_DETAILS = 1000


class AuditLog(models.Model):
    """Append-only record of important changes: hallmarks, moderation, account deletion.

    `target_type` + `target_id` instead of a foreign key, so entries survive when the target is deleted.
    `target_repr` keeps a readable name for the same reason.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )  # None: the system (a cron command)
    action = models.CharField(max_length=60, db_index=True)  # e.g. "hallmark.live.earned"
    target_type = models.CharField(max_length=40)  # e.g. "projects.project"
    target_id = models.CharField(max_length=40)
    target_repr = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id"])]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action} {self.target_repr}"


class Report(models.Model):
    """A signed-in user's report about a project or a profile. Handled in the admin.

    The target is `project` or `target_user` (never both). Both are SET_NULL, so the report survives
    when the target is deleted, and `target_repr` keeps a readable name. When the reporter deletes their
    account the report is kept but anonymized (reporter becomes empty).
    """

    class Reason(models.TextChoices):
        SPAM = "spam", _("Spam or advertising")
        FAKE_PROOF = "fake_proof", _("Fake or misleading proof")
        IMPERSONATION = "impersonation", _("Impersonation")
        INAPPROPRIATE = "inappropriate", _("Offensive or illegal content")
        COPYRIGHT = "copyright", _("Copyright or stolen work")
        OTHER = "other", _("Something else")

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        RESOLVED = "resolved", _("Resolved")

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports_made",
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="reports",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports_received",
    )
    target_repr = models.CharField(max_length=200)
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True, max_length=MAX_DETAILS)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    handled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(project__isnull=True) | models.Q(target_user__isnull=True),
                name="report_one_target",
            ),
            # One open report per person and target: repeating it adds nothing but noise.
            models.UniqueConstraint(
                fields=["reporter", "project"], condition=models.Q(status="open"), name="one_open_report_per_project",
            ),
            models.UniqueConstraint(
                fields=["reporter", "target_user"], condition=models.Q(status="open"), name="one_open_report_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.get_reason_display()}: {self.target_repr}"

    @property
    def target(self):
        return self.project or self.target_user


class SanctionQuerySet(models.QuerySet):
    def active(self, now=None):
        """In force right now: started, not expired, not revoked. Evaluated per request; no cron needed."""
        now = now or timezone.now()
        return self.filter(revoked_at__isnull=True, starts_at__lte=now).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now),
        )


class Sanction(models.Model):
    """A mute or a ban. The reason is shown to the user, with the end date and the appeals contact.

    Mute: can read and use own settings, export and delete; cannot create, edit, publish, log, like,
    follow, report or upload. Ban: cannot sign in; projects hidden from public lists while it lasts.
    expires_at None = permanent (superusers only). A sanction is never deleted: it is revoked, so the
    history stays (also in AuditLog).
    """

    class Kind(models.TextChoices):
        MUTE = "mute", _("Mute")
        BAN = "ban", _("Ban")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sanctions")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    reason = models.TextField(max_length=MAX_DETAILS, help_text=_("Shown to the user."))
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True, help_text=_("Empty: permanent (superusers only)."))
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.SET_NULL, related_name="sanctions")
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    objects = SanctionQuerySet.as_manager()

    class Meta:
        ordering = ["-starts_at", "-pk"]
        indexes = [models.Index(fields=["user", "kind"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(expires_at__isnull=True) | Q(expires_at__gt=models.F("starts_at")),
                name="sanction_ends_after_it_starts",
            ),
        ]
        verbose_name = _("sanction")
        verbose_name_plural = _("sanctions")

    def __str__(self):
        return f"{self.get_kind_display()}: {self.user}"

    @property
    def is_permanent(self):
        return self.expires_at is None

    def is_active(self, now=None):
        now = now or timezone.now()
        return (self.revoked_at is None and self.starts_at <= now
                and (self.expires_at is None or self.expires_at > now))

    def state(self, now=None):
        """"active", "scheduled", "expired" or "revoked" (for lists)."""
        now = now or timezone.now()
        if self.revoked_at is not None:
            return "revoked"
        if self.starts_at > now:
            return "scheduled"
        if self.expires_at is not None and self.expires_at <= now:
            return "expired"
        return "active"

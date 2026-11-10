from django.conf import settings
from django.db import models
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

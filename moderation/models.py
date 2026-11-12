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


OPEN_STATES = ("open", "in_review")  # a report that still needs a decision


class Report(models.Model):
    """A report about a project, a profile or a build-log entry. Handled in /mod/ and the admin.

    The target is one of `project`, `target_user`, `log_entry` (never two). They are SET_NULL, so the report
    survives when the target is deleted, and `target_repr` keeps a readable name. `target_owner` is the person
    the report is about (for their history). The reporter is shown only to moderators and staff, never to
    the reported person. When the reporter deletes their account the report is kept but anonymized.
    `source` is "moderator" when a moderator acted while browsing (one history for everything).
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
        IN_REVIEW = "in_review", _("In review")
        RESOLVED = "resolved", _("Resolved")  # action taken
        DISMISSED = "dismissed", _("Dismissed")  # no action

    class Source(models.TextChoices):
        USER = "user", _("User report")
        MODERATOR = "moderator", _("Moderator")

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports_made",
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="reports",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports_received",
    )
    log_entry = models.ForeignKey(
        "projects.BuildLogEntry", null=True, blank=True, on_delete=models.SET_NULL, related_name="reports",
    )
    target_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports_about",
    )
    target_repr = models.CharField(max_length=200)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.USER)
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True, max_length=MAX_DETAILS)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    handled_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True, default="", max_length=MAX_DETAILS)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(project__isnull=True) & Q(target_user__isnull=True))
                | (Q(project__isnull=True) & Q(log_entry__isnull=True))
                | (Q(target_user__isnull=True) & Q(log_entry__isnull=True)),
                name="report_one_target",
            ),
            # One open report per person and target: repeating it adds nothing but noise.
            models.UniqueConstraint(
                fields=["reporter", "project"], condition=Q(status__in=OPEN_STATES), name="one_open_report_per_project",
            ),
            models.UniqueConstraint(
                fields=["reporter", "target_user"], condition=Q(status__in=OPEN_STATES), name="one_open_report_per_user",
            ),
            models.UniqueConstraint(
                fields=["reporter", "log_entry"], condition=Q(status__in=OPEN_STATES), name="one_open_report_per_entry",
            ),
        ]

    def __str__(self):
        return f"{self.get_reason_display()}: {self.target_repr}"

    @property
    def target(self):
        return self.project or self.target_user or self.log_entry

    @property
    def kind(self):
        """"project", "profile" or "entry" ("" when the target is gone)."""
        if self.project_id:
            return "project"
        if self.target_user_id:
            return "profile"
        if self.log_entry_id:
            return "entry"
        return ""

    @property
    def is_open(self):
        return self.status in OPEN_STATES


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


class BannedIdentity(models.Model):
    """Stops a banned person from deleting the account and signing up again with the same GitHub account.

    Only a keyed hash of the GitHub user id is kept (HMAC-SHA256 with settings.BAN_HASH_KEY, see moderation/bans.py),
    never the id itself, and only until the ban ends: rows past `expires_at` are deleted when bans are checked and by
    `manage.py prune_bans`. `expires_at` None = permanent ban. The reason and the end date are kept so a refused
    signup sees the same ban page.

    `hash_scheme` "secret_key" marks hashes made before BAN_HASH_KEY existed (keyed from SECRET_KEY); `rehash_bans`
    converts those whose account still exists. They are only looked up while such rows exist.
    """

    class HashScheme(models.TextChoices):
        BAN_KEY = "ban_key", "BAN_HASH_KEY"  # plain labels: a technical field, shown only in the admin
        SECRET_KEY = "secret_key", "SECRET_KEY (old)"

    identity_hash = models.CharField(max_length=64, db_index=True)
    hash_scheme = models.CharField(max_length=10, choices=HashScheme.choices, default=HashScheme.SECRET_KEY)
    sanction = models.ForeignKey(Sanction, null=True, blank=True, on_delete=models.SET_NULL, related_name="identities")
    reason = models.TextField(max_length=MAX_DETAILS)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("banned identity")
        verbose_name_plural = _("banned identities")

    def __str__(self):
        return f"{self.identity_hash[:12]}…"


class Notice(models.Model):
    """An in-app message about a moderation decision, shown at the top of every page until dismissed.

    Mutes and bans are not notices: they are shown from the Sanction itself (banner, ban page). The reporter
    is never named in a notice.
    """

    class Kind(models.TextChoices):
        PROJECT_REMOVED = "project_removed", _("Project removed")
        PROJECT_RESTORED = "project_restored", _("Project restored")
        PROFILE_CLEARED = "profile_cleared", _("Profile fields cleared")
        REPORT_DISMISSED = "report_dismissed", _("Report reviewed, no action")
        REPORT_ACTIONED = "report_actioned", _("Report reviewed, action taken")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notices")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    target_repr = models.CharField(max_length=200)
    reason = models.TextField(blank=True, default="", max_length=MAX_DETAILS)
    created_at = models.DateTimeField(auto_now_add=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "dismissed_at"])]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.target_repr}"

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class RepoLink(models.Model):
    """A GitHub repository that passed the Repo owner check for a project.

    Rows exist only for repositories that passed: owned by the user and not a fork. A failed check is
    never stored, so nobody can block someone else's repository by claiming it (CLAUDE.md section 2).
    A passed link earns the mark unless it waits for a review (`review_state`).
    """

    class Review(models.TextChoices):
        CLEAR = "", "Clear"
        NEEDS_REVIEW = "needs_review", "Needs review"  # a fact in review_reasons; staff decides
        NEEDS_RECHECK = "needs_recheck", "Needs re-check"  # passed under older rules; checked again
        APPROVED = "approved", "Approved"  # staff looked at the reasons and approved

    project = models.OneToOneField("projects.Project", on_delete=models.CASCADE, related_name="repo_link")
    repo_full_name = models.CharField(max_length=140)  # as GitHub spells it: "owner/repo"
    github_repo_id = models.BigIntegerField(unique=True)  # does not change when the repo is renamed
    # The account that owns the repository on GitHub. Changes only on a transfer. Empty: not backfilled yet.
    github_owner_id = models.BigIntegerField(null=True, blank=True)
    is_owner = models.BooleanField(default=False)  # a personal, non-fork repo owned by the user
    user_commit_count = models.PositiveIntegerField(default=0)
    first_commit_at = models.DateTimeField(null=True, blank=True)
    last_commit_at = models.DateTimeField(null=True, blank=True)
    repo_created_at = models.DateTimeField(null=True, blank=True)  # on GitHub
    root_commit_sha = models.CharField(max_length=40, blank=True, db_index=True)  # oldest commit, default branch
    root_commit_at = models.DateTimeField(null=True, blank=True)  # its author date, as written in the commit
    active_weeks = models.PositiveIntegerField(null=True, blank=True)  # None: GitHub statistics not ready yet
    stats_checked_at = models.DateTimeField(null=True, blank=True)
    review_state = models.CharField(max_length=16, choices=Review.choices, default="", blank=True, db_index=True)
    review_reasons = models.JSONField(default=list, blank=True)  # codes from verification/repo.py
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    checked_at = models.DateTimeField()  # latest successful check
    # First successful check. A failed check deletes the row, so this is when the current Authored began.
    earned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            # GitHub names are case-insensitive: Octo/Repo and octo/repo are the same repository.
            models.UniqueConstraint(Lower("repo_full_name"), name="unique_repolink_name_ci"),
        ]

    def __str__(self):
        return self.repo_full_name

    @property
    def is_verified(self):
        """Earns Repo owner: the repository passed and is not waiting for a review or re-check."""
        return self.is_owner and self.review_state in (self.Review.CLEAR, self.Review.APPROVED)


class DomainVerification(models.Model):
    """Proof that the project owner controls the domain of the project's live URL (the Live hallmark).

    One row per project + domain, with its own random token. A new domain gets a new row and token,
    so tokens are never reused. Only verified rows block the domain for other projects.
    """

    class Method(models.TextChoices):
        DNS = "dns", "DNS TXT"
        META = "meta", "Meta tag"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"  # created, not proven yet
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"  # was verified, a later check did not find the token

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="domain_verifications")
    domain = models.CharField(max_length=253)  # exact host, lowercase, punycode: "www.example.com"
    domain_key = models.CharField(max_length=253)  # for comparison, without "www.": "example.com"
    method = models.CharField(max_length=4, choices=Method.choices, default=Method.DNS)
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)  # first success
    last_confirmed_at = models.DateTimeField(null=True, blank=True)  # latest success
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=40, blank=True)  # error code from verification/domain.py

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "domain_key"], name="unique_domain_per_project"),
            # One verified domain, one project. Partial unique index: works on SQLite and PostgreSQL.
            models.UniqueConstraint(
                fields=["domain_key"], condition=models.Q(status="verified"), name="unique_verified_domain",
            ),
        ]

    def __str__(self):
        return f"{self.domain} ({self.status})"


class UptimeCheck(models.Model):
    """One request to a Live project's URL (the Steady hallmark). Kept for 90 days.

    Written only by `check_uptime`, at most once per project per 3 hours (verification/uptime.py).
    """

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="uptime_checks")
    checked_at = models.DateTimeField()
    ok = models.BooleanField()  # an HTTP answer with status < 400
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)  # None: no HTTP answer at all
    response_ms = models.PositiveIntegerField(null=True, blank=True)
    error = models.CharField(max_length=40, blank=True)  # FetchError code when there was no answer

    class Meta:
        indexes = [
            models.Index(fields=["project", "checked_at"], name="uptime_project_time"),
            models.Index(fields=["checked_at"], name="uptime_time"),  # pruning
        ]

    def __str__(self):
        return f"{self.project_id} {self.checked_at:%Y-%m-%d %H:%M} {'ok' if self.ok else 'down'}"

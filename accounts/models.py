"""Моделі акаунтів: User, бейджі, посилання профілю, закріплені проєкти."""
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .usernames import MAX_LENGTH, validate_username


def avatar_path(instance, filename):
    """Випадкова назва файлу для аватарки чи обкладинки.

    Random file name: the uploaded name (which the user controls) is never used."""
    return f"avatars/{uuid.uuid4().hex}.webp"


def cover_path(instance, filename):
    return f"covers/{uuid.uuid4().hex}.webp"


class User(AbstractUser):
    """Користувач Shipmark: профіль, мова, згода з умовами, призупинення."""
    class Status(models.TextChoices):
        # The empty value means "no status": nothing is shown on the profile.
        OPEN_TO_WORK = "open_to_work", _("Open to work")
        OPEN_TO_COLLABORATE = "open_to_collaborate", _("Open to collaborate")
        HIRING = "hiring", _("Hiring")
        BUILDING_IN_PUBLIC = "building_in_public", _("Building in public")

    class AvatarSource(models.TextChoices):
        NONE = "", _("Initials")
        UPLOAD = "upload", _("Uploaded")
        GITHUB = "github", _("From GitHub")

    # Lowercase, URL-safe, not reserved (see usernames.py). Replaces Django's default rules.
    username = models.CharField(
        max_length=MAX_LENGTH,
        unique=True,
        validators=[validate_username],
        error_messages={"unique": _("This username is already taken.")},
    )
    display_name = models.CharField(max_length=80, blank=True)
    # Deprecated since the profile rework: copied to `about` and to a website ProfileLink by migration 0006.
    # Nothing reads or writes them any more; a later migration drops both columns.
    bio = models.CharField(max_length=280, blank=True, editable=False)
    website = models.URLField(blank=True, editable=False)
    headline = models.CharField(max_length=80, blank=True)
    about = models.TextField(max_length=1000, blank=True)  # limited markdown, rendered and sanitized on display
    location = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=20, blank=True, choices=Status.choices)
    skills = models.ManyToManyField("projects.Tag", blank=True, related_name="skilled_users")
    # Pictures are always files on our disk (re-encoded WebP, random names), never hotlinked.
    avatar = models.ImageField(upload_to=avatar_path, blank=True)
    avatar_source = models.CharField(max_length=10, blank=True, choices=AvatarSource.choices)
    cover = models.ImageField(upload_to=cover_path, blank=True)
    github_login = models.CharField(max_length=39, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    preferred_language = models.CharField(max_length=10, blank=True, choices=settings.LANGUAGES)
    terms_version_accepted = models.CharField(max_length=20, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)
    # Set when someone replies to this person in the community; cleared when they open their notifications.
    # Read from request.user, so the "new replies" mark in the header costs no query on any page.
    community_notified_at = models.DateTimeField(null=True, blank=True, editable=False)
    # The one system account (the official "shipmark" author of news and community notices), set by migration
    # 0008. A stable mark, not the username: it has no public profile, cannot be followed and is not counted.
    is_system_account = models.BooleanField(default=False, editable=False)

    class Meta:
        constraints = [
            # One Shipmark account per GitHub account; many users may have it empty.
            models.UniqueConstraint(
                fields=["github_login"],
                condition=~Q(github_login=""),
                name="unique_github_login_when_set",
            ),
            models.UniqueConstraint(
                fields=["is_system_account"], condition=Q(is_system_account=True), name="one_system_account",
            ),
        ]

    def __str__(self):
        return self.username


class UserBadge(models.Model):
    """Бейдж біля імені (official, moderator); видає лише суперкористувач.

    A mark next to a person's name. Granted and revoked only by superusers (admin or `grant_badge`).

    Official: "Official Shipmark account", gives no permissions. Moderator: the only source of the
    moderation permission (`accounts.roles.can_moderate`), never `is_staff`. Every change is in AuditLog.
    """

    class Kind(models.TextChoices):
        OFFICIAL = "official", _("Official")
        MODERATOR = "moderator", _("Moderator")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )  # None: a migration or the command
    granted_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["kind"]
        constraints = [models.UniqueConstraint(fields=["user", "kind"], name="one_badge_of_a_kind_per_user")]
        verbose_name = _("badge")
        verbose_name_plural = _("badges")

    def __str__(self):
        return f"{self.user} · {self.get_kind_display()}"


class ProfileLink(models.Model):
    """Посилання в профілі (до шести).

    Up to 6 links on a profile. http(s) only; GitHub, X, LinkedIn and Telegram must point to their own sites
    (accounts/links.py), so an icon never leads somewhere else. Shown with rel="nofollow ugc noopener"."""

    class Kind(models.TextChoices):
        WEBSITE = "website", _("Website")
        GITHUB = "github", _("GitHub")
        X = "x", _("X")
        LINKEDIN = "linkedin", _("LinkedIn")
        TELEGRAM = "telegram", _("Telegram")
        OTHER = "other", _("Other")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="links")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.WEBSITE)
    url = models.URLField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("profile link")
        verbose_name_plural = _("profile links")

    def __str__(self):
        return f"{self.user} · {self.get_kind_display()}"


class PinnedProject(models.Model):
    """Закріплений проєкт у профілі (до трьох).

    Up to 3 of a person's own published projects, shown first on the profile."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pins")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="pins")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [models.UniqueConstraint(fields=["user", "project"], name="one_pin_per_project")]
        verbose_name = _("pinned project")
        verbose_name_plural = _("pinned projects")

    def __str__(self):
        return f"{self.user} · {self.project}"

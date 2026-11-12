from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .usernames import MAX_LENGTH, validate_username


class User(AbstractUser):
    # Lowercase, URL-safe, not reserved (see usernames.py). Replaces Django's default rules.
    username = models.CharField(
        max_length=MAX_LENGTH,
        unique=True,
        validators=[validate_username],
        error_messages={"unique": _("This username is already taken.")},
    )
    display_name = models.CharField(max_length=80, blank=True)
    bio = models.CharField(max_length=280, blank=True)
    website = models.URLField(blank=True)
    github_login = models.CharField(max_length=39, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    preferred_language = models.CharField(max_length=10, blank=True, choices=settings.LANGUAGES)
    terms_version_accepted = models.CharField(max_length=20, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # One Shipmark account per GitHub account; many users may have it empty.
            models.UniqueConstraint(
                fields=["github_login"],
                condition=~Q(github_login=""),
                name="unique_github_login_when_set",
            ),
        ]

    def __str__(self):
        return self.username


class UserBadge(models.Model):
    """A mark next to a person's name. Granted and revoked only by superusers (admin or `grant_badge`).

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

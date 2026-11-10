from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
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

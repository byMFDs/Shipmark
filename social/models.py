"""Моделі підписок і вподобань."""
from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Follow(models.Model):
    """Підписка однієї людини на іншу."""
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_set")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_set")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_pair"),
            # Nobody follows themselves, even if a view forgets to check.
            models.CheckConstraint(condition=~Q(follower=F("following")), name="no_self_follow"),
        ]

    def __str__(self):
        return f"{self.follower_id} -> {self.following_id}"


class Like(models.Model):
    """Вподобання проєкту."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "project"], name="unique_like_pair"),
        ]

    def __str__(self):
        return f"{self.user_id} likes {self.project_id}"

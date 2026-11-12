"""Community: boards, threads, replies (three levels), images, upvotes.

Nothing is ever hard-deleted by a normal action. An author's delete wipes the text for real and sets `deleted_at`;
a moderator's removal sets `status = removed` and keeps the text for appeals (the image files go at once).
`score` and `reply_count` are denormalized: changed with F() in the same transaction as the vote or reply,
and repaired by `manage.py community_recount`.
"""
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from moderation.visibility import banned

from . import limits, stickers


def visible_author(queryset):
    """Rows whose author is not suspended or banned. A deleted account (author is NULL) stays visible."""
    return queryset.filter(Q(author__isnull=True) | Q(author__is_suspended=False)).filter(~banned("author"))


class Board(models.Model):
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text=_("Inactive boards and their threads are hidden."))

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        return gettext(self.name) if self.name else ""

    @property
    def display_description(self):
        return gettext(self.description) if self.description else ""

    def get_absolute_url(self):
        return reverse("community:board", args=[self.slug])


class ThreadQuerySet(models.QuerySet):
    def public(self):
        """What everyone may read: published or locked, on an active board, the author not hidden.
        A thread its author deleted stays only while it has replies (shown as "[deleted]")."""
        queryset = self.filter(status__in=Thread.PUBLIC_STATES, board__is_active=True)
        return visible_author(queryset.exclude(deleted_at__isnull=False, reply_count=0))


class Thread(models.Model):
    class Status(models.TextChoices):
        PUBLISHED = "published", _("Published")
        LOCKED = "locked", _("Locked")  # readable; only moderators reply
        REMOVED = "removed", _("Removed")  # by a moderator; only the author and moderators see it

    PUBLIC_STATES = (Status.PUBLISHED, Status.LOCKED)

    board = models.ForeignKey(Board, on_delete=models.PROTECT, related_name="threads")
    # NULL after the author deleted their account: the thread stays, shown as "[deleted]".
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="community_threads",
    )
    title = models.CharField(max_length=limits.MAX_TITLE)
    slug = models.SlugField(max_length=60)  # for readable URLs only; the id finds the thread
    body = models.TextField(max_length=limits.MAX_THREAD_BODY, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PUBLISHED, db_index=True)
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    edited_at = models.DateTimeField(null=True, blank=True)  # only set by an edit after the silent window
    last_activity_at = models.DateTimeField(default=timezone.now)
    score = models.IntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)  # replies that are published and not deleted
    deleted_at = models.DateTimeField(null=True, blank=True)  # by the author; the body is wiped
    removed_reason = models.TextField(blank=True, default="")
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    lock_reason = models.TextField(blank=True, default="")

    objects = ThreadQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="thread_status_new"),
            models.Index(fields=["board", "status", "-last_activity_at"], name="thread_board_active"),
            models.Index(fields=["status", "-score"], name="thread_status_top"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:60].strip("-") or "thread"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("community:thread", args=[self.pk, self.slug])

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def is_locked(self):
        return self.status == self.Status.LOCKED

    @property
    def is_removed(self):
        return self.status == self.Status.REMOVED

    @property
    def body_html(self):
        from .rendering import render_thread_body

        return render_thread_body(self.body)


class Reply(models.Model):
    class Status(models.TextChoices):
        PUBLISHED = "published", _("Published")
        REMOVED = "removed", _("Removed")

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="replies")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    # The top-level reply of this branch (NULL for a top-level reply): a page of the tree loads in one query.
    root = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    depth = models.PositiveSmallIntegerField(default=1)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="community_replies",
    )
    body = models.TextField(max_length=limits.MAX_REPLY_BODY, blank=True)
    sticker_key = models.CharField(max_length=40, blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PUBLISHED)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    removed_reason = models.TextField(blank=True, default="")
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["thread", "root", "created_at"], name="reply_thread_tree")]
        constraints = [
            models.CheckConstraint(condition=Q(depth__gte=1) & Q(depth__lte=limits.MAX_DEPTH), name="reply_depth_1_to_3"),
        ]

    def __str__(self):
        return f"#{self.pk} · {self.thread.title}"[:200]

    def get_absolute_url(self):
        return f"{self.thread.get_absolute_url()}#r{self.pk}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def is_removed(self):
        return self.status == self.Status.REMOVED

    @property
    def is_alive(self):
        """Published and not deleted: it counts in `reply_count`, accepts votes, replies and edits."""
        return self.status == self.Status.PUBLISHED and self.deleted_at is None

    @property
    def body_html(self):
        from .rendering import render_reply_body

        return render_reply_body(self.body)

    @property
    def sticker_label(self):
        return stickers.label(self.sticker_key)


def _dated(folder):
    now = timezone.now()
    return f"community/{now:%Y}/{now:%m}/{folder}{uuid.uuid4().hex}.webp"


def image_path(instance, filename):
    """Random name: the uploaded file name is never used."""
    return _dated("")


def thumb_path(instance, filename):
    return _dated("t/")


class CommunityImage(models.Model):
    """A picture on a thread or a reply: a display copy (longest side 1600) and a 640 thumbnail, both WebP,
    re-encoded by projects.images (no metadata). The files are deleted with the row (community/signals.py)."""

    thread = models.ForeignKey(Thread, null=True, blank=True, on_delete=models.CASCADE, related_name="images")
    reply = models.ForeignKey(Reply, null=True, blank=True, on_delete=models.CASCADE, related_name="images")
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="community_images",
    )
    image = models.ImageField(upload_to=image_path, width_field="width", height_field="height")
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    thumb = models.ImageField(upload_to=thumb_path, width_field="thumb_width", height_field="thumb_height")
    thumb_width = models.PositiveIntegerField(default=0)
    thumb_height = models.PositiveIntegerField(default=0)
    alt = models.CharField(max_length=limits.MAX_ALT, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(thread__isnull=False) & Q(reply__isnull=True)) | (Q(thread__isnull=True) & Q(reply__isnull=False)),
                name="community_image_one_target",
            ),
        ]

    def __str__(self):
        return self.image.name


class Vote(models.Model):
    """An upvote. There are no downvotes. Not shown in the admin: nobody browses who voted for what."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_votes")
    thread = models.ForeignKey(Thread, null=True, blank=True, on_delete=models.CASCADE, related_name="votes")
    reply = models.ForeignKey(Reply, null=True, blank=True, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(thread__isnull=False) & Q(reply__isnull=True)) | (Q(thread__isnull=True) & Q(reply__isnull=False)),
                name="community_vote_one_target",
            ),
            models.UniqueConstraint(fields=["user", "thread"], condition=Q(thread__isnull=False), name="one_vote_per_thread"),
            models.UniqueConstraint(fields=["user", "reply"], condition=Q(reply__isnull=False), name="one_vote_per_reply"),
        ]

    def __str__(self):
        return f"{self.user_id} -> {'thread' if self.thread_id else 'reply'} {self.thread_id or self.reply_id}"

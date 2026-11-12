import uuid
from functools import cached_property

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .rendering import render_user_markdown

MAX_SCREENSHOTS = 4


class Tag(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=40, unique=True, allow_unicode=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tool(models.Model):
    """An AI tool a project was built with. A fixed list (seeded by a migration), edited in the admin."""

    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=40, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        HIDDEN = "hidden", _("Hidden")  # set by moderation only (admin)
        REMOVED = "removed", _("Removed")  # by a moderator, with a reason the owner sees; superusers restore or purge

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=60)  # never changes after creation, so links stay valid
    tagline = models.CharField(max_length=120)
    description = models.TextField(blank=True, max_length=5000)  # markdown
    live_url = models.URLField(max_length=200, blank=True)
    repo_full_name = models.CharField(max_length=140, blank=True)  # "owner/repo"
    # Content of the verification file for organisation and team repositories (verification/repo.py).
    # Random, made on first use, unique: never shared with or reused by another project.
    repo_token = models.CharField(max_length=64, null=True, blank=True, unique=True, editable=False)
    tags = models.ManyToManyField(Tag, blank=True, related_name="projects")
    built_with = models.ManyToManyField(Tool, blank=True, related_name="projects")  # self-declared
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    launched_at = models.DateTimeField(null=True, blank=True)
    removed_reason = models.TextField(blank=True, default="", max_length=1000)
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "slug"], name="unique_project_slug_per_owner"),
        ]
        ordering = ["-launched_at", "-created_at"]

    def __str__(self):
        return f"{self.owner}/{self.slug}"

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.owner.username, self.slug])

    @property
    def description_html(self):
        return render_user_markdown(self.description)

    @property
    def safe_live_url(self):
        """Only http(s) links are rendered as links, whatever is stored."""
        return self.live_url if self.live_url.lower().startswith(("http://", "https://")) else ""

    @property
    def repo_url(self):
        return f"https://github.com/{self.repo_full_name}" if self.repo_full_name else ""

    @cached_property
    def hallmarks(self):
        """compute_hallmarks() once per instance, so once per request. Delete the attribute to recompute."""
        from .proof import compute_hallmarks  # here: proof imports verification, which refers back to projects
        return compute_hallmarks(self)

    @property
    def cover(self):
        """First screenshot. Uses the prefetch cache when the list view prefetched `screenshots`."""
        shots = list(self.screenshots.all())
        return shots[0] if shots else None


def unique_slug(owner, name):
    """A slug from the name, with -2, -3 ... added when this owner already has it."""
    base = slugify(name)[:50].strip("-") or "project"
    taken = set(Project.objects.filter(owner=owner, slug__startswith=base).values_list("slug", flat=True))
    slug, n = base, 2
    while slug in taken:
        slug = f"{base}-{n}"
        n += 1
    return slug


def screenshot_path(instance, filename):
    """Random file name: the original name (which the user controls) is never used."""
    return f"screenshots/{uuid.uuid4().hex}.webp"


class Screenshot(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="screenshots")
    image = models.ImageField(upload_to=screenshot_path, width_field="width", height_field="height")
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.project} #{self.order}"


MAX_LOG_LENGTH = 500
LOG_ENTRIES_PER_DAY = 10


class BuildLogEntry(models.Model):
    """A short public update on a project. One entry per project can be the "Launched" milestone."""

    class Kind(models.TextChoices):
        UPDATE = "update", _("Update")
        LAUNCH = "launch", _("Launched")

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="log_entries")
    text = models.TextField(max_length=MAX_LOG_LENGTH)  # limited markdown
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.UPDATE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            # Partial unique index (SQLite and PostgreSQL): at most one launch per project.
            models.UniqueConstraint(fields=["project"], condition=models.Q(kind="launch"), name="one_launch_per_project"),
        ]

    def __str__(self):
        return f"{self.project} · {self.kind} · {self.created_at:%Y-%m-%d}"

    @property
    def is_launch(self):
        return self.kind == self.Kind.LAUNCH

    @property
    def text_html(self):
        from .rendering import render_log_markdown
        return render_log_markdown(self.text)

"""Official news. Written only in the admin (superusers, or staff given the news permissions); there are
no public write endpoints. On the site the author is always the system account "shipmark" with the
official badge; `created_by` (the staff member) is only shown in the admin."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from projects.rendering import MAX_LENGTH, render_user_markdown


class NewsPostQuerySet(models.QuerySet):
    def published(self, now=None):
        """Visible on the site: has a publish time that has come (a future time = scheduled)."""
        return self.filter(published_at__isnull=False, published_at__lte=now or timezone.now())


class NewsPost(models.Model):
    title = models.CharField(_("title"), max_length=140)
    slug = models.SlugField(_("slug"), max_length=80, unique=True,
                            help_text=_("Part of the address: /news/<slug>/. Do not change it after publishing."))
    body = models.TextField(_("body"), max_length=MAX_LENGTH,
                            help_text=_("Markdown. Rendered and sanitized like project descriptions; no HTML."))
    published_at = models.DateTimeField(_("published at"), null=True, blank=True, db_index=True,
                                        help_text=_("Empty: draft. A time in the future: scheduled."))
    pinned = models.BooleanField(_("pinned"), default=False, help_text=_("Shown first in the news list."))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        editable=False, verbose_name=_("created by"),
    )  # internal only
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NewsPostQuerySet.as_manager()

    class Meta:
        ordering = ["-pinned", "-published_at", "-created_at"]
        verbose_name = _("news post")
        verbose_name_plural = _("news posts")

    def __str__(self):
        return self.title

    @property
    def body_html(self):
        return render_user_markdown(self.body)

    @property
    def excerpt(self):
        """Plain text for cards and page descriptions: the first ~200 characters of the body, without markup."""
        text = " ".join(strip_tags(self.body_html).split())
        return text if len(text) <= 200 else text[:199].rsplit(" ", 1)[0] + "…"

    def get_absolute_url(self):
        return reverse("news:detail", args=[self.slug])

    def is_published(self, now=None):
        return self.published_at is not None and self.published_at <= (now or timezone.now())

import re
from urllib.parse import urlsplit

from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from accounts.forms import StyledFormMixin
from verification.domain import forget_other_domains
from verification.repo import remove_link

from .models import MAX_LOG_LENGTH, BuildLogEntry, Project, Tag, Tool, unique_slug

MAX_TAGS = 5
TAG_RE = re.compile(r"^[\w+#.-]+(?: [\w+#.-]+)*$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,39}/[A-Za-z0-9_.-]{1,100}$")


class ProjectForm(StyledFormMixin, forms.ModelForm):
    """Create/edit. Status, slug and owner are not here: they are set by views, never by the user."""

    live_url = forms.URLField(required=False, max_length=200, assume_scheme="https")
    tags_text = forms.CharField(
        required=False, max_length=200, label=_("Tags"),
        help_text=_("Up to 5, separated by commas. For example: devtools, webhooks."),
    )

    class Meta:
        model = Project
        fields = ["name", "tagline", "description", "live_url", "repo_full_name", "built_with"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 10, "maxlength": 5000}),
            "built_with": forms.CheckboxSelectMultiple,
        }
        labels = {"repo_full_name": _("GitHub repository")}
        help_texts = {
            "tagline": _("One line, up to 120 characters."),
            "description": _("Markdown works. Links, lists, bold and code are allowed; HTML and images are not."),
            "live_url": _("The address where people can use it."),
            "repo_full_name": _("Like owner/name, or paste the GitHub link. It is checked later."),
            "built_with": _("Self-declared: we do not check this."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["built_with"].queryset = Tool.objects.all()
        self.fields["built_with"].widget.attrs["class"] = "checkbox"  # StyledFormMixin gave it "input"
        self.fields["repo_full_name"].widget.attrs.update({"autocapitalize": "none", "spellcheck": "false"})
        self.fields["tags_text"].widget.attrs["class"] = "input"
        if self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(t.name for t in self.instance.tags.all())

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean_tagline(self):
        return " ".join(self.cleaned_data["tagline"].split())

    def clean_live_url(self):
        url = self.cleaned_data["live_url"]
        if not url:
            return url
        parts = urlsplit(url)
        host = parts.hostname or ""
        if parts.scheme not in ("http", "https") or "." not in host or parts.username or parts.password:
            raise ValidationError(_("Enter a public web address, like https://example.com."))
        return url

    def clean_repo_full_name(self):
        value = self.cleaned_data["repo_full_name"].strip()
        for prefix in ("https://github.com/", "http://github.com/", "https://www.github.com/", "github.com/"):
            if value.lower().startswith(prefix):
                value = value[len(prefix):]
                break
        value = value.strip("/").removesuffix(".git")
        if value and not REPO_RE.match(value):
            raise ValidationError(_("Use the form owner/name, for example octocat/hello-world."))
        return value

    def clean_tags_text(self):
        tags = {}
        for raw in self.cleaned_data["tags_text"].split(","):
            name = " ".join(raw.lower().split())
            if not name:
                continue
            if len(name) > 30 or not TAG_RE.match(name) or not slugify(name, allow_unicode=True):
                raise ValidationError(_("Tags use letters, digits, spaces and + # . - (up to 30 characters)."))
            tags[slugify(name, allow_unicode=True)] = name
        if len(tags) > MAX_TAGS:
            raise ValidationError(_("Use at most 5 tags."))
        return tags  # {slug: name}

    def save(self, owner=None):
        project = super().save(commit=False)
        if owner is not None:
            project.owner = owner
        creating = project.pk is None
        for _attempt in range(5):  # a parallel request can take the same slug between check and insert
            try:
                with transaction.atomic():
                    if creating:
                        project.slug = unique_slug(project.owner, project.name)
                    project.save()
                break
            except IntegrityError:
                if not creating:
                    raise
        else:
            raise IntegrityError("Could not find a free slug")
        self.save_m2m()
        if not creating and "repo_full_name" in self.changed_data:
            # The old check was for another repository. Remove it so it stops blocking that repo.
            remove_link(project, "repo_changed", actor=project.owner)
        if not creating and "live_url" in self.changed_data:
            # Same idea for domains: a verification for the old domain must not keep blocking it.
            forget_other_domains(project, actor=project.owner)
        tags = []
        for slug, name in self.cleaned_data["tags_text"].items():
            tag, _created = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
            tags.append(tag)
        project.tags.set(tags)
        return project


class BuildLogForm(StyledFormMixin, forms.Form):
    text = forms.CharField(
        max_length=MAX_LOG_LENGTH, strip=True, label=_("What changed?"),
        help_text=_("Up to 500 characters. **Bold**, *italic*, [links](https://…) and `code` work."),
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": MAX_LOG_LENGTH}),
        error_messages={"required": _("Write a few words about the update first.")},
    )
    is_launch = forms.BooleanField(
        required=False, label=_("This is the launch"),
        help_text=_("Marks this entry as Launched and sets the project's launch date to today. Only one per project."),
    )

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def clean_is_launch(self):
        is_launch = self.cleaned_data["is_launch"]
        if is_launch and self.project.log_entries.filter(kind=BuildLogEntry.Kind.LAUNCH).exists():
            raise ValidationError(_("This project already has a launch entry. Delete it first to mark another one."))
        return is_launch

    def save(self):
        """Creates the entry. A launch entry also sets Project.launched_at, in the same transaction."""
        kind = BuildLogEntry.Kind.LAUNCH if self.cleaned_data["is_launch"] else BuildLogEntry.Kind.UPDATE
        try:
            with transaction.atomic():
                entry = BuildLogEntry.objects.create(project=self.project, text=self.cleaned_data["text"], kind=kind)
                if entry.is_launch:
                    self.project.launched_at = entry.created_at
                    self.project.save(update_fields=["launched_at", "updated_at"])
        except IntegrityError:  # two launch entries posted at the same moment: the unique index stops the second
            self.add_error("is_launch", _("This project already has a launch entry. Delete it first to mark another one."))
            return None
        return entry

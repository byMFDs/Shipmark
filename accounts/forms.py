from allauth.socialaccount.forms import SignupForm
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from config.ratelimit import is_limited
from moderation.pages import write_blocked_message
from projects.images import clean_avatar, clean_cover
from projects.models import Project, Tag
from projects.tags import parse_tag_names

from . import avatars
from .avatars import download_github_avatar, github_avatar_url
from .links import MAX_LINKS, clean_link
from .models import PinnedProject, ProfileLink, User
from .usernames import is_taken, validate_display_name, validate_username

MAX_SKILLS = 10
MAX_PINNED = 3


class StyledFormMixin:
    """Adds our CSS classes and accessibility attributes to every widget."""

    WIDGET_CLASSES = {"textarea": "textarea", "select": "select", "checkbox": "checkbox"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            kind = self[name].widget_type
            css = self.WIDGET_CLASSES.get(kind, "input")
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()
            if field.help_text:
                widget.attrs["aria-describedby"] = f"{self[name].auto_id}_hint"

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                attrs = self.fields[name].widget.attrs
                attrs["aria-invalid"] = "true"
                described = f"{attrs.get('aria-describedby', '')} {self[name].auto_id}_error".strip()
                attrs["aria-describedby"] = described


class SignupConfirmForm(StyledFormMixin, SignupForm):
    """The step after the first GitHub login: confirm the username and accept the Terms."""

    terms = forms.BooleanField(
        required=True,
        error_messages={"required": _("You need to accept the Terms to create an account.")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The email comes from GitHub and is private; the user is not asked for it.
        self.fields.pop("email", None)
        self.fields["username"].help_text = _("Your profile will be at /u/username/. Lowercase letters, digits, - and _.")
        self.fields["username"].widget.attrs.update({"autocapitalize": "none", "autocorrect": "off", "spellcheck": "false"})

    def clean_username(self):
        value = self.cleaned_data["username"].strip().lower()
        validate_username(value)
        if is_taken(value):
            raise ValidationError(User._meta.get_field("username").error_messages["unique"], code="unique")
        return value

    def save(self, request):
        user = self.sociallogin.user
        user.terms_version_accepted = settings.TERMS_VERSION
        user.terms_accepted_at = timezone.now()
        return super().save(request)


class SettingsForm(StyledFormMixin, forms.ModelForm):
    """Everything on the settings page, saved together with one button (so a chosen picture is never lost).

    Only these fields can be changed. Username and GitHub login are not editable here. Pictures go through
    the Pillow pipeline in projects.images and are stored by accounts.avatars; "use my GitHub picture" is a
    checkbox that downloads once on save. Links, skills and pinned projects are replaced as a whole.
    """

    avatar_file = forms.FileField(
        required=False, label=_("Upload a picture"),
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp", "data-preview-file": "avatar"}),
        help_text=_("PNG, JPEG or WebP, up to 5 MB. It is cropped to a square."),
    )
    use_github_avatar = forms.BooleanField(required=False, label=_("Use my GitHub picture instead"))
    remove_avatar = forms.BooleanField(required=False, label=_("Remove my picture (show initials)"))
    cover_file = forms.FileField(
        required=False, label=_("Cover image"),
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}),
        help_text=_("Optional. PNG, JPEG or WebP, up to 5 MB. It is cropped to a wide banner (3:1)."),
    )
    remove_cover = forms.BooleanField(required=False, label=_("Remove the cover image"))
    skills_text = forms.CharField(
        required=False, max_length=400, label=_("Skills"),
        help_text=_("Up to 10, separated by commas. For example: python, django, design."),
    )
    pinned = forms.ModelMultipleChoiceField(
        queryset=Project.objects.none(), required=False, widget=forms.CheckboxSelectMultiple,
        label=_("Pinned projects"),
        help_text=_("Up to 3 of your published projects, shown first on your profile."),
    )
    preferred_language = forms.ChoiceField(
        required=False,
        choices=[("", _("Automatic (browser language)"))] + list(settings.LANGUAGES),
    )

    class Meta:
        model = User
        fields = ["display_name", "headline", "location", "status", "about", "preferred_language"]
        widgets = {"about": forms.Textarea(attrs={"rows": 6, "maxlength": 1000})}
        labels = {
            "headline": _("Headline"), "location": _("Location"), "status": _("Status"),
            "about": pgettext_lazy("profile", "About"),
        }
        help_texts = {
            "display_name": _("Shown instead of your username. Optional."),
            "headline": _("One line under your name, up to 80 characters. For example: Building small tools with AI."),
            "location": _("City or country. Optional."),
            "status": _("A small label on your profile. Optional."),
            "about": _("Markdown works: links, lists, bold and code. Up to 1000 characters. HTML and images are not allowed."),
        }

    def __init__(self, *args, can_upload=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_upload = can_upload
        user = self.instance
        self.avatar_content = self.cover_content = None
        self.avatar_source = ""
        self.fields["status"].choices = [("", _("No status")), *User.Status.choices]
        self.fields["status"].required = False
        for name in ("avatar_file", "cover_file"):
            self.fields[name].widget.attrs["class"] = "input input--file"
        for name in ("use_github_avatar", "remove_avatar", "remove_cover"):
            self.fields[name].widget.attrs["class"] = "checkbox"
        self.fields["pinned"].widget.attrs["class"] = "checkbox"
        self.fields["skills_text"].widget.attrs["class"] = "input"
        self.fields["pinned"].queryset = Project.objects.filter(owner=user, status=Project.Status.PUBLISHED).order_by("name")
        self.fields["pinned"].label_from_instance = lambda project: project.name
        self.has_github_picture = bool(github_avatar_url(user)) if user.pk else False
        if not self.has_github_picture:
            del self.fields["use_github_avatar"]
        # Initial values for the saved lists. The link rows are fixed slots (empty ones stay blank).
        links = list(user.links.all()) if user.pk else []
        for i in range(MAX_LINKS):
            link = links[i] if i < len(links) else None
            self.fields[f"link{i}_kind"] = forms.ChoiceField(
                choices=ProfileLink.Kind.choices, required=False, label=_("Kind"),
                initial=link.kind if link else ProfileLink.Kind.WEBSITE,
            )
            self.fields[f"link{i}_url"] = forms.URLField(
                required=False, max_length=200, assume_scheme="https", label=_("Address"),
                initial=link.url if link else "",
            )
            self.fields[f"link{i}_kind"].widget.attrs["class"] = "select"
            self.fields[f"link{i}_url"].widget.attrs.update({
                "class": "input", "autocapitalize": "none", "spellcheck": "false", "placeholder": "https://",
            })
        if user.pk and not self.is_bound:
            self.fields["skills_text"].initial = ", ".join(t.name for t in user.skills.all())
            self.fields["pinned"].initial = [pin.project_id for pin in user.pins.all()]

    @property
    def link_rows(self):
        return [(self[f"link{i}_kind"], self[f"link{i}_url"]) for i in range(MAX_LINKS)]

    def clean_display_name(self):
        value = " ".join(self.cleaned_data["display_name"].split())
        validate_display_name(value, self.instance)
        return value

    def clean_headline(self):
        return " ".join(self.cleaned_data["headline"].split())

    def clean_location(self):
        return " ".join(self.cleaned_data["location"].split())

    def clean_about(self):
        return self.cleaned_data["about"].replace("\r\n", "\n").strip()

    def clean_skills_text(self):
        return parse_tag_names(self.cleaned_data["skills_text"], MAX_SKILLS, _("Use at most 10 skills."))

    def clean_pinned(self):
        pinned = self.cleaned_data["pinned"]
        if len(pinned) > MAX_PINNED:
            raise ValidationError(_("Pin at most 3 projects."))
        return list(pinned)

    def _image(self, field, cleaner, limit_name):
        """Run an uploaded picture through the pipeline. Returns the ContentFile or None (error added)."""
        upload = self.cleaned_data.get(field)
        if not upload:
            return None
        if not self.can_upload:
            self.add_error(field, write_blocked_message(self.instance))
        elif is_limited(limit_name, self.instance.pk, limit=20, window=3600):
            self.add_error(field, _("Too many changes in a short time. Try again in a few minutes."))
        else:
            try:
                return cleaner(upload)
            except ValidationError as error:
                self.add_error(field, error)
        return None

    def clean(self):
        data = super().clean()
        user = self.instance
        # Pictures: an upload wins over "use my GitHub picture", which wins over "remove".
        self.avatar_content = self._image("avatar_file", clean_avatar, "profile_image")
        if self.avatar_content is not None:
            self.avatar_source = User.AvatarSource.UPLOAD
        elif data.get("use_github_avatar") and "avatar_file" not in self.errors:
            if not self.can_upload:
                self.add_error("use_github_avatar", write_blocked_message(user))
            elif is_limited("avatar_github", user.pk, limit=5, window=3600):
                self.add_error("use_github_avatar", _("Too many changes in a short time. Try again in a few minutes."))
            else:
                try:
                    self.avatar_content = download_github_avatar(user)
                    self.avatar_source = User.AvatarSource.GITHUB
                except ValidationError as error:
                    self.add_error("use_github_avatar", error)
        self.cover_content = self._image("cover_file", clean_cover, "profile_image")
        # Links.
        self.links_clean, seen = [], set()
        for i in range(MAX_LINKS):
            url, kind = data.get(f"link{i}_url"), data.get(f"link{i}_kind") or ProfileLink.Kind.WEBSITE
            if not url:
                continue
            try:
                url = clean_link(kind, url)
            except ValidationError as error:
                self.add_error(f"link{i}_url", error)
                continue
            if url.lower() not in seen:
                seen.add(url.lower())
                self.links_clean.append((kind, url))
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        data = self.cleaned_data
        with transaction.atomic():
            if self.avatar_content is not None:
                avatars.set_avatar(user, self.avatar_content, self.avatar_source)
            elif data.get("remove_avatar"):
                avatars.remove_avatar(user)
            if self.cover_content is not None:
                avatars.set_cover(user, self.cover_content)
            elif data.get("remove_cover"):
                avatars.remove_cover(user)
            user.save()
            tags = [Tag.objects.get_or_create(slug=slug, defaults={"name": name})[0]
                    for slug, name in data["skills_text"].items()]
            user.skills.set(tags)
            user.links.all().delete()
            ProfileLink.objects.bulk_create(
                [ProfileLink(user=user, kind=kind, url=url, order=i) for i, (kind, url) in enumerate(self.links_clean)])
            user.pins.all().delete()
            PinnedProject.objects.bulk_create(
                [PinnedProject(user=user, project=project, order=i) for i, project in enumerate(data["pinned"])])
        return user


class AcceptTermsForm(StyledFormMixin, forms.Form):
    """Shown after settings.TERMS_VERSION is bumped."""

    terms = forms.BooleanField(
        required=True,
        error_messages={"required": _("Accept the updated Terms to keep using your account.")},
    )

    def save(self, user):
        user.terms_version_accepted = settings.TERMS_VERSION
        user.terms_accepted_at = timezone.now()
        user.save(update_fields=["terms_version_accepted", "terms_accepted_at"])


class DeleteAccountForm(StyledFormMixin, forms.Form):
    """The user types their username to confirm. Case and surrounding spaces do not matter."""

    confirm = forms.CharField(label=_("Type your username to confirm"), max_length=60)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        widget = self.fields["confirm"].widget
        widget.attrs.update({"autocomplete": "off", "autocapitalize": "none", "autocorrect": "off", "spellcheck": "false"})

    def clean_confirm(self):
        value = self.cleaned_data["confirm"].strip().lower()
        if value != self.user.username:
            raise ValidationError(_("This is not your username. Type it exactly as shown."), code="mismatch")
        return value

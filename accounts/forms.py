from allauth.socialaccount.forms import SignupForm
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import User
from .usernames import is_taken, validate_display_name, validate_username


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
    """Only these fields can be changed. Username and GitHub login are not editable here."""

    website = forms.URLField(required=False, max_length=200, assume_scheme="https")
    preferred_language = forms.ChoiceField(
        required=False,
        choices=[("", _("Automatic (browser language)"))] + list(settings.LANGUAGES),
    )

    class Meta:
        model = User
        fields = ["display_name", "bio", "website", "preferred_language"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}
        labels = {"bio": _("Bio")}

    def clean_website(self):
        url = self.cleaned_data["website"]
        if url and not url.lower().startswith(("http://", "https://")):
            raise ValidationError(_("Enter a link that starts with http:// or https://."))
        return url

    def clean_display_name(self):
        value = " ".join(self.cleaned_data["display_name"].split())
        validate_display_name(value, self.instance)
        return value


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

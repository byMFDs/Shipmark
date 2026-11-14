"""Форма підтримки з вкладеннями (картинки або текстові логи).

The support form. Attachments: up to 3, PNG/JPEG/WebP images (re-encoded by projects/images.py, metadata
removed) or .txt/.log text files (at most 200 KB, stored as UTF-8 text). Nothing else is accepted."""
import os
import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from accounts.forms import StyledFormMixin
from projects.images import clean_image

from . import antispam
from .models import MAX_ATTACHMENTS, MAX_BODY, MAX_SUBJECT, MIN_BODY, SupportAttachment, SupportMessage

MAX_TEXT_BYTES = 200 * 1024
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
TEXT_EXTENSIONS = {".txt", ".log"}
REFERENCE_RE = re.compile(r"^[A-Za-z0-9-]{1,32}$")


class MultipleFileInput(forms.ClearableFileInput):
    """Поле вибору кількох файлів."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Поле форми для кількох файлів."""
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else ([data] if data else [])
        return [super(MultipleFileField, self).clean(item, initial) for item in files]


def clean_name(name):
    """Безпечна назва файлу для персоналу.

    The file name as staff will see it: no folders, only safe characters, at most 100."""
    base = os.path.basename(name or "").strip()
    return re.sub(r"[^\w .()-]", "_", base)[:100]


def clean_text_file(upload):
    """Перевіряє .txt/.log і перекодовує в UTF-8.

    A .txt/.log file -> UTF-8 ContentFile. Refuses binary content."""
    if upload.size > MAX_TEXT_BYTES:
        raise ValidationError(_("A text file can be at most 200 KB."), code="text_too_big")
    raw = upload.read(MAX_TEXT_BYTES + 1)
    if len(raw) > MAX_TEXT_BYTES:
        raise ValidationError(_("A text file can be at most 200 KB."), code="text_too_big")
    text = raw.decode("utf-8", errors="replace")
    if "\x00" in text or text.count("�") > max(8, len(text) // 100):
        raise ValidationError(_("This does not look like a text file."), code="not_text")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return ContentFile(text.encode("utf-8"), name="attachment.txt")


def clean_attachment(upload):
    """Перевіряє одне вкладення за його типом.

    (kind, ContentFile) for one upload, or ValidationError. The extension picks the check; the check decides."""
    extension = os.path.splitext(upload.name or "")[1].lower()
    if extension in TEXT_EXTENSIONS:
        return SupportAttachment.Kind.TEXT, clean_text_file(upload)
    if extension in IMAGE_EXTENSIONS:
        return SupportAttachment.Kind.IMAGE, clean_image(upload)
    raise ValidationError(_("Attach PNG, JPEG or WebP images, or .txt and .log files."), code="bad_type")


class SupportForm(StyledFormMixin, forms.Form):
    """Форма звернення: тема, текст, адреса, вкладення."""
    category = forms.ChoiceField(
        label=_("What is it about?"), choices=[("", _("Choose a topic")), *SupportMessage.Category.choices],
        error_messages={"required": _("Choose a topic.")},
    )
    subject = forms.CharField(
        label=_("Subject (optional)"), required=False, max_length=MAX_SUBJECT,
        widget=forms.TextInput(attrs={"maxlength": MAX_SUBJECT, "autocomplete": "off"}),
    )
    body = forms.CharField(
        label=_("Message"), min_length=MIN_BODY, max_length=MAX_BODY,
        widget=forms.Textarea(attrs={"rows": 8, "maxlength": MAX_BODY}),
        help_text=_("What happened, where, and what you expected. Never send passwords or keys."),
        error_messages={"required": _("Write your message."),
                        "min_length": _("Write at least a short sentence (10 characters).")},
    )
    email = forms.EmailField(
        label=_("Your email"), required=False, max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        help_text=_("Used only to reply to this message."),
    )
    attachments = MultipleFileField(
        label=_("Attachments (optional)"), required=False,
        widget=MultipleFileInput(attrs={"accept": "image/png,image/jpeg,image/webp,.txt,.log,text/plain"}),
        help_text=_("Up to 3 files: PNG, JPEG or WebP images up to 5 MB, or .txt and .log files up to 200 KB."),
    )
    reference = forms.CharField(required=False, max_length=32, widget=forms.HiddenInput)
    started = forms.CharField(required=False, widget=forms.HiddenInput)
    # Honeypot: hidden from people (CSS and aria-hidden), filled by bots. Never shown as an error.
    website = forms.CharField(required=False, label=_("Leave this empty"),
                              widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and user.is_authenticated:
            self.fields["email"].initial = user.email
            self.fields["email"].help_text = _("From your account; used only to reply. You can change it here.")
        else:
            self.fields["email"].required = True
            self.fields["email"].error_messages["required"] = _("Add your email, so we can reply.")
        if not self.is_bound:
            self.fields["started"].initial = antispam.issue_token()

    @property
    def is_bot(self):
        return bool(self.data.get("website"))

    def clean_email(self):
        """Адреса з форми або з акаунта."""
        email = (self.cleaned_data.get("email") or "").strip()
        if not email and self.user is not None and self.user.is_authenticated:
            email = self.user.email or ""
        if not email:
            raise ValidationError(_("Add your email, so we can reply."), code="required")
        return email

    def clean_reference(self):
        value = (self.cleaned_data.get("reference") or "").strip()
        return value if REFERENCE_RE.match(value) else ""

    def clean_attachments(self):
        """Не більше трьох вкладень."""
        files = self.cleaned_data.get("attachments") or []
        if len(files) > MAX_ATTACHMENTS:
            raise ValidationError(ngettext(
                "Attach at most %(count)d file.", "Attach at most %(count)d files.", MAX_ATTACHMENTS,
            ) % {"count": MAX_ATTACHMENTS}, code="too_many")
        cleaned, errors = [], []
        for upload in files:
            try:
                kind, content = clean_attachment(upload)
            except ValidationError as error:
                errors.extend(f"{clean_name(upload.name)}: {message}" for message in error.messages)
                continue
            cleaned.append({"kind": kind, "content": content, "name": clean_name(upload.name), "size": content.size})
        if errors:
            raise ValidationError(errors)
        return cleaned

    def clean(self):
        """Перевіряє, чи форму заповнили як людина."""
        data = super().clean()
        problem = antispam.token_problem(self.data.get("started"))
        if problem == "fast":
            raise ValidationError(_("That was quick. Check your message and send it again."), code="too_fast")
        if problem == "expired":
            self.data = self.data.copy()
            self.data["started"] = antispam.issue_token()
            raise ValidationError(_("The form was open too long. Send it again."), code="expired")
        return data

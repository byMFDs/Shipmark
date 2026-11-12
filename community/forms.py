from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from accounts.forms import StyledFormMixin
from config.ratelimit import is_limited
from projects.forms import ScreenshotsField

from . import limits, stickers
from .images import clean_upload
from .models import Board
from .permissions import is_young
from .rendering import count_links


class BoardChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, board):
        return board.display_name


class PostFormMixin(StyledFormMixin):
    """Shared by threads and replies: the images field, and the rules for accounts younger than 24 hours.

    `user` is the author. Nothing here trusts the browser: counts, sizes and types are checked again.
    """

    max_images = 0

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_images(self):
        files = self.cleaned_data.get("images") or []
        if not files:
            return []
        if is_young(self.user):
            raise ValidationError(_("New accounts can add images 24 hours after signing up."), code="young")
        if len(files) > self.max_images:
            raise ValidationError(
                ngettext("You can add at most %(max)d image.", "You can add at most %(max)d images.", self.max_images),
                code="too_many", params={"max": self.max_images},
            )
        # One hit per file, counted before Pillow opens anything.
        if any([is_limited("community_upload", self.user.pk, limits.UPLOADS_PER_HOUR, limits.HOUR) for _file in files]):
            raise ValidationError(_("Too many images in one hour. Try again later."), code="rate")
        images, errors = [], []
        for upload in files:
            try:
                images.append(clean_upload(upload))
            except ValidationError as error:
                errors.append(ValidationError("%(name)s: %(error)s" % {
                    "name": (upload.name or "")[:60], "error": error.messages[0],
                }))
        if errors:
            raise ValidationError(errors)
        return images

    def check_links(self, *texts):
        if is_young(self.user) and count_links(*texts) > limits.YOUNG_MAX_LINKS:
            self.add_error("body", ValidationError(
                _("New accounts can put one link in a post during the first 24 hours."), code="links"))


def _body(rows, max_length):
    return forms.CharField(
        label=_("Text"), required=False, max_length=max_length, strip=True,
        widget=forms.Textarea(attrs={"rows": rows, "maxlength": max_length}),
        help_text=_("Markdown works. Links, lists, bold and code are allowed; HTML is not."),
    )


def _images(max_images):
    return ScreenshotsField(
        label=_("Images"), required=False,
        help_text=ngettext(
            "Up to %(max)d image, PNG, JPEG or WebP, 5 MB each.", "Up to %(max)d images, PNG, JPEG or WebP, 5 MB each.",
            max_images) % {"max": max_images},
    )


class ThreadForm(PostFormMixin, forms.Form):
    max_images = limits.MAX_THREAD_IMAGES

    board = BoardChoiceField(label=_("Board"), queryset=Board.objects.none(), empty_label=_("Choose a board"),
                             error_messages={"required": _("Choose a board."),
                                             "invalid_choice": _("Choose a board.")})
    title = forms.CharField(label=_("Title"), min_length=limits.MIN_TITLE, max_length=limits.MAX_TITLE, strip=True,
                            widget=forms.TextInput(attrs={"maxlength": limits.MAX_TITLE}))
    body = _body(10, limits.MAX_THREAD_BODY)
    images = _images(limits.MAX_THREAD_IMAGES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["board"].queryset = Board.objects.filter(is_active=True)

    def clean(self):
        data = super().clean()
        if not data.get("body") and not data.get("images") and "images" not in self.errors:
            self.add_error("body", _("Write something or add an image."))
        self.check_links(data.get("title"), data.get("body"))
        return data


class ThreadEditForm(PostFormMixin, forms.Form):
    """Text only. The title can change during the first 15 minutes (`title_editable`), the board and images never."""

    title = forms.CharField(label=_("Title"), min_length=limits.MIN_TITLE, max_length=limits.MAX_TITLE, strip=True,
                            widget=forms.TextInput(attrs={"maxlength": limits.MAX_TITLE}))
    body = _body(10, limits.MAX_THREAD_BODY)

    def __init__(self, *args, title_editable, has_images, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_images = has_images
        if not title_editable:
            del self.fields["title"]

    def clean(self):
        data = super().clean()
        if not data.get("body") and not self.has_images:
            self.add_error("body", _("Write something or add an image."))
        self.check_links(data.get("title"), data.get("body"))
        return data


class ReplyForm(PostFormMixin, forms.Form):
    max_images = limits.MAX_REPLY_IMAGES

    body = _body(4, limits.MAX_REPLY_BODY)
    # One key from community/stickers.py or nothing. A reply may be a sticker alone.
    sticker = forms.CharField(label=_("Sticker"), required=False, max_length=40, widget=forms.HiddenInput)
    images = _images(limits.MAX_REPLY_IMAGES)

    def clean_sticker(self):
        key = self.cleaned_data.get("sticker") or ""
        if key and not stickers.is_sticker(key):
            raise ValidationError(_("This sticker does not exist."), code="bad_sticker")
        return key

    def clean(self):
        data = super().clean()
        if not self.errors and not (data.get("body") or data.get("sticker") or data.get("images")):
            self.add_error("body", _("Write something, or add an image or a sticker."))
        self.check_links(data.get("body"))
        return data


class ReplyEditForm(PostFormMixin, forms.Form):
    body = _body(4, limits.MAX_REPLY_BODY)

    def __init__(self, *args, has_extras, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_extras = has_extras  # a sticker or images: the text may then be empty

    def clean(self):
        data = super().clean()
        if not data.get("body") and not self.has_extras:
            self.add_error("body", _("Write something, or add an image or a sticker."))
        self.check_links(data.get("body"))
        return data

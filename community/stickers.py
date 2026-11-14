"""Набір стікерів: ключ і перекладена назва.

The sticker manifest: key -> translated label. The database stores only the key (Reply.sticker_key).

The artwork is our own vector set in static/stickers/<key>.svg (added with the picker); nothing is ever accepted
from users. The label is the alt text.
"""
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

FACES = {
    "smile": _("Smile"),
    "laugh": _("Laugh"),
    "wink": _("Wink"),
    "cool": _("Cool"),
    "love": _("Love"),
    "thinking": _("Thinking"),
    "surprised": _("Surprised"),
    "sad": _("Sad"),
    "angry": _("Angry"),
    "sleepy": _("Sleepy"),
    "facepalm": _("Facepalm"),
}
GESTURES = {
    "thumbs-up": _("Thumbs up"),
    "clap": _("Clap"),
    "wave": _("Wave"),
    "ok": _("OK hand"),
    "fingers-crossed": _("Fingers crossed"),
    "flex": _("Flexed arm"),
    "pray": _("Folded hands"),
    "raised-hand": _("Raised hand"),
}
COMMUNITY = {
    "rocket": _("Rocket"),
    "fire": _("Fire"),
    "bug": _("Bug"),
    "heart": _("Heart"),
    "star": _("Star"),
    "party": _("Party"),
    "coffee": _("Coffee"),
    "ship": pgettext_lazy("sticker", "Ship"),
    "check": _("Check mark"),
    "hundred": _("One hundred"),
    "eyes": _("Eyes"),
    "lightbulb": _("Light bulb"),
    "handshake": _("Handshake"),
}

STICKERS = {**FACES, **GESTURES, **COMMUNITY}


def is_sticker(key):
    return key in STICKERS


def label(key):
    """Перекладена назва стікера або "".

    The translated name, or "" for an unknown key (an old row whose sticker was retired)."""
    return str(STICKERS.get(key, ""))

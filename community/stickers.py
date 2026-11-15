"""Reference sticker sheets: ordered keys and translated alt labels.

Only a manifest key is stored in the database. SVG is shipped by us, never accepted from users.
Artwork is traced from docs/new/img_2.png and img_3.png, in row-major sheet order.
"""
from django.utils.translation import gettext_lazy as _

FACES = {
    "smile": _("Smile"),
    "big-eyes": _("Grinning face with big eyes"),
    "smiling-eyes": _("Grinning face with smiling eyes"),
    "beaming": _("Beaming face with smiling eyes"),
    "laugh": _("Laugh"),
    "holding-back-tears": _("Face holding back tears"),
    "sweat-smile": _("Grinning face with sweat"),
    "joy": _("Face with tears of joy"),
    "rofl": _("Rolling on the floor laughing"),
    "smiling-tear": _("Smiling face with tear"),
    "smiling-face": _("Smiling face"),
    "blushing-smile": _("Smiling face with smiling eyes"),
    "halo": _("Smiling face with halo"),
    "slight-smile": _("Slightly smiling face"),
    "upside-down": _("Upside-down face"),
    "wink": _("Wink"),
    "relieved": _("Relieved face"),
    "love": _("Love"),
    "smiling-hearts": _("Smiling face with hearts"),
    "blowing-kiss": _("Face blowing a kiss"),
    "kissing": _("Kissing face"),
    "kissing-smiling-eyes": _("Kissing face with smiling eyes"),
    "kissing-closed-eyes": _("Kissing face with closed eyes"),
    "savoring-food": _("Face savoring food"),
    "tongue": _("Face with tongue"),
    "squinting-tongue": _("Squinting face with tongue"),
    "winking-tongue": _("Winking face with tongue"),
    "zany": _("Zany face"),
    "raised-eyebrow": _("Face with raised eyebrow"),
    "monocle": _("Face with monocle"),
    "nerd": _("Nerd face"),
    "cool": _("Cool"),
    "disguised": _("Disguised face"),
    "star-struck": _("Star-struck face"),
    "party": _("Party"),
    "melting": _("Melting face"),
    "smirk": _("Smirking face"),
    "unamused": _("Unamused face"),
    "exhaling": _("Face exhaling"),
    "sad": _("Pensive face"),
    "disappointed": _("Disappointed face"),
    "worried": _("Worried face"),
    "confused": _("Confused face"),
    "slightly-frowning": _("Slightly frowning face"),
    "frowning": _("Frowning face"),
    "persevering": _("Persevering face"),
    "confounded": _("Confounded face"),
    "tired": _("Tired face"),
}

GESTURES = {
    "pouting-cat": _("Pouting cat"),
    "heart-hands": _("Heart hands"),
    "palms-together": _("Palms up together"),
    "open-hands": _("Open hands"),
    "raised-hands": _("Raising hands"),
    "clap": _("Clap"),
    "handshake": _("Handshake"),
    "thumbs-up": _("Thumbs up"),
    "thumbs-down": _("Thumbs down"),
    "oncoming-fist": _("Oncoming fist"),
    "raised-fist": _("Raised fist"),
    "left-fist": _("Left-facing fist"),
    "right-fist": _("Right-facing fist"),
    "push-left": _("Leftwards pushing hand"),
    "push-right": _("Rightwards pushing hand"),
    "fingers-crossed": _("Fingers crossed"),
    "victory": _("Victory hand"),
    "finger-heart": _("Hand with index finger and thumb crossed"),
    "love-you-hand": _("Love-you gesture"),
    "horns": _("Sign of the horns"),
    "ok": _("OK hand"),
    "pinched-fingers": _("Pinched fingers"),
    "pinching-hand": _("Pinching hand"),
    "palm-down": _("Palm down hand"),
    "palm-up": _("Palm up hand"),
    "point-left": _("Backhand index pointing left"),
    "point-right": _("Backhand index pointing right"),
    "point-up": _("Backhand index pointing up"),
    "point-down": _("Backhand index pointing down"),
    "index-up": _("Index pointing up"),
    "raised-hand": _("Raised hand"),
    "back-of-hand": _("Raised back of hand"),
    "splayed-hand": _("Hand with fingers splayed"),
    "vulcan": _("Vulcan salute"),
    "wave": _("Wave"),
    "call-me": _("Call me hand"),
    "hand-right": _("Rightwards hand"),
    "hand-left": _("Leftwards hand"),
    "flex": _("Flexed arm"),
    "mechanical-arm": _("Mechanical arm"),
    "middle-finger": _("Middle finger"),
    "writing-hand": _("Writing hand"),
    "pray": _("Folded hands"),
    "point-at-viewer": _("Index pointing at the viewer"),
    "foot": _("Foot"),
    "leg": _("Leg"),
    "mechanical-leg": _("Mechanical leg"),
    "lipstick": _("Lipstick"),
}

STICKERS = {**FACES, **GESTURES}


def is_sticker(key):
    return key in STICKERS


def label(key):
    """Translated alt text, or empty text for an unknown/retired key."""
    return str(STICKERS.get(key, ""))

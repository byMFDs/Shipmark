"""Parsing "devtools, webhooks" into tags. Shared by projects (tags) and profiles (skills)."""
import re

from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

TAG_RE = re.compile(r"^[\w+#.-]+(?: [\w+#.-]+)*$")


def parse_tag_names(text, limit, too_many_message):
    """Returns {slug: name}; raises ValidationError for a bad tag or more than `limit` tags."""
    tags = {}
    for raw in text.split(","):
        name = " ".join(raw.lower().split())
        if not name:
            continue
        if len(name) > 30 or not TAG_RE.match(name) or not slugify(name, allow_unicode=True):
            raise ValidationError(_("Tags can use letters, numbers, spaces and + # . - (up to 30 characters)."))
        tags[slugify(name, allow_unicode=True)] = name
    if len(tags) > limit:
        raise ValidationError(too_many_message)
    return tags

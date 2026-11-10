"""Long pages written as markdown: content/<lang>/<slug>.md, falling back to content/en/.

Editing the .md file changes the page; no code or restart needed.
"""
import re

import markdown
import nh3
from django.conf import settings
from django.utils.translation import get_language

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

ALLOWED_TAGS = {
    "p", "br", "hr", "h1", "h2", "h3", "h4", "strong", "em", "code", "pre", "blockquote",
    "ul", "ol", "li", "a", "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_SCHEMES = {"http", "https", "mailto"}
H1_RE = re.compile(r"^#\s+(.+?)\s*#*\s*$", re.MULTILINE)


def render_markdown(text):
    """Markdown to safe HTML. Raw HTML in the source is stripped by the allowlist."""
    html = markdown.markdown(text, extensions=["tables", "fenced_code"])
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_SCHEMES,
        link_rel="noopener",
    )


def load_page(slug, language=None):
    """Return {"title", "html", "language"} for a page, or None if no file exists.

    `language` is the language of the file actually used (en when we fell back).
    """
    if not SLUG_RE.match(slug):
        return None
    language = language or get_language() or settings.LANGUAGE_CODE
    for lang in dict.fromkeys([language.split("-")[0], settings.LANGUAGE_CODE]):
        path = settings.CONTENT_DIR / lang / f"{slug}.md"
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            match = H1_RE.search(text)
            return {"title": match.group(1) if match else "", "html": render_markdown(text), "language": lang}
    return None

"""Довгі сторінки з markdown: content/<lang>/<slug>.md з запасним англійським.

Long pages written as markdown: content/<lang>/<slug>.md, falling back to content/en/.

Editing the .md file changes the page; no code or restart needed.
Placeholders like {{ contact_email }} are filled from config/branding.py (see PLACEHOLDERS).
"""
import re

import markdown
import nh3
from django.conf import settings
from django.utils.translation import get_language

from config import branding

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

ALLOWED_TAGS = {
    "p", "br", "hr", "h1", "h2", "h3", "h4", "strong", "em", "code", "pre", "blockquote",
    "ul", "ol", "li", "a", "table", "thead", "tbody", "tr", "th", "td",
}
# Heading ids come from "## Title {#anchor}" (attr_list), so pages can link to a section.
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}, "h2": {"id"}, "h3": {"id"}}
ALLOWED_SCHEMES = {"http", "https", "mailto"}
H1_RE = re.compile(r"^#\s+(.+?)\s*#*\s*$", re.MULTILINE)


def _placeholders():
    """Значення підстановок для markdown-сторінок."""
    return {
        "{{ site_name }}": branding.SITE_NAME,
        "{{ contact_email }}": branding.CONTACT_EMAIL,
        "{{ legal_owner_name }}": branding.LEGAL_OWNER_NAME,
        "{{ terms_version }}": settings.TERMS_VERSION,
    }


def fill_placeholders(text):
    """Підставляє значення простою заміною тексту.

    Plain text replacement (not the template engine), so a .md file can never run template code."""
    for key, value in _placeholders().items():
        text = text.replace(key, str(value))
    return text


def render_markdown(text):
    """Markdown у безпечний HTML.

    Markdown to safe HTML. Raw HTML in the source is stripped by the allowlist."""
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "attr_list"])
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_SCHEMES,
        link_rel="noopener",
    )


def load_page(slug, language=None):
    """Заголовок і HTML сторінки або None.

    Return {"title", "html", "language"} for a page, or None if no file exists.

    `language` is the language of the file actually used (en when we fell back).
    """
    if not SLUG_RE.match(slug):
        return None
    language = language or get_language() or settings.LANGUAGE_CODE
    # "pt-br" looks in content/pt-br/, then content/pt/, then content/en/.
    for lang in dict.fromkeys([language.lower(), language.split("-")[0].lower(), settings.LANGUAGE_CODE]):
        path = settings.CONTENT_DIR / lang / f"{slug}.md"
        if path.is_file():
            text = fill_placeholders(path.read_text(encoding="utf-8"))
            match = H1_RE.search(text)
            return {"title": match.group(1) if match else "", "html": render_markdown(text), "language": lang}
    return None

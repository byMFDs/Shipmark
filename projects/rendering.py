"""User markdown (project descriptions, build log entries) to safe HTML.

Two layers: raw HTML in the source is turned off in the markdown parser, and the result
goes through an nh3 allowlist anyway. If one layer has a hole, the other still holds.
"""
import re

import markdown
import nh3

ALLOWED_TAGS = {
    "p", "br", "strong", "em", "code", "pre", "blockquote", "ul", "ol", "li", "a",
    "h3", "h4",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_SCHEMES = {"http", "https", "mailto"}
MAX_LENGTH = 5000

# The page already has an h1 (project name) and h2 (section). User headings start at h3.
_HEADING = re.compile(r"<(/?)h([1-6])>")


def _demote(match):
    level = min(max(int(match.group(2)), 3), 4)
    return f"<{match.group(1)}h{level}>"


def _parser():
    md = markdown.Markdown(extensions=["fenced_code"])
    md.preprocessors.deregister("html_block")  # <div> ... </div> blocks stay text
    md.inlinePatterns.deregister("html")  # inline <b>, <script>, ... stay text
    return md


def render_user_markdown(text):
    """Markdown to sanitized HTML. Images are not allowed (screenshots have their own upload)."""
    text = (text or "")[:MAX_LENGTH]
    html = _HEADING.sub(_demote, _parser().convert(text))
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_SCHEMES,
        clean_content_tags={"script", "style"},
        link_rel="nofollow ugc noopener",
    )


# ---------- Build log: inline markdown only ----------

LOG_TAGS = {"p", "br", "strong", "em", "code", "a"}
LOG_MAX_LENGTH = 500
# Block syntax (headings, lists, quotes, code blocks, rules) stays plain text. So do images and emails.
_LOG_BLOCKS_OFF = ("indent", "code", "hashheader", "setextheader", "hr", "olist", "ulist", "quote")
_LOG_INLINE_OFF = ("html", "image_link", "image_reference", "short_image_ref", "automail")


def _log_parser():
    md = markdown.Markdown(extensions=["nl2br"])  # one Enter = a line break in short updates
    md.preprocessors.deregister("html_block")
    for name in _LOG_BLOCKS_OFF:
        md.parser.blockprocessors.deregister(name)
    for name in _LOG_INLINE_OFF:
        md.inlinePatterns.deregister(name)
    return md


def render_log_markdown(text):
    """Bold, italic, links and inline code (build log). Everything else stays text. Same nh3 layer."""
    text = (text or "")[:LOG_MAX_LENGTH]
    return nh3.clean(
        _log_parser().convert(text),
        tags=LOG_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https"},
        clean_content_tags={"script", "style"},
        link_rel="nofollow ugc noopener",
    )

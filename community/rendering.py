"""Thread and reply text: the site's one markdown renderer (projects.rendering: raw HTML off, nh3 allowlist,
links get rel="nofollow ugc noopener", no images)."""
import re

from projects.rendering import render_user_markdown

from . import limits

_URL = re.compile(r"https?://", re.IGNORECASE)
_ANCHOR = re.compile(r"<a\s", re.IGNORECASE)


def render_thread_body(text):
    return render_user_markdown(text, max_length=limits.MAX_THREAD_BODY)


def render_reply_body(text):
    return render_user_markdown(text, max_length=limits.MAX_REPLY_BODY)


def count_links(*texts):
    """How many links a post holds: addresses typed in the text or links after rendering, whichever is more
    (so `[text](mailto:...)` and a bare address both count)."""
    total = 0
    for text in texts:
        text = text or ""
        total += max(len(_URL.findall(text)), len(_ANCHOR.findall(render_thread_body(text))))
    return total

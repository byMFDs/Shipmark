"""SEO: robots.txt, sitemap.xml, JSON-LD і заголовки noindex.

Search engine helpers. Nothing here ranks a page: it only tells crawlers what is public, what is not, and what
each public page is.

- robots.txt (`robots_txt`) and sitemap.xml (`sitemap_xml`, built by pages/sitemaps.py) live at the root.
- JSON-LD builders: Organization and WebSite (home), BreadcrumbList (project and profile pages).
- The `X-Robots-Tag: noindex` header for private and utility pages lives in config/robots.py (middleware).
"""
import json
from urllib.parse import urlsplit

from django.contrib.sitemaps.views import x_robots_tag
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.templatetags.static import static
from django.utils.html import escape
from django.views.decorators.cache import cache_control

from config import branding
from config.robots import ROBOTS_DISALLOW
from config.site import absolute_url

from .sitemaps import SITEMAPS

MAX_SITEMAP_URLS = 50_000  # the sitemaps protocol limit for one file


def robots_txt(request):
    """/robots.txt: публічні сторінки дозволені, службові ні, з посиланням на sitemap."""
    lines = ["User-agent: *", "Allow: /"]
    lines += [f"Disallow: {path}" for path in ROBOTS_DISALLOW]
    lines += ["", f"Sitemap: {absolute_url('/sitemap.xml')}", ""]
    response = HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
    response["Cache-Control"] = "public, max-age=3600"
    return response


@x_robots_tag
@cache_control(public=True, max_age=3600)
def sitemap_xml(request):
    """/sitemap.xml: усі публічні сторінки одним файлом (до 50 000 адрес)."""
    urls = []
    for sitemap_class in SITEMAPS.values():
        urls.extend(sitemap_class().get_urls())
    return TemplateResponse(request, "sitemap.xml", {"urlset": urls[:MAX_SITEMAP_URLS]}, content_type="application/xml")


# ---------- JSON-LD ----------

def json_ld(data):
    """JSON для <script type="application/ld+json"> без символів, що можуть закрити тег.

    Serialized so the text can never contain "</script>" or HTML (same escaping as Django's json_script)."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return text.replace("<", "\\u003C").replace(">", "\\u003E").replace("&", "\\u0026")


def organization_ld():
    """Дані Organization: назва, адреса, логотип; sameAs лише якщо є посилання."""
    data = {
        "@type": "Organization",
        "name": branding.SITE_NAME,
        "url": absolute_url("/"),
        "logo": absolute_url(static(branding.APPLE_TOUCH_ICON)),
    }
    same_as = [url for url in getattr(branding, "SOCIAL_LINKS", {}).values() if str(url).startswith(("http://", "https://"))]
    if same_as:
        data["sameAs"] = same_as
    return data


def website_ld():
    """Дані WebSite: назва й адреса. Без SearchAction: пошукові сторінки закриті в robots.txt."""
    return {"@type": "WebSite", "name": branding.SITE_NAME, "url": absolute_url("/")}


def home_graph():
    """Organization і WebSite в одному @graph для головної сторінки."""
    return {"@context": "https://schema.org", "@graph": [organization_ld(), website_ld()]}


def breadcrumb_ld(crumbs):
    """BreadcrumbList зі списку (назва, шлях). Перший елемент — головна."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": str(name), "item": absolute_url(path)}
            for i, (name, path) in enumerate(crumbs, start=1)
        ],
    }

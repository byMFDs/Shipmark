"""Сторінки помилок 400, 403, 404, 500 і збою CSRF.

Error pages: 400, 403, 404, 500 and the CSRF failure (wired in config/urls.py and CSRF_FAILURE_VIEW).

404 and 403 render inside the site (header, menu). 500, 400 and the CSRF failure are standalone: they use
no database, no session and no context processor, so they still work when those are what broke.
Django's technical pages (URL list, traceback) never appear, because these views replace Django's defaults
and the settings switch DEBUG off in production.
"""
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme, urlencode

from config import branding

# Last resort when even the template fails (a missing static file in production, a broken tag).
_FALLBACK = (
    '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Error {code}</title></head>'
    "<body><h1>Error {code}</h1><p>Something went wrong. Please try again later.</p>{ref}"
    '<p><a href="/">Front page</a></p></body></html>'
)


def _back_url(request):
    """Попередня сторінка, якщо вона з цього сайту.

    The previous page, if it was on this site. Never fails: the 400 page can be shown for a bad Host."""
    referer = request.META.get("HTTP_REFERER", "")
    if not referer:
        return ""
    try:
        host = request.get_host()
    except Exception:
        return ""
    if url_has_allowed_host_and_scheme(referer, allowed_hosts={host}, require_https=request.is_secure()):
        return referer
    return ""


def _support_url(request):
    """Посилання «Повідомити про проблему» з id запиту.

    /support/ with the topic "Bug" and this request's id filled in ("Report a problem"). Never fails."""
    try:
        url = reverse("support:form")
    except Exception:
        return ""
    request_id = getattr(request, "request_id", "")
    return f"{url}?{urlencode({'category': 'bug', 'ref': request_id} if request_id else {'category': 'bug'})}"


def _context(request, code, reference):
    """Спільний контекст сторінок помилок."""
    return {
        "code": code,
        "back_url": _back_url(request),
        "request_id": getattr(request, "request_id", "") if reference else "",
        "support_url": _support_url(request),
        "contact_email": branding.CONTACT_EMAIL,
        "site_name": branding.SITE_NAME,
    }


def _site_page(request, template, status, reference=False):
    """Сторінка помилки всередині сайту (404, 403)."""
    context = _context(request, str(status), reference)
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        context.update(home_url=reverse("social:feed"), home_is_feed=True)
    else:
        context.update(home_url=reverse("pages:landing"), home_is_feed=False)
    return render(request, template, context, status=status)


def _standalone_page(request, template, status, code=None, reference=True):
    """Сторінка помилки без бази й контекстних процесорів (500, 400, CSRF)."""
    context = _context(request, code or str(status), reference)
    try:
        html = loader.get_template(template).render(context)  # no request: no context processors, no DB
    except Exception:
        ref = f"<p>Reference: {escape(context['request_id'])}</p>" if context["request_id"] else ""
        html = _FALLBACK.format(code=status, ref=ref)
    return HttpResponse(html, status=status)


def bad_request(request, exception=None):
    return _standalone_page(request, "400.html", 400, reference=False)


def permission_denied(request, exception=None):
    return _site_page(request, "403.html", 403, reference=True)


def page_not_found(request, exception=None):
    return _site_page(request, "404.html", 404)


def server_error(request):
    return _standalone_page(request, "500.html", 500)


def csrf_failure(request, reason="", template_name=None):
    # `reason` is not shown: it would tell an attacker which check failed. It is in the log (config/errorlog.py).
    return _standalone_page(request, "403_csrf.html", 403)


PREVIEWS = {
    "400": bad_request,
    "403": permission_denied,
    "404": page_not_found,
    "500": server_error,
    "csrf": csrf_failure,
}


def preview(request, code):
    """Перегляд усіх сторінок помилок у розробці (/_dev/errors/<code>/).

    /_dev/errors/<code>/: every error page, as the real views render it. Development only (404 without DEBUG)."""
    if not settings.DEBUG or code not in PREVIEWS:
        raise Http404
    response = PREVIEWS[code](request)
    response.status_code = 200  # a preview is not an error: keeps it out of the error log
    return response

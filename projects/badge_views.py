"""Публічні SVG-бейджі без входу, сесії й cookie.

Public SVG badges. No login, no session, no cookies.

Unknown, draft, hidden and suspended all give the same neutral badge with status 200, so a README
never shows a broken image and the badge does not reveal which of those cases it was.
"""
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils.cache import patch_cache_control
from django.views.decorators.http import require_safe

from accounts.profile import profile_projects
from moderation.visibility import visible_owner, visible_users
from verification.uptime import with_uptime

from . import badges
from .models import Project

FOUND_MAX_AGE = 3600
NOT_FOUND_MAX_AGE = 300  # short, so a badge pasted before publishing starts working soon


def _svg(svg, max_age):
    """SVG-відповідь з кешем і суворою CSP."""
    response = HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")
    patch_cache_control(response, public=True, max_age=max_age)
    # If the file is opened on its own, it may not run anything or load anything.
    response["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    return response


@require_safe
def project_badge(request, username, slug):
    """Бейдж проєкту; невідомий чи прихований дає нейтральний бейдж."""
    project = (
        with_uptime(visible_owner(Project.objects).select_related("owner", "repo_link").prefetch_related("domain_verifications"))
        .filter(owner__username__iexact=username, slug=slug, status=Project.Status.PUBLISHED)
        .first()
    )
    if project is None:
        return _svg(badges.not_found_badge(), NOT_FOUND_MAX_AGE)
    earned = {mark.kind for mark in project.hallmarks if mark.earned}
    return _svg(badges.project_badge(project.name, earned), FOUND_MAX_AGE)


@require_safe
def profile_badge(request, username):
    """Бейдж профілю з кількістю марок."""
    person = visible_users(get_user_model().objects.filter(is_system_account=False)).filter(username__iexact=username).first()
    if person is None:
        return _svg(badges.not_found_badge(), NOT_FOUND_MAX_AGE)
    count = sum(project.hallmarks.earned_count for project in profile_projects(person))
    return _svg(badges.profile_badge(person.username, count), FOUND_MAX_AGE)

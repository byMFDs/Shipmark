"""Public news pages. Read-only: posts are written in the admin (news/admin.py), never through the site.

Everyone sees published posts, anonymous visitors included. A draft, or a post scheduled for later, is a 404 for
everybody (staff preview it in the admin). The byline is always the system account "shipmark" with its official badge.
"""
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from accounts.system import SYSTEM_USERNAME

from .models import NewsPost

PAGE_SIZE = 10
MAX_PAGE = 100


def news_author():
    """The system account, with its badges loaded (one query for the badge)."""
    return get_user_model().objects.prefetch_related("badges").get(username=SYSTEM_USERNAME)


@require_GET
def post_list(request):
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    if page > MAX_PAGE:
        raise Http404
    page = max(page, 1)
    start = (page - 1) * PAGE_SIZE
    posts = list(NewsPost.objects.published().order_by("-pinned", "-published_at", "-pk")[start:start + PAGE_SIZE + 1])
    if page > 1 and not posts:
        raise Http404
    return render(request, "news/list.html", {
        "posts": posts[:PAGE_SIZE], "author": news_author(), "page": page,
        "has_next": len(posts) > PAGE_SIZE, "has_prev": page > 1,
    })


@require_GET
def post_detail(request, slug):
    post = get_object_or_404(NewsPost.objects.published(), slug=slug)
    return render(request, "news/detail.html", {"post": post, "author": news_author()})

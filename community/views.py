"""Сторінки спільноти й обробники запису.

Community pages and write endpoints.

Every view starts with `community_view` (404 while COMMUNITY_ENABLED is off). Reading is public. Every write
needs a signed-in user who may post (community/permissions.py), is rate limited, and checks in code that the
target is visible and, for edit and delete, that it is the user's own (someone else's is a 404).
"""
import re
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from config.ratelimit import is_limited
from moderation.pages import write_blocked_message
from pages.content import load_page

from . import limits, notifications, ranking, services, tree
from .flags import community_view
from .forms import ReplyEditForm, ReplyForm, ThreadEditForm, ThreadForm
from .models import Board, Reply, Thread, Vote
from .permissions import author_hidden, can_reply, can_see_thread, post_block

TOO_MANY = gettext_lazy("Too many changes in a short time. Try again in a few minutes.")


def _wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def _page(request):
    """Номер сторінки з GET (щонайменше 1)."""
    try:
        return max(int(request.GET.get("page", 1)), 1)
    except ValueError:
        return 1


def _choice(value, allowed, default):
    return value if value in allowed else default


# ---------- Shared page parts ----------

_IMG_SRC = re.compile(r"(img-src[^;]*)")


def allow_blob_previews(view):
    """Дозволяє в CSP прев'ю картинок blob: на сторінках з формою допису.

    Pages with a composer: the browser shows chosen images before upload as blob: URLs (local to the page,
    nothing leaves the device). Only these responses get `blob:` in img-src; every other page keeps the site policy."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        policy = settings.CONTENT_SECURITY_POLICY
        if policy and "Content-Security-Policy" not in response and request.user.is_authenticated:
            response["Content-Security-Policy"] = _IMG_SRC.sub(lambda m: m.group(1) + " blob:", policy, count=1)
        return response
    return wrapper


def _boards_with_counts():
    """Активні дошки з кількістю публічних тем.

    Active boards with their number of public threads (two queries), for the left column."""
    counts = dict(Thread.objects.public().values_list("board").annotate(n=Count("pk")))
    boards = list(Board.objects.filter(is_active=True))
    for item in boards:
        item.thread_count = counts.get(item.pk, 0)
    return boards


def _voted(user, threads=(), replies=()):
    """Id тем і відповідей, за які людина проголосувала.

    (thread ids, reply ids) the user upvoted among these. One query, none for visitors."""
    if not user.is_authenticated or not (threads or replies):
        return set(), set()
    rows = Vote.objects.filter(user=user).filter(
        Q(thread__in=[t.pk for t in threads]) | Q(reply__in=list(replies))).values_list("thread_id", "reply_id")
    return {t for t, _r in rows if t}, {r for _t, r in rows if r}


def _list_url(board, page, **params):
    """Адреса списку тем з фільтрами й сторінкою."""
    base = board.get_absolute_url() if board else reverse("community:home")
    query = {k: v for k, v in params.items() if v}
    if page > 1:
        query["page"] = page
    return f"{base}?{urlencode(query)}" if query else base


# ---------- Lists ----------

@community_view
@require_GET
def home(request, slug=None):
    """Головна спільноти й дошки: теми, пошук, дошки.

    /community/ and /community/b/<slug>/: threads (Hot, New, Top), search by title, the boards with counts.
    "Load more" asks for JSON ({html, next_url}); without JS the same links open the next page."""
    board = get_object_or_404(Board, slug=slug, is_active=True) if slug else None
    sort = _choice(request.GET.get("sort"), ranking.SORTS, "hot")
    window = _choice(request.GET.get("t"), ranking.TOP_WINDOWS, "week")
    query = " ".join(request.GET.get("q", "").split())[:limits.MAX_SEARCH]
    if len(query) < limits.MIN_SEARCH:
        query = ""
    page = _page(request)
    now = timezone.now()

    public = Thread.objects.public()
    scoped = public.filter(board=board) if board else public
    listed = scoped.select_related("board", "author").prefetch_related("author__badges", "images")
    if query:
        pinned, threads = [], listed.filter(title__icontains=query)
    else:
        pinned = list(listed.filter(pinned=True).order_by("-last_activity_at", "-pk")[:3]) if page == 1 else []
        threads = listed.filter(pinned=False)
    start = (page - 1) * limits.THREADS_PER_PAGE
    rows = list(ranking.ordered(threads, sort, window, now)[start:start + limits.THREADS_PER_PAGE + 1])
    has_next = len(rows) > limits.THREADS_PER_PAGE
    rows = rows[:limits.THREADS_PER_PAGE]
    voted, _replies = _voted(request.user, threads=rows + pinned)
    params = {"q": query, "sort": sort if sort != "hot" else "", "t": window if sort == "top" else ""}
    next_url = _list_url(board, page + 1, **params) if has_next else ""
    item_context = {"threads": rows, "voted": voted}
    if _wants_json(request):
        return JsonResponse({
            "html": render_to_string("community/_thread_items.html", item_context, request=request),
            "next_url": next_url,
        })
    return render(request, "community/home.html", {
        **item_context, "board": board, "boards": _boards_with_counts(), "pinned": pinned, "has_next": has_next,
        "next_url": next_url, "prev_url": _list_url(board, page - 1, **params) if page > 1 else "",
        "page": page, "sort": sort, "window": window, "query": query,
        "sort_urls": {key: _list_url(board, 1, q=query, sort=key if key != "hot" else "") for key in ranking.SORTS},
        "window_urls": {key: _list_url(board, 1, q=query, sort="top", t=key) for key in ranking.TOP_WINDOWS},
    })


@community_view
@require_GET
def rules(request):
    """Сторінка правил спільноти.

    /community/rules/: content/<lang>/community-rules.md (falls back to English)."""
    page = load_page("community-rules")
    if page is None:
        raise Http404
    return render(request, "community/rules.html", {"page": page, "boards": _boards_with_counts()})


# ---------- Thread page ----------

def _thread_or_404(request, pk):
    """Тема, яку людина може бачити, або 404."""
    thread = get_object_or_404(Thread.objects.select_related("board", "author"), pk=pk)
    if not can_see_thread(request.user, thread):
        raise Http404
    return thread


def _render_thread(request, thread, form=None, parent=None, status=200):
    """Сторінка теми з деревом відповідей і формою."""
    user = request.user
    sort = _choice(request.GET.get("sort"), ranking.REPLY_SORTS, "best")
    page = _page(request)
    nodes, has_next = tree.load_page(thread, sort, page)
    voted_threads, voted_replies = _voted(user, threads=[thread], replies=tree.reply_ids(nodes))
    block = post_block(user) if user.is_authenticated else ""
    may_reply = bool(user.is_authenticated and not block and can_reply(user, thread))
    base = thread.get_absolute_url()
    next_url = f"{base}?{urlencode({'sort': sort, 'page': page + 1})}" if has_next else ""
    item_context = {"nodes": nodes, "thread": thread, "voted_replies": voted_replies, "may_reply": may_reply}
    if _wants_json(request):  # "Load more" replies
        return JsonResponse({
            "html": render_to_string("community/_reply_items.html", item_context, request=request),
            "next_url": next_url,
        })
    if parent is None and request.method == "GET" and request.GET.get("reply_to", "").isdigit():
        parent = Reply.objects.filter(pk=request.GET["reply_to"], thread=thread).select_related("author").first()
        if parent is not None and not parent.is_alive:
            parent = None
    return render(request, "community/thread.html", {
        **item_context, "images": list(thread.images.all()), "has_next": has_next, "page": page,
        "next_url": next_url, "prev_url": f"{base}?{urlencode({'sort': sort, 'page': page - 1})}" if page > 1 else "",
        "sort": sort, "sort_urls": {key: f"{base}?sort={key}" for key in ranking.REPLY_SORTS},
        "voted_thread": thread.pk in voted_threads, "parent": parent, "post_block_reason": block,
        "form": form if form is not None else (ReplyForm(user=user) if may_reply else None),
        "is_author": user.is_authenticated and thread.author_id == user.pk,
        "can_edit": user.is_authenticated and thread.author_id == user.pk and _thread_editable(thread),
        "boards": _boards_with_counts(),
    }, status=status)


@community_view
@require_GET
@allow_blob_previews
def thread_detail(request, pk, slug=""):
    """Сторінка теми; неправильний slug перенаправляє на правильний."""
    thread = _thread_or_404(request, pk)
    if slug != thread.slug:
        return redirect(thread.get_absolute_url(), permanent=True)
    return _render_thread(request, thread)


# ---------- Write: threads ----------

def _blocked(request, message):
    if _wants_json(request):
        return JsonResponse({"ok": False, "message": str(message)}, status=403)
    return HttpResponseForbidden(message)


@community_view
@login_required
@require_http_methods(["GET", "POST"])
@allow_blob_previews
def thread_new(request):
    """Створення теми."""
    user = request.user
    block = post_block(user)
    if request.method == "POST" and block:
        return _blocked(request, block)
    initial = {}
    if request.method == "GET" and request.GET.get("board"):
        initial["board"] = Board.objects.filter(slug=request.GET["board"], is_active=True).first()
    form = ThreadForm(request.POST or None, request.FILES or None, user=user, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if is_limited("community_thread", user.pk, limits.THREADS_PER_HOUR, limits.HOUR):
            form.add_error(None, _("You started several threads in the last hour. Try again later."))
        elif not services.claim_thread_text(user, data["title"], data["body"]):
            form.add_error(None, _("You already posted this."))
        else:
            thread = services.create_thread(user, data["board"], data["title"], data["body"], data["images"])
            return redirect(thread)
    return render(request, "community/thread_form.html", {"form": form, "post_block_reason": block, "thread": None,
                                                         "boards": _boards_with_counts()},
                  status=400 if form.errors else 200)


def _thread_editable(thread):
    return thread.status == Thread.Status.PUBLISHED and not thread.is_deleted


def _own_thread_or_404(request, pk):
    """Власна тема людини або 404.

    The signed-in user's own thread. Anyone else's is a 404, like a thread that does not exist."""
    thread = get_object_or_404(Thread.objects.select_related("board", "author"), pk=pk)
    if thread.author_id != request.user.pk or not can_see_thread(request.user, thread):
        raise Http404
    return thread


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def thread_edit(request, pk):
    """Редагування своєї теми."""
    thread = _own_thread_or_404(request, pk)
    if not _thread_editable(thread):
        return HttpResponseForbidden(_("This thread is locked or removed. It cannot be changed."))
    user = request.user
    block = post_block(user)
    if request.method == "POST" and block:
        return _blocked(request, block)
    title_editable = services.title_editable(thread)
    form = ThreadEditForm(
        request.POST or None, user=user, title_editable=title_editable, has_images=thread.images.exists(),
        initial={"title": thread.title, "body": thread.body},
    )
    if request.method == "POST" and form.is_valid():
        if is_limited("community_edit", user.pk, limits.EDITS_PER_HOUR, limits.HOUR):
            form.add_error(None, TOO_MANY)
        else:
            services.edit_thread(thread, form.cleaned_data["body"], form.cleaned_data.get("title"))
            return redirect(thread)
    return render(request, "community/thread_form.html", {
        "form": form, "post_block_reason": block, "thread": thread, "title_editable": title_editable,
    }, status=400 if form.errors else 200)


def _may_clean_up(request):
    """Чи може людина видаляти своє (приглушеним можна, призупиненим ні).

    Deleting your own post stays open to muted people (like unpublishing a project); not to suspended ones."""
    if request.user.is_suspended:
        return HttpResponseForbidden(write_blocked_message(request.user))
    if is_limited("community_delete", request.user.pk, limits.DELETES_PER_HOUR, limits.HOUR):
        return HttpResponseForbidden(TOO_MANY)
    return None


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def thread_delete(request, pk):
    """Видалення своєї теми з підтвердженням."""
    thread = _own_thread_or_404(request, pk)
    if thread.is_deleted:
        raise Http404
    if request.method == "POST":
        refusal = _may_clean_up(request)
        if refusal:
            return refusal
        services.delete_thread(thread)
        messages.success(request, _("Thread deleted."))
        return redirect("community:home")
    return render(request, "community/confirm_delete.html", {"thread": thread, "reply": None,
                                                           "back": thread.get_absolute_url()})


# ---------- Write: replies ----------

def _parent_for(request, thread):
    """Відповідь, на яку відповідають, з POST.

    The reply being answered, from POST. (reply or None, error message or "")."""
    raw = request.POST.get("parent", "")
    if not raw:
        return None, ""
    gone = _("The reply you are answering is gone.")
    if not raw.isdigit():
        return None, gone
    # Only a reply of this very thread: a parent from another thread is refused.
    parent = Reply.objects.filter(pk=raw, thread=thread).select_related("author", "parent", "root").first()
    if parent is None or not parent.is_alive or author_hidden(parent.author):
        return None, gone
    return parent, ""


@community_view
@login_required
@require_POST
@allow_blob_previews
def reply_create(request, pk):
    """Створення відповіді."""
    thread = _thread_or_404(request, pk)
    user = request.user
    block = post_block(user)
    if block:
        return _blocked(request, block)
    if not can_reply(user, thread):
        return _blocked(request, _("This thread is locked. Only moderators can reply."))
    parent, parent_error = _parent_for(request, thread)
    form = ReplyForm(request.POST, request.FILES, user=user)
    if parent_error:
        form.add_error(None, parent_error)
    if form.is_valid():
        data = form.cleaned_data
        if is_limited("community_reply", user.pk, limits.REPLIES_PER_HOUR, limits.HOUR):
            form.add_error(None, _("You replied many times in the last hour. Try again later."))
        elif not services.claim_reply_text(user, thread, parent, data["body"]):
            form.add_error(None, _("You already posted this."))
        else:
            reply = services.create_reply(user, thread, parent, data["body"], images=data["images"])
            return redirect(reply.get_absolute_url())
    return _render_thread(request, thread, form=form, parent=parent, status=400)


def _own_reply_or_404(request, pk):
    """Власна відповідь людини або 404."""
    reply = get_object_or_404(Reply.objects.select_related("thread__board", "thread__author", "author"), pk=pk)
    if reply.author_id != request.user.pk or not can_see_thread(request.user, reply.thread):
        raise Http404
    return reply


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def reply_edit(request, pk):
    """Редагування своєї відповіді."""
    reply = _own_reply_or_404(request, pk)
    if not reply.is_alive or reply.thread.status != Thread.Status.PUBLISHED:
        return HttpResponseForbidden(_("This reply cannot be changed."))
    user = request.user
    block = post_block(user)
    if request.method == "POST" and block:
        return _blocked(request, block)
    form = ReplyEditForm(request.POST or None, user=user, initial={"body": reply.body},
                         has_extras=reply.images.exists())
    if request.method == "POST" and form.is_valid():
        if is_limited("community_edit", user.pk, limits.EDITS_PER_HOUR, limits.HOUR):
            form.add_error(None, TOO_MANY)
        else:
            services.edit_reply(reply, form.cleaned_data["body"])
            return redirect(reply.get_absolute_url())
    return render(request, "community/reply_form.html", {"form": form, "reply": reply, "post_block_reason": block},
                  status=400 if form.errors else 200)


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def reply_delete(request, pk):
    """Видалення своєї відповіді з підтвердженням."""
    reply = _own_reply_or_404(request, pk)
    if reply.is_deleted:
        raise Http404
    if request.method == "POST":
        refusal = _may_clean_up(request)
        if refusal:
            return refusal
        services.delete_reply(reply)
        messages.success(request, _("Reply deleted."))
        return redirect(reply.thread)
    return render(request, "community/confirm_delete.html", {"thread": reply.thread, "reply": reply,
                                                           "back": reply.get_absolute_url()})


# ---------- Notifications ----------

@community_view
@login_required
@require_GET
def notifications_view(request):
    """Сповіщення людини; відкриття сторінки позначає їх прочитаними.

    The signed-in person's own notifications only (there is no per-item URL to guess). Opening the page
    marks everything read and clears the header mark; the ones that were new are highlighted this once."""
    page = _page(request)
    start = (page - 1) * limits.NOTIFICATIONS_PER_PAGE
    rows = list(notifications.inbox(request.user)[start:start + limits.NOTIFICATIONS_PER_PAGE + 1])
    notifications.mark_all_read(request.user)
    return render(request, "community/notifications.html", {
        "items": rows[:limits.NOTIFICATIONS_PER_PAGE], "has_next": len(rows) > limits.NOTIFICATIONS_PER_PAGE,
        "page": page,
    })


# ---------- Votes ----------

def _vote(request, target, thread):
    """Ставить або знімає голос: JSON для fetch, перенаправлення для форми.

    Upvote or take it back: POST value=1 / value=0. JSON for fetch, a redirect for a plain form."""
    user = request.user
    back = target.get_absolute_url()

    def fail(message, status):
        if _wants_json(request):
            return JsonResponse({"ok": False, "message": str(message)}, status=status)
        messages.error(request, message)
        return redirect(back)

    block = post_block(user)
    if block:
        return fail(block, 403)
    if is_limited("community_vote", user.pk, limits.VOTES_PER_HOUR, limits.HOUR):
        return fail(TOO_MANY, 429)
    if request.POST.get("value") not in ("0", "1"):
        return fail(_("Something went wrong. Reload the page and try again."), 400)
    if target.author_id == user.pk:
        return fail(_("You cannot vote for your own post."), 400)
    if thread.is_removed:
        raise Http404
    score = services.set_vote(user, target, request.POST["value"] == "1")
    if _wants_json(request):
        return JsonResponse({"ok": True, "voted": request.POST["value"] == "1", "score": score})
    return redirect(back)


def _signed_in_or_401(request):
    """Неавторизованим: 401 для fetch або перехід на вхід."""
    if request.user.is_authenticated:
        return None
    if _wants_json(request):
        return JsonResponse({"ok": False, "message": _("Sign in to do this.")}, status=401)
    return redirect_to_login(request.get_full_path())


@community_view
@require_POST
def vote_thread(request, pk):
    """Голос за тему."""
    refusal = _signed_in_or_401(request)
    if refusal:
        return refusal
    thread = _thread_or_404(request, pk)
    if thread.is_deleted:
        raise Http404
    return _vote(request, thread, thread)


@community_view
@require_POST
def vote_reply(request, pk):
    """Голос за відповідь."""
    refusal = _signed_in_or_401(request)
    if refusal:
        return refusal
    reply = get_object_or_404(Reply.objects.select_related("thread__board", "thread__author", "author"), pk=pk)
    if not can_see_thread(request.user, reply.thread) or not reply.is_alive or author_hidden(reply.author):
        raise Http404
    return _vote(request, reply, reply.thread)

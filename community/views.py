"""Community pages and write endpoints.

Every view starts with `community_view` (404 while COMMUNITY_ENABLED is off). Reading is public. Every write
needs a signed-in user who may post (community/permissions.py), is rate limited, and checks in code that the
target is visible and, for edit and delete, that it is the user's own (someone else's is a 404).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from config.ratelimit import is_limited
from moderation.pages import write_blocked_message

from . import limits, ranking, services, tree
from .flags import community_view
from .forms import ReplyEditForm, ReplyForm, ThreadEditForm, ThreadForm
from .models import Board, Reply, Thread, Vote
from .permissions import author_hidden, can_reply, can_see_thread, post_block

TOO_MANY = gettext_lazy("Too many changes in a short time. Try again in a few minutes.")


def _wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def _page(request):
    try:
        return max(int(request.GET.get("page", 1)), 1)
    except ValueError:
        return 1


def _choice(value, allowed, default):
    return value if value in allowed else default


# ---------- Lists ----------

@community_view
@require_GET
def home(request, slug=None):
    """/community/ and /community/b/<slug>/: threads (Hot, New, Top), search by title, the boards with counts."""
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
    listed = scoped.select_related("board", "author").prefetch_related("author__badges")
    if query:
        pinned, threads = [], listed.filter(title__icontains=query)
    else:
        pinned = list(listed.filter(pinned=True).order_by("-last_activity_at", "-pk")[:3]) if page == 1 else []
        threads = listed.filter(pinned=False)
    start = (page - 1) * limits.THREADS_PER_PAGE
    rows = list(ranking.ordered(threads, sort, window, now)[start:start + limits.THREADS_PER_PAGE + 1])

    counts = dict(public.values_list("board").annotate(n=Count("pk")))
    boards = list(Board.objects.filter(is_active=True))
    for item in boards:
        item.thread_count = counts.get(item.pk, 0)

    return render(request, "community/home.html", {
        "board": board, "boards": boards, "pinned": pinned, "threads": rows[:limits.THREADS_PER_PAGE],
        "has_next": len(rows) > limits.THREADS_PER_PAGE, "page": page, "sort": sort, "window": window,
        "query": query, "sorts": ranking.SORTS, "windows": list(ranking.TOP_WINDOWS),
    })


# ---------- Thread page ----------

def _thread_or_404(request, pk):
    thread = get_object_or_404(Thread.objects.select_related("board", "author"), pk=pk)
    if not can_see_thread(request.user, thread):
        raise Http404
    return thread


def _render_thread(request, thread, form=None, parent=None, status=200):
    user = request.user
    sort = _choice(request.GET.get("sort"), ranking.REPLY_SORTS, "best")
    page = _page(request)
    nodes, has_next = tree.load_page(thread, sort, page)
    voted_thread, voted_replies = False, set()
    if user.is_authenticated:
        ids = tree.reply_ids(nodes)
        for thread_id, reply_id in Vote.objects.filter(user=user).filter(
                Q(thread=thread) | Q(reply__in=ids)).values_list("thread_id", "reply_id"):
            if thread_id:
                voted_thread = True
            else:
                voted_replies.add(reply_id)
    if parent is None and request.method == "GET" and request.GET.get("reply_to", "").isdigit():
        parent = Reply.objects.filter(pk=request.GET["reply_to"], thread=thread).select_related("author").first()
        if parent is not None and not parent.is_alive:
            parent = None
    block = post_block(user) if user.is_authenticated else ""
    may_reply = user.is_authenticated and not block and can_reply(user, thread)
    return render(request, "community/thread.html", {
        "thread": thread, "images": list(thread.images.all()), "nodes": nodes, "has_next": has_next, "page": page,
        "sort": sort, "reply_sorts": ranking.REPLY_SORTS, "voted_thread": voted_thread,
        "voted_replies": voted_replies, "parent": parent, "block": block, "may_reply": may_reply,
        "form": form if form is not None else (ReplyForm(user=user) if may_reply else None),
        "is_author": user.is_authenticated and thread.author_id == user.pk,
        "can_edit": user.is_authenticated and thread.author_id == user.pk and _thread_editable(thread),
    }, status=status)


@community_view
@require_GET
def thread_detail(request, pk, slug=""):
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
def thread_new(request):
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
    return render(request, "community/thread_form.html", {"form": form, "block": block, "thread": None},
                  status=400 if form.errors else 200)


def _thread_editable(thread):
    return thread.status == Thread.Status.PUBLISHED and not thread.is_deleted


def _own_thread_or_404(request, pk):
    """The signed-in user's own thread. Anyone else's is a 404, like a thread that does not exist."""
    thread = get_object_or_404(Thread.objects.select_related("board", "author"), pk=pk)
    if thread.author_id != request.user.pk or not can_see_thread(request.user, thread):
        raise Http404
    return thread


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def thread_edit(request, pk):
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
        "form": form, "block": block, "thread": thread, "title_editable": title_editable,
    }, status=400 if form.errors else 200)


def _may_clean_up(request):
    """Deleting your own post stays open to muted people (like unpublishing a project); not to suspended ones."""
    if request.user.is_suspended:
        return HttpResponseForbidden(write_blocked_message(request.user))
    if is_limited("community_delete", request.user.pk, limits.DELETES_PER_HOUR, limits.HOUR):
        return HttpResponseForbidden(TOO_MANY)
    return None


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def thread_delete(request, pk):
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
    """The reply being answered, from POST. (reply or None, error message or "")."""
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
def reply_create(request, pk):
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
            reply = services.create_reply(user, thread, parent, data["body"], data["sticker"], data["images"])
            return redirect(reply.get_absolute_url())
    return _render_thread(request, thread, form=form, parent=parent, status=400)


def _own_reply_or_404(request, pk):
    reply = get_object_or_404(Reply.objects.select_related("thread__board", "thread__author", "author"), pk=pk)
    if reply.author_id != request.user.pk or not can_see_thread(request.user, reply.thread):
        raise Http404
    return reply


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def reply_edit(request, pk):
    reply = _own_reply_or_404(request, pk)
    if not reply.is_alive or reply.thread.status != Thread.Status.PUBLISHED:
        return HttpResponseForbidden(_("This reply cannot be changed."))
    user = request.user
    block = post_block(user)
    if request.method == "POST" and block:
        return _blocked(request, block)
    form = ReplyEditForm(request.POST or None, user=user, initial={"body": reply.body},
                         has_extras=bool(reply.sticker_key) or reply.images.exists())
    if request.method == "POST" and form.is_valid():
        if is_limited("community_edit", user.pk, limits.EDITS_PER_HOUR, limits.HOUR):
            form.add_error(None, TOO_MANY)
        else:
            services.edit_reply(reply, form.cleaned_data["body"])
            return redirect(reply.get_absolute_url())
    return render(request, "community/reply_form.html", {"form": form, "reply": reply, "block": block},
                  status=400 if form.errors else 200)


@community_view
@login_required
@require_http_methods(["GET", "POST"])
def reply_delete(request, pk):
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


# ---------- Votes ----------

def _vote(request, target, thread):
    """Upvote or take it back: POST value=1 / value=0. JSON for fetch, a redirect for a plain form."""
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
        return fail(_("Bad request."), 400)
    if target.author_id == user.pk:
        return fail(_("You cannot vote for your own post."), 400)
    if thread.is_removed:
        raise Http404
    score = services.set_vote(user, target, request.POST["value"] == "1")
    if _wants_json(request):
        return JsonResponse({"ok": True, "voted": request.POST["value"] == "1", "score": score})
    return redirect(back)


def _signed_in_or_401(request):
    if request.user.is_authenticated:
        return None
    if _wants_json(request):
        return JsonResponse({"ok": False, "message": _("Sign in to do this.")}, status=401)
    return redirect_to_login(request.get_full_path())


@community_view
@require_POST
def vote_thread(request, pk):
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
    refusal = _signed_in_or_401(request)
    if refusal:
        return refusal
    reply = get_object_or_404(Reply.objects.select_related("thread__board", "thread__author", "author"), pk=pk)
    if not can_see_thread(request.user, reply.thread) or not reply.is_alive or author_hidden(reply.author):
        raise Http404
    return _vote(request, reply, reply.thread)

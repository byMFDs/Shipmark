"""/mod/: the moderation queue, report details and "Moderate" while browsing.

Moderator badge or superuser only (accounts.roles.can_moderate); everyone else gets a 404, so the pages do not
reveal that they exist. The decisions themselves live in moderation.decisions.
"""
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from accounts.roles import can_moderate, can_write
from config.ratelimit import is_limited
from projects.models import BuildLogEntry, Project

from . import audit, decisions, sanctions
from .forms import ActionForm
from .models import OPEN_STATES, Notice, Report, Sanction
from .visibility import visible_owner, visible_users

User = get_user_model()
PAGE_SIZE = 50


def moderator_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not can_moderate(request.user):
            raise Http404
        if request.method == "POST" and not can_write(request.user):
            return HttpResponseForbidden(_("A muted account cannot moderate."))
        return view(request, *args, **kwargs)
    return wrapper


# ---------- Queue ----------

STATUS_FILTERS = {
    "open": OPEN_STATES,
    "resolved": (Report.Status.RESOLVED,),
    "dismissed": (Report.Status.DISMISSED,),
    "all": None,
}
KIND_FILTERS = {"project": Q(project__isnull=False), "profile": Q(target_user__isnull=False),
                "entry": Q(log_entry__isnull=False)}


@moderator_required
@require_http_methods(["GET"])
def queue(request):
    status = request.GET.get("status") if request.GET.get("status") in STATUS_FILTERS else "open"
    kind = request.GET.get("kind") if request.GET.get("kind") in KIND_FILTERS else ""
    reason = request.GET.get("reason") if request.GET.get("reason") in Report.Reason.values else ""
    try:
        page = max(int(request.GET.get("page", 1)), 1)
    except ValueError:
        page = 1
    reports = Report.objects.select_related("reporter", "target_owner", "handled_by")
    if STATUS_FILTERS[status] is not None:
        reports = reports.filter(status__in=STATUS_FILTERS[status])
    if kind:
        reports = reports.filter(KIND_FILTERS[kind])
    if reason:
        reports = reports.filter(reason=reason)
    reports = reports.order_by("created_at" if status == "open" else "-handled_at", "pk")
    start = (page - 1) * PAGE_SIZE
    rows = list(reports[start:start + PAGE_SIZE + 1])
    counts = Report.objects.aggregate(
        open=Count("pk", filter=Q(status__in=OPEN_STATES)),
        resolved=Count("pk", filter=Q(status=Report.Status.RESOLVED)),
        dismissed=Count("pk", filter=Q(status=Report.Status.DISMISSED)),
    )
    return render(request, "moderation/mod/queue.html", {
        "reports": rows[:PAGE_SIZE], "has_next": len(rows) > PAGE_SIZE, "page": page,
        "status": status, "kind": kind, "reason": reason, "counts": counts,
        "reasons": Report.Reason.choices,
    })


# ---------- Report detail ----------

def _owner_history(owner, exclude_report=None):
    if owner is None:
        return None
    reports = Report.objects.filter(target_owner=owner).select_related("handled_by").order_by("-created_at")
    if exclude_report is not None:
        reports = reports.exclude(pk=exclude_report.pk)
    return {
        "person": owner,
        "sanctions": list(Sanction.objects.filter(user=owner).select_related("issued_by").order_by("-starts_at")[:20]),
        "reports": list(reports[:20]),
        "removed": list(owner.projects.filter(status=Project.Status.REMOVED).order_by("-removed_at")[:20]),
        "now": timezone.now(),
    }


def _protection(owner, actor):
    """The message to show when `actor` may not act on `owner`, or ""."""
    if owner is None:
        return ""
    try:
        sanctions.check_target(owner, actor)
    except PermissionDenied as error:
        return str(error)
    return ""


def _actions_for(kind, has_report):
    actions = ["dismiss"] if has_report else []
    actions += {"project": ["remove_project"], "profile": ["clear_profile"], "entry": ["remove_project"]}.get(kind, [])
    return actions + ["mute", "ban"]


def _perform(request, form, *, report, owner, project=None):
    """Runs the chosen decision. Returns None when done, or an HttpResponse for a refusal."""
    actor = request.user
    data = form.cleaned_data
    action, reason = data["action"], data["reason"].strip()
    if is_limited("mod_action", actor.pk, settings.MODERATION_ACTIONS_PER_HOUR, 3600):
        form.add_error(None, _("Too many moderation actions in a short time. Try again later."))
        return False
    try:
        if action == decisions.DISMISS:
            decisions.dismiss(report, actor, reason)
            messages.success(request, _("Report dismissed."))
        elif action == decisions.REMOVE_PROJECT:
            decisions.remove_project(project, actor, reason, report=report)
            messages.success(request, _("Project removed. The owner sees the reason."))
        elif action == decisions.CLEAR_PROFILE:
            decisions.clear_profile(owner, data["fields"], actor, reason, report=report)
            messages.success(request, _("Profile fields cleared."))
        else:
            decisions.sanction(owner, decisions.KINDS[action], actor, reason, data["timedelta"], report=report)
            messages.success(request, _("Muted.") if action == decisions.MUTE else _("Banned."))
    except PermissionDenied as error:
        return HttpResponseForbidden(str(error) or _("You cannot do this."))
    return None


def _target_of(report):
    """(kind, owner, project, entry) for a report; None parts when the target is gone."""
    entry = report.log_entry
    project = report.project or (entry.project if entry else None)
    owner = report.target_owner or (project.owner if project else report.target_user)
    return report.kind, owner, project, entry


@moderator_required
@require_http_methods(["GET", "POST"])
def report_detail(request, pk):
    report = get_object_or_404(
        Report.objects.select_related("reporter", "project__owner", "target_user", "log_entry__project__owner",
                                      "target_owner", "handled_by"), pk=pk)
    kind, owner, project, entry = _target_of(report)
    if request.method == "GET" and report.status == Report.Status.OPEN:
        report.status = Report.Status.IN_REVIEW
        report.save(update_fields=["status"])
        audit.log("moderation.report.in_review", report, actor=request.user)
    actions = _actions_for(kind, True) if report.is_open else []
    if owner is None and actions:
        actions = ["dismiss"]
    protected = _protection(owner, request.user)
    if protected:
        actions = ["dismiss"] if report.is_open else []
    form = ActionForm(request.POST or None, actions=actions, actor=request.user) if actions else None
    if request.method == "POST":
        if form is None:
            return HttpResponseForbidden(_("This report is closed."))
        if form.is_valid():
            if form.cleaned_data["action"] != "dismiss" and protected:
                return HttpResponseForbidden(protected)
            refusal = _perform(request, form, report=report, owner=owner, project=project)
            if refusal:
                return refusal
            if refusal is None:
                return redirect("moderation:queue")
    return render(request, "moderation/mod/report.html", {
        "report": report, "kind": kind, "owner": owner, "project": project, "entry": entry,
        "history": _owner_history(owner, exclude_report=report), "protected": protected, "form": form,
    })


# ---------- Moderate while browsing ----------

def _linked_report(actor, owner, target_repr, category, **target):
    """The newest open report about this target, or a new one in the moderator's name (one history)."""
    report = Report.objects.filter(status__in=OPEN_STATES, **target).order_by("-created_at").first()
    if report is None:
        report = Report.objects.create(
            reporter=actor, source=Report.Source.MODERATOR, target_owner=owner, target_repr=target_repr[:200],
            reason=category, status=Report.Status.IN_REVIEW, **target,
        )
        audit.log("moderation.report.opened", report, actor=actor, source="moderator")
    return report


def _act(request, *, kind, owner, target_repr, back, project=None, target):
    protected = _protection(owner, request.user)
    if protected:
        if request.method == "POST":
            return HttpResponseForbidden(protected)
        form = None
    else:
        form = ActionForm(request.POST or None, actions=_actions_for(kind, False), actor=request.user,
                          with_category=True)
    if request.method == "POST" and form.is_valid():
        report = _linked_report(request.user, owner, target_repr, form.cleaned_data["category"], **target)
        refusal = _perform(request, form, report=report, owner=owner, project=project)
        if refusal:
            return refusal
        if refusal is None:
            return redirect(back if url_has_allowed_host_and_scheme(back, None) else reverse("moderation:queue"))
    open_reports = Report.objects.filter(status__in=OPEN_STATES, **target).count()
    return render(request, "moderation/mod/act.html", {
        "kind": kind, "owner": owner, "target_repr": target_repr, "form": form, "protected": protected,
        "back": back, "open_reports": open_reports, "history": _owner_history(owner),
    })


def _public_project_qs():
    return visible_owner(Project.objects.filter(status=Project.Status.PUBLISHED)).select_related("owner")


@moderator_required
@require_http_methods(["GET", "POST"])
def act_project(request, pk):
    project = get_object_or_404(_public_project_qs(), pk=pk)
    return _act(request, kind="project", owner=project.owner, target_repr=str(project), project=project,
                back=project.get_absolute_url(), target={"project": project})


@moderator_required
@require_http_methods(["GET", "POST"])
def act_user(request, username):
    person = get_object_or_404(visible_users(User.objects.all()), username__iexact=username)
    return _act(request, kind="profile", owner=person, target_repr=str(person),
                back=reverse("accounts:profile", args=[person.username]), target={"target_user": person})


@moderator_required
@require_http_methods(["GET", "POST"])
def act_log_entry(request, pk):
    entry = get_object_or_404(BuildLogEntry.objects.select_related("project__owner"), pk=pk,
                              project__in=_public_project_qs())
    project = entry.project
    return _act(request, kind="entry", owner=project.owner, target_repr=f"{project} · {entry.text[:80]}",
                project=project, back=f"{project.get_absolute_url()}#log-{entry.pk}", target={"log_entry": entry})


# ---------- Notices ----------

@login_required
@require_POST
def dismiss_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk, user=request.user)  # someone else's: 404
    if notice.dismissed_at is None:
        notice.dismissed_at = timezone.now()
        notice.save(update_fields=["dismissed_at"])
    back = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(back, {request.get_host()}, require_https=request.is_secure()):
        back = "/"
    return redirect(back)

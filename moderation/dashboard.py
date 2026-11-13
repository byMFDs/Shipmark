"""Numbers for the admin dashboard and the sidebar badge."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.system import SYSTEM_USERNAME
from projects.models import Project
from verification.uptime import with_uptime

from .models import Report
from .visibility import visible_owner


def open_reports_badge(request):
    count = Report.objects.filter(status=Report.Status.OPEN).count()
    return count or None


def public_projects():
    """Published projects of users who are not suspended: what visitors can see."""
    return visible_owner(Project.objects.filter(status=Project.Status.PUBLISHED))


def hallmark_counts():
    """How many public projects hold each hallmark right now. One pass, no per-project queries."""
    projects = list(with_uptime(
        public_projects().select_related("repo_link").prefetch_related("domain_verifications")
    ))
    counts = {"authored": 0, "live": 0, "steady": 0}
    for project in projects:
        for mark in project.hallmarks:
            counts[mark.kind] += mark.earned
    return counts


def dashboard_callback(request, context):
    people = get_user_model().objects.exclude(username=SYSTEM_USERNAME)  # the system account is not a person
    week_ago = timezone.now() - timedelta(days=7)
    marks = hallmark_counts()
    open_reports = Report.objects.filter(status=Report.Status.OPEN)
    context.update({
        "stats": [
            {"label": _("Users"), "value": people.count()},
            {"label": _("Published projects"), "value": public_projects().count()},
            {"label": _("Signups, last 7 days"), "value": people.filter(date_joined__gte=week_ago).count()},
            {"label": _("Open reports"), "value": open_reports.count(),
             "link": reverse("admin:moderation_report_changelist") + "?status__exact=open"},
        ],
        "hallmark_stats": [
            {"label": _("Repo owner"), "value": marks["authored"]},
            {"label": _("Domain verified"), "value": marks["live"]},
            {"label": _("Steady"), "value": marks["steady"]},
        ],
        "latest_reports": list(open_reports.select_related("reporter").order_by("-created_at")[:5]),
    })
    from support.admin import can_view_inbox, unread_count  # only people with the support permission see it

    if can_view_inbox(request):
        context["support_stat"] = {
            "label": _("Unread support messages"), "value": unread_count(),
            "link": reverse("admin:support_supportmessage_changelist") + "?status__exact=new",
        }
    return context

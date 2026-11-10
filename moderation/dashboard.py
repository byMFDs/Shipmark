"""Numbers for the admin dashboard and the sidebar badge."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from projects.models import Project
from verification.uptime import with_uptime

from .models import Report


def open_reports_badge(request):
    count = Report.objects.filter(status=Report.Status.OPEN).count()
    return count or None


def public_projects():
    """Published projects of users who are not suspended: what visitors can see."""
    return Project.objects.filter(status=Project.Status.PUBLISHED, owner__is_suspended=False)


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
    User = get_user_model()
    week_ago = timezone.now() - timedelta(days=7)
    marks = hallmark_counts()
    open_reports = Report.objects.filter(status=Report.Status.OPEN)
    context.update({
        "stats": [
            {"label": _("Users"), "value": User.objects.count()},
            {"label": _("Published projects"), "value": public_projects().count()},
            {"label": _("Signups, last 7 days"), "value": User.objects.filter(date_joined__gte=week_ago).count()},
            {"label": _("Open reports"), "value": open_reports.count(),
             "link": reverse("admin:moderation_report_changelist") + "?status__exact=open"},
        ],
        "hallmark_stats": [
            {"label": _("Authored"), "value": marks["authored"]},
            {"label": _("Live"), "value": marks["live"]},
            {"label": _("Steady"), "value": marks["steady"]},
        ],
        "latest_reports": list(open_reports.select_related("reporter").order_by("-created_at")[:5]),
    })
    return context

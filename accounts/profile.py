"""Data for the public profile page."""
from django.db.models import Count

from projects.models import BuildLogEntry, Project, Tool
from social.queries import follower_count
from verification.uptime import with_uptime


def profile_projects(person):
    """Published projects of `person`, newest first. Others' drafts and hidden ones never appear."""
    return list(with_uptime(
        Project.objects.filter(owner=person, status=Project.Status.PUBLISHED)
        .prefetch_related("screenshots", "domain_verifications")
        .select_related("owner", "repo_link")
        .order_by("-launched_at", "-created_at")
    ))


def profile_drafts(person):
    """Unpublished and hidden projects. Shown to the owner only (the view checks that)."""
    return list(
        Project.objects.filter(owner=person).exclude(status=Project.Status.PUBLISHED)
        .prefetch_related("screenshots")
        .select_related("owner")
        .order_by("-updated_at")
    )


def profile_stats(person, projects=None):
    """Counts shown under the name. Hallmarks are counted over published projects only.

    Pass the list from `profile_projects` to avoid a second query. 
    """
    if projects is None:
        projects = profile_projects(person)
    hallmarks = sum(p.hallmarks.earned_count for p in projects)
    return {"projects": len(projects), "hallmarks": hallmarks, "followers": follower_count(person)}


TABS = ("projects", "log", "about")
LOG_SHOWN = 30
BUILT_WITH_SHOWN = 6


def profile_pinned(person, projects):
    """The pinned projects that are still public, in pin order. `projects` is the list from profile_projects,
    so a project that was unpublished, removed or hidden since is simply not there (no extra query)."""
    public = {p.pk: p for p in projects}
    return [public[pin.project_id] for pin in person.pins.all() if pin.project_id in public]


def profile_log(person):
    """Newest build-log updates across the person's published projects, with the project (one query)."""
    return list(
        BuildLogEntry.objects.filter(project__owner=person, project__status=Project.Status.PUBLISHED)
        .select_related("project__owner").order_by("-created_at", "-pk")[:LOG_SHOWN]
    )


def profile_built_with(person):
    """The AI tools used most often across published projects. Self-declared, so the page says so."""
    return list(
        Tool.objects.filter(projects__owner=person, projects__status=Project.Status.PUBLISHED)
        .annotate(n=Count("projects")).order_by("-n", "name")[:BUILT_WITH_SHOWN]
    )

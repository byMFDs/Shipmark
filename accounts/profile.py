"""Data for the public profile page."""
from projects.models import Project
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

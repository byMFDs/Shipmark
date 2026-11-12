"""Download my data": everything we store about one user, as JSON (CLAUDE.md section 12).

Only the user's own records. Other people appear only by their public username
(projects you liked, people you follow); nobody else's private data is included.
Keep docs/DATA_INVENTORY.md in sync when a model gets a new personal field.
"""
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.db.models import Prefetch
from django.utils import timezone

from community.models import CommunityImage, Reply, Thread, Vote
from config import branding
from moderation.models import Notice, Report, Sanction
from projects.models import BuildLogEntry, Project
from social.models import Follow, Like

FORMAT_VERSION = 1


def _dt(value):
    return value.isoformat() if value else None


def _profile(user, absolute):
    return {
        "username": user.username,
        "display_name": user.display_name,
        "headline": user.headline,
        "about": user.about,
        "location": user.location,
        "status": user.status,
        "skills": [tag.name for tag in user.skills.all()],
        "links": [{"kind": link.kind, "url": link.url} for link in user.links.all()],
        "pinned_projects": [pin.project.slug for pin in user.pins.select_related("project")],
        "avatar": absolute(user.avatar.url) if user.avatar else "",
        "avatar_source": user.avatar_source,
        "cover": absolute(user.cover.url) if user.cover else "",
        "email": user.email,
        "github_login": user.github_login,
        "avatar_url": user.avatar_url,
        "preferred_language": user.preferred_language,
        "date_joined": _dt(user.date_joined),
        "last_login": _dt(user.last_login),
        "terms_version_accepted": user.terms_version_accepted,
        "terms_accepted_at": _dt(user.terms_accepted_at),
        "is_suspended": user.is_suspended,
    }


def _github(user):
    accounts = SocialAccount.objects.filter(user=user, provider="github")
    return {
        # What GitHub sent at the latest sign-in (allauth keeps it as is).
        "accounts": [
            {"uid": a.uid, "date_joined": _dt(a.date_joined), "last_login": _dt(a.last_login), "data": a.extra_data}
            for a in accounts
        ],
        "email_addresses": [
            {"email": e.email, "primary": e.primary, "verified": e.verified}
            for e in EmailAddress.objects.filter(user=user)
        ],
    }


def _project(project, absolute):
    repo = getattr(project, "repo_link", None)
    return {
        "name": project.name,
        "slug": project.slug,
        "url": absolute(project.get_absolute_url()),
        "status": project.status,
        "tagline": project.tagline,
        "description": project.description,
        "live_url": project.live_url,
        "repo_full_name": project.repo_full_name,
        "tags": [t.name for t in project.tags.all()],
        "built_with_self_declared": [t.name for t in project.built_with.all()],
        "launched_at": _dt(project.launched_at),
        "created_at": _dt(project.created_at),
        "updated_at": _dt(project.updated_at),
        "screenshots": [absolute(s.image.url) for s in project.screenshots.all() if s.image],
        "repository_check": {
            "repo_full_name": repo.repo_full_name,
            "github_repo_id": repo.github_repo_id,
            "github_owner_id": repo.github_owner_id,
            "is_owner": repo.is_owner,
            "token_file_found": repo.token_file_found,
            "repo_created_at": _dt(repo.repo_created_at),
            "homepage": repo.homepage,
            "root_commit_sha": repo.root_commit_sha,
            "root_commit_at": _dt(repo.root_commit_at),
            "user_commit_count": repo.user_commit_count,
            "first_commit_at": _dt(repo.first_commit_at),
            "last_commit_at": _dt(repo.last_commit_at),
            "active_weeks": repo.active_weeks,
            # The person has a right to see why a review is pending; the public page never says it.
            "review_state": repo.review_state,
            "review_reasons": repo.review_reasons,
            "reviewed_at": _dt(repo.reviewed_at),
            "checked_at": _dt(repo.checked_at),
            "earned_at": _dt(repo.earned_at),
        } if repo else None,
        "domain_verifications": [
            {
                "domain": d.domain, "method": d.method, "status": d.status, "created_at": _dt(d.created_at),
                "verified_at": _dt(d.verified_at), "last_confirmed_at": _dt(d.last_confirmed_at),
            }
            for d in project.domain_verifications.all()
        ],
        "build_log": [
            {"kind": e.kind, "text": e.text, "created_at": _dt(e.created_at)}
            for e in project.log_entries.all()
        ],
    }


def _community(user, absolute):
    """The person's threads, replies, images and upvotes. Text they deleted is not stored any more, so it is
    not here either; a post removed by moderators is included with the reason."""
    images = {}
    for image in CommunityImage.objects.filter(uploader=user).order_by("order", "id"):
        images.setdefault(("thread", image.thread_id) if image.thread_id else ("reply", image.reply_id), []).append(
            {"url": absolute(image.image.url), "width": image.width, "height": image.height, "alt": image.alt})
    votes = Vote.objects.filter(user=user).select_related("thread", "reply__thread").order_by("created_at", "id")
    return {
        "threads": [
            {
                "url": absolute(t.get_absolute_url()), "board": t.board.slug, "title": t.title, "text": t.body,
                "status": t.status, "pinned": t.pinned, "created_at": _dt(t.created_at), "edited_at": _dt(t.edited_at),
                "deleted_at": _dt(t.deleted_at), "removed_at": _dt(t.removed_at), "removed_reason": t.removed_reason,
                "images": images.get(("thread", t.pk), []),
            }
            for t in Thread.objects.filter(author=user).select_related("board").order_by("created_at", "id")
        ],
        "replies": [
            {
                "url": absolute(r.get_absolute_url()), "thread": r.thread.title, "text": r.body,
                "sticker": r.sticker_key, "status": r.status, "created_at": _dt(r.created_at),
                "edited_at": _dt(r.edited_at), "deleted_at": _dt(r.deleted_at), "removed_at": _dt(r.removed_at),
                "removed_reason": r.removed_reason, "images": images.get(("reply", r.pk), []),
            }
            for r in Reply.objects.filter(author=user).select_related("thread").order_by("created_at", "id")
        ],
        "upvotes": [
            {"url": absolute((v.thread or v.reply).get_absolute_url()), "created_at": _dt(v.created_at)}
            for v in votes
        ],
    }


def build_export(user, absolute=lambda url: url):
    """A JSON-ready dict. `absolute` turns site paths into full URLs (config.site.absolute_url: SITE_URL)."""
    projects = (
        Project.objects.filter(owner=user)
        .select_related("owner", "repo_link")
        .prefetch_related(
            "tags", "built_with", "screenshots", "domain_verifications",
            Prefetch("log_entries", queryset=BuildLogEntry.objects.order_by("created_at", "id")),
        )
        .order_by("created_at", "id")
    )
    likes = Like.objects.filter(user=user).select_related("project__owner").order_by("created_at", "id")
    follows = Follow.objects.filter(follower=user).select_related("following").order_by("created_at", "id")
    reports = Report.objects.filter(reporter=user).order_by("created_at", "id")
    return {
        "format_version": FORMAT_VERSION,
        "site": branding.SITE_NAME,
        "exported_at": _dt(timezone.now()),
        "profile": _profile(user, absolute),
        "github": _github(user),
        "projects": [_project(p, absolute) for p in projects],
        "likes": [
            {"project": f"{like.project.owner.username}/{like.project.slug}", "created_at": _dt(like.created_at)}
            for like in likes
        ],
        "following": [{"username": f.following.username, "created_at": _dt(f.created_at)} for f in follows],
        "community": _community(user, absolute),
        "reports_made": [
            {
                "target": r.target_repr, "reason": r.reason, "details": r.details,
                "status": r.status, "created_at": _dt(r.created_at),
            }
            for r in reports
        ],
        # Moderation decisions about you. Who reported you is never included.
        "sanctions": [
            {
                "kind": s.kind, "reason": s.reason, "starts_at": _dt(s.starts_at), "expires_at": _dt(s.expires_at),
                "revoked_at": _dt(s.revoked_at),
            }
            for s in Sanction.objects.filter(user=user).order_by("starts_at", "id")
        ],
        "notices": [
            {"kind": n.kind, "about": n.target_repr, "reason": n.reason, "created_at": _dt(n.created_at),
             "dismissed_at": _dt(n.dismissed_at)}
            for n in Notice.objects.filter(user=user).order_by("created_at", "id")
        ],
    }

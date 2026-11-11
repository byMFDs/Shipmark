"""Repository authorship check: the Authored hallmark (CLAUDE.md section 2).

Talks only to the fixed host api.github.com. The user controls just the "owner/name" part,
which is validated strictly and URL-encoded, so it cannot change the host or path.
(The `safe_fetch` guard is for user-supplied URLs; there is none here.)

Identity is always compared by GitHub's numeric ids, never by names: the user by account id, the
repository by repo id, its owner by owner id. Names can be renamed, and a freed name can be taken by
someone else (a deleted repo recreated under the same name is a different repository).
Only repositories that earn Authored are stored (see RepoLink). Every removal is logged (AuditLog).
"""
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs, quote, urlsplit

import httpx
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from config import branding
from moderation import audit
from projects.proof import MIN_AUTHORED_COMMITS

from .models import RepoLink

logger = logging.getLogger(__name__)

API = "https://api.github.com"
TIMEOUT = 6  # seconds per request
DEADLINE = 25  # seconds for the whole check, so a slow GitHub cannot hold a worker for long
CONTRIBUTORS_PAGES = 5  # 5 x 100 contributors, sorted by commits. Beyond that we say "too large".
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,39}/[A-Za-z0-9_.-]{1,100}$")
# Where GitHub points a renamed or transferred repository: GET /repos/old/name -> 301 to this.
MOVED_RE = re.compile(r"^https://api\.github\.com/repositories/(\d{1,15})(?:[/?]|$)")

# Outcomes after a successful look at GitHub.
AUTHORED, TOO_FEW, NOT_YOURS = "authored", "too_few", "not_yours"


class RepoCheckError(Exception):
    """The check could not finish. `message` is user-facing (already translated)."""

    def __init__(self, code, message, moved_to=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.moved_to = moved_to  # repo id from a 301, when GitHub says where the repository went


@dataclass
class RepoFacts:
    full_name: str
    repo_id: int
    owner_id: int
    is_owner: bool
    commit_count: int
    first_commit_at: datetime | None = None
    last_commit_at: datetime | None = None


@dataclass
class CheckResult:
    outcome: str
    facts: RepoFacts


def is_authored(is_owner, commit_count):
    return is_owner or commit_count >= MIN_AUTHORED_COMMITS


# ---------- GitHub API ----------

class _Api:
    def __init__(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"{branding.SITE_NAME}-repo-check",
        }
        token = getattr(settings, "GITHUB_API_TOKEN", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(base_url=API, headers=headers, timeout=TIMEOUT, follow_redirects=False)
        self.started = time.monotonic()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.client.close()

    def get(self, path, params=None):
        """GET and return the response, or raise RepoCheckError. `path` is built from validated parts."""
        if time.monotonic() - self.started > DEADLINE:
            raise _unavailable()
        try:
            response = self.client.get(path, params=params)
        except httpx.HTTPError as exc:
            logger.warning("GitHub request failed: %s", exc.__class__.__name__)
            raise _unavailable() from exc
        _raise_for_status(response)
        return response

    def json(self, path, params=None):
        response = self.get(path, params)
        if response.status_code == 204 or not response.content:
            return None, response
        try:
            return response.json(), response
        except ValueError as exc:
            raise _unavailable() from exc


def _unavailable():
    return RepoCheckError("unavailable", _("GitHub did not answer properly. Try again in a few minutes."))


def _rate_limited(response):
    wait = None
    if response.headers.get("retry-after", "").isdigit():
        wait = int(response.headers["retry-after"])
    elif response.headers.get("x-ratelimit-reset", "").isdigit():
        wait = int(response.headers["x-ratelimit-reset"]) - int(time.time())
    if wait is not None and wait > 0:
        minutes = max(1, -(-wait // 60))
        return RepoCheckError(
            "rate_limited",
            _("GitHub's rate limit was reached. Try again in about %(minutes)s min.") % {"minutes": minutes},
        )
    return RepoCheckError("rate_limited", _("GitHub's rate limit was reached. Try again later."))


def _raise_for_status(response):
    status = response.status_code
    if status in (200, 204):  # 204: an empty repository has no contributors
        return
    if status in (301, 302, 307, 308):
        match = MOVED_RE.match(response.headers.get("location", ""))
        raise RepoCheckError("moved", _("This repository was renamed or moved. Enter its current name."),
                             moved_to=int(match.group(1)) if match else None)
    if status in (404, 410, 451):
        raise RepoCheckError(
            "not_found",
            _("Repository not found. Check the spelling. Private repositories cannot be checked."),
        )
    if status == 429 or (status == 403 and (
        response.headers.get("x-ratelimit-remaining") == "0"
        or "retry-after" in response.headers
        or "rate limit" in response.text.lower()
    )):
        raise _rate_limited(response)
    if status == 403 and "too large" in response.text.lower():
        raise RepoCheckError("too_large", _("This repository is too large to check automatically."))
    if status == 401:
        logger.error("GitHub rejected GITHUB_API_TOKEN")
    raise _unavailable()


def _parse_time(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def _commit_time(commits):
    try:
        return _parse_time(commits[0]["commit"]["author"]["date"])
    except (IndexError, KeyError, TypeError):
        return None


def _last_page(response):
    """Page number of the last page from the Link header (per_page=1 makes it the commit count)."""
    link = response.links.get("last")
    if not link:
        return 1
    try:
        return int(parse_qs(urlsplit(link["url"]).query)["page"][0])
    except (KeyError, IndexError, ValueError):
        return 1


def _valid_name(full_name):
    return bool(REPO_RE.match(full_name or "")) and not any(part in (".", "..") for part in full_name.split("/"))


def _base(full_name):
    owner_name, repo_name = full_name.split("/")
    return f"/repos/{quote(owner_name, safe='')}/{quote(repo_name, safe='')}"


def _repo_json(api, full_name):
    """GET /repos/{full_name}, following one rename/transfer redirect by repo id. Checked shape."""
    try:
        repo, _response = api.json(_base(full_name))
    except RepoCheckError as exc:
        if exc.code != "moved" or exc.moved_to is None:
            raise
        repo, _response = api.json(f"/repositories/{exc.moved_to}")
    return _checked(repo)


def _checked(repo):
    if (not isinstance(repo, dict) or not isinstance(repo.get("owner"), dict) or not isinstance(repo.get("id"), int)
            or not isinstance(repo["owner"].get("id"), int) or not _valid_name(str(repo.get("full_name") or ""))):
        raise _unavailable()
    return repo


def repo_by_id(api, repo_id):
    """GET /repositories/{id}: the repository with this id, whatever its name is now. 404 = deleted or private."""
    return _checked(api.json(f"/repositories/{int(repo_id)}")[0])


def identity_change(link, repo_id, owner_id, full_name):
    """How the repository GitHub shows now differs from the stored link, by ids first.

    "recreated": another repository id (the old one was deleted, or the name now points elsewhere);
    "transferred": same repository, another owner account; "renamed": same ids, another name; None: same.
    """
    if link is None:
        return None
    if link.github_repo_id != repo_id:
        return "recreated"
    if link.github_owner_id is not None and link.github_owner_id != owner_id:
        return "transferred"
    if link.repo_full_name.lower() != full_name.lower():
        return "renamed"
    return None


def fetch_facts(full_name, github_user_id, project=None):
    """Ask GitHub about the repository. Raises RepoCheckError; never returns partial garbage.

    `project` is the project asking: its own existing link does not count as "taken".
    """
    if not _valid_name(full_name):
        raise RepoCheckError("invalid", _("Use the form owner/name, for example octocat/hello-world."))

    with _Api() as api:
        repo = _repo_json(api, full_name)
        if repo.get("private"):
            raise RepoCheckError("private", _("This repository is private. Only public repositories can be checked."))
        base = _base(repo["full_name"])  # the current name, after a rename

        facts = RepoFacts(
            full_name=str(repo["full_name"]),
            repo_id=repo["id"],
            owner_id=repo["owner"]["id"],
            # A fork is not authorship: forking someone's project must not earn the mark.
            is_owner=repo["owner"].get("id") == github_user_id
            and repo["owner"].get("type") == "User"
            and not repo.get("fork"),
            commit_count=0,
        )
        if _taken(facts, project):  # fail early, before spending more API calls
            raise RepoCheckError("taken", _("This repository is already linked to another project."))

        login = _find_contributor(api, base, github_user_id, facts)
        if facts.commit_count and login:
            commits_path = f"{base}/commits"
            latest, response = api.json(commits_path, {"author": login, "per_page": 1})
            facts.last_commit_at = _commit_time(latest)
            pages = _last_page(response)
            if pages > 1:
                oldest, _response = api.json(commits_path, {"author": login, "per_page": 1, "page": pages})
                facts.first_commit_at = _commit_time(oldest)
            else:
                facts.first_commit_at = facts.last_commit_at
        return facts


def _find_contributor(api, base, github_user_id, facts):
    """Fill facts.commit_count from the contributors endpoint. Returns the user's login or None."""
    for page in range(1, CONTRIBUTORS_PAGES + 1):
        try:
            people, _response = api.json(f"{base}/contributors", {"per_page": 100, "page": page})
        except RepoCheckError as exc:
            # An empty repository answers 204 (no JSON) and a huge one 403: only the owner can still pass.
            if exc.code == "too_large" and facts.is_owner:
                return None
            raise
        if not isinstance(people, list):
            return None  # empty repository
        for person in people:
            if isinstance(person, dict) and person.get("id") == github_user_id:
                facts.commit_count = int(person.get("contributions") or 0)
                return person.get("login")
        if len(people) < 100:
            return None
    return None


# ---------- Storing the result ----------

def _taken(facts, project):
    qs = RepoLink.objects.filter(Q(github_repo_id=facts.repo_id) | Q(repo_full_name__iexact=facts.full_name))
    if project is not None:
        qs = qs.exclude(project=project)
    return qs.exists()


def remove_link(project, reason, actor=None, **metadata):
    """Delete the project's RepoLink (Repo owner is gone) and log it. Returns True if there was one."""
    link = RepoLink.objects.filter(project=project).first()
    if link is None:
        return False
    with transaction.atomic():
        audit.log("hallmark.authored.removed", project, actor=actor, repo=link.repo_full_name,
                  repo_id=link.github_repo_id, reason=reason, **metadata)
        link.delete()
    return True


def _follow_rename(project, link, facts, actor):
    """Same ids, new name on GitHub: keep the project pointing at its repository's current name."""
    if project.repo_full_name.lower() == facts.full_name.lower():
        return
    audit.log("repo.renamed", project, actor=actor, old=project.repo_full_name, new=facts.full_name,
              repo_id=facts.repo_id)
    project.repo_full_name = facts.full_name
    project.save(update_fields=["repo_full_name"])


def run_check(project, github_user_id, actor=None):
    """Check `project.repo_full_name` for its owner and store the result. Returns CheckResult.

    A definite "no" (gone, private, not authored) removes the project's old RepoLink, so the
    hallmark disappears. A temporary problem (rate limit, GitHub down) leaves everything as it was.
    """
    try:
        facts = fetch_facts(project.repo_full_name, github_user_id, project)
    except RepoCheckError as exc:
        if exc.code in ("not_found", "private", "moved", "taken", "invalid"):
            remove_link(project, exc.code, actor=actor)
        raise

    old = RepoLink.objects.filter(project=project).first()
    change = identity_change(old, facts.repo_id, facts.owner_id, facts.full_name)
    if change in ("recreated", "transferred"):
        remove_link(project, change, actor=actor, new_repo_id=facts.repo_id, new_owner_id=facts.owner_id)

    if not is_authored(facts.is_owner, facts.commit_count):
        remove_link(project, "not_authored", actor=actor)
        outcome = TOO_FEW if facts.commit_count else NOT_YOURS
        return CheckResult(outcome, facts)

    _follow_rename(project, old, facts, actor)
    try:
        with transaction.atomic():
            RepoLink.objects.update_or_create(project=project, defaults={
                "repo_full_name": facts.full_name,
                "github_repo_id": facts.repo_id,
                "github_owner_id": facts.owner_id,
                "is_owner": facts.is_owner,
                "user_commit_count": facts.commit_count,
                "first_commit_at": facts.first_commit_at,
                "last_commit_at": facts.last_commit_at,
                "checked_at": timezone.now(),
            })
    except IntegrityError as exc:  # another project linked it between our check and the save
        raise RepoCheckError("taken", _("This repository is already linked to another project.")) from exc
    return CheckResult(AUTHORED, facts)

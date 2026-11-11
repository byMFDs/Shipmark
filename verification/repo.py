"""Repository check: the Repo owner hallmark (id `authored`, CLAUDE.md section 2).

Repo owner is earned by a public, non-fork repository that is either owned by the user's personal
GitHub account, or (for organisation and team repositories) has the project's verification file
`.shipmark-verify` on its default branch, which only someone with write access can add.
It says who controls the repository, never who wrote the code. The other facts read here
(commit count and dates, history start, active weeks) are shown as facts; three of them send the
link to a manual review instead of earning the mark (`review_reasons`).

Talks only to the fixed host api.github.com. The user controls just the "owner/name" part,
which is validated strictly and URL-encoded, so it cannot change the host or path.
(The `safe_fetch` guard is for user-supplied URLs; there is none here.)

Identity is always compared by GitHub's numeric ids, never by names: the user by account id, the
repository by repo id, its owner by owner id. Names can be renamed, and a freed name can be taken by
someone else (a deleted repo recreated under the same name is a different repository).
Only repositories that earn Authored are stored (see RepoLink). Every removal is logged (AuditLog).
"""
import base64
import hmac
import logging
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import parse_qs, quote, urlsplit

import httpx
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from config import branding
from moderation import audit
from .models import Block, RepoLink

logger = logging.getLogger(__name__)

API = "https://api.github.com"
TIMEOUT = 6  # seconds per request
DEADLINE = 25  # seconds for the whole check, so a slow GitHub cannot hold a worker for long
CONTRIBUTORS_PAGES = 5  # 5 x 100 contributors, sorted by commits. Beyond that we say "too large".
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,39}/[A-Za-z0-9_.-]{1,100}$")
TOKEN_FILE = f".{branding.VERIFY_TOKEN_NAME}"  # ".shipmark-verify" in the repository root
TOKEN_FILE_MAX = 1024  # bytes; the file holds one 32-character token
# Where GitHub points a renamed or transferred repository: GET /repos/old/name -> 301 to this.
MOVED_RE = re.compile(r"^https://api\.github\.com/repositories/(\d{1,15})(?:[/?]|$)")

# Outcomes after a successful look at GitHub.
AUTHORED, NOT_YOURS, FORK = "authored", "not_yours", "fork"
# Why a link waits for a manual review (RepoLink.review_reasons). Facts, not accusations.
IMPORTED_HISTORY = "imported_history"  # first commit much older than the repository on GitHub
DUPLICATE_HISTORY = "duplicate_history"  # same first commit as a repository linked to another project
NO_OWNER_COMMITS = "no_owner_commits"  # GitHub shows no commits by the owner


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
    is_owner: bool  # personal account of the user, not a fork
    commit_count: int  # commits by the user on the default branch (GitHub's contributors list)
    token_file: bool = False  # the project's verification file is on the default branch
    is_fork: bool = False
    repo_created_at: datetime | None = None
    homepage: str = ""
    first_commit_at: datetime | None = None  # the user's first and last commit
    last_commit_at: datetime | None = None
    root_commit_sha: str = ""  # the oldest commit of the default branch
    root_commit_at: datetime | None = None
    active_weeks: int | None = None  # None: GitHub is still computing its statistics
    review_reasons: list = field(default_factory=list)


@dataclass
class CheckResult:
    outcome: str
    facts: RepoFacts
    link: object = None  # the stored RepoLink when the outcome is AUTHORED


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
    if status in (200, 202, 204):  # 202: statistics still being computed; 204: empty repository
        return
    if status == 409:  # GET /commits on a repository without commits
        raise RepoCheckError("empty", _("This repository has no commits yet."))
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


def _commit_sha(commits):
    try:
        sha = str(commits[0]["sha"])
    except (IndexError, KeyError, TypeError):
        return ""
    return sha if re.fullmatch(r"[0-9a-f]{40}", sha) else ""


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


def _homepage(value):
    """The repository's Website field, kept only when it is a plain http(s) address."""
    value = str(value or "").strip()
    return value if len(value) <= 200 and value.lower().startswith(("http://", "https://")) else ""


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
        if Block.repo_blocked(repo["id"]):
            raise RepoCheckError("blocked", _("This repository cannot be linked. If you think this is a mistake, "
                                              "write to us."))
        if repo.get("private"):
            raise RepoCheckError("private", _("This repository is private. Only public repositories can be checked."))
        base = _base(repo["full_name"])  # the current name, after a rename

        facts = RepoFacts(
            full_name=str(repo["full_name"]),
            repo_id=repo["id"],
            owner_id=repo["owner"]["id"],
            is_fork=bool(repo.get("fork")),
            # A fork is someone else's project: it never earns the mark (on any path).
            is_owner=repo["owner"].get("id") == github_user_id
            and repo["owner"].get("type") == "User"
            and not repo.get("fork"),
            commit_count=0,
            repo_created_at=_parse_time(repo.get("created_at")),
            homepage=_homepage(repo.get("homepage")),
        )
        if facts.is_fork:
            return facts  # refused anyway: no need to spend more API calls
        facts.token_file = _has_token_file(api, base, getattr(project, "repo_token", None))
        if not (facts.is_owner or facts.token_file):
            return facts
        if _taken(facts, project):  # fail early, before spending more API calls
            raise RepoCheckError("taken", _("This repository is already linked to another project."))

        login = _find_contributor(api, base, github_user_id, facts)
        commits_path = f"{base}/commits"
        if facts.commit_count and login:
            facts.last_commit_at, facts.first_commit_at, _sha = _newest_and_oldest(api, commits_path, {"author": login})
        _newest, facts.root_commit_at, facts.root_commit_sha = _newest_and_oldest(api, commits_path, {})
        facts.active_weeks = _active_weeks(api, base, github_user_id)
        return facts


def repo_token_for(project):
    """The project's verification-file token, made on first use. Random and unique, never reused."""
    if project.repo_token:
        return project.repo_token
    from projects.models import Project  # here: projects imports this module

    for _attempt in range(3):
        token = secrets.token_hex(16)
        try:
            with transaction.atomic():
                updated = Project.objects.filter(pk=project.pk, repo_token__isnull=True).update(repo_token=token)
        except IntegrityError:  # astronomically unlikely collision: try another
            continue
        if not updated:  # a parallel request made it first
            token = Project.objects.values_list("repo_token", flat=True).get(pk=project.pk)
        project.repo_token = token
        return token
    raise RuntimeError("could not make a unique repo token")


def _has_token_file(api, base, token):
    """True when the default branch has TOKEN_FILE with exactly this project's token (spaces around ignored)."""
    if not token:
        return False
    try:
        data, _response = api.json(f"{base}/contents/{TOKEN_FILE}")
    except RepoCheckError as exc:
        if exc.code == "not_found":  # no such file (or an empty repository)
            return False
        raise
    if (not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64"
            or not isinstance(data.get("size"), int) or data["size"] > TOKEN_FILE_MAX):
        return False
    try:
        content = base64.b64decode(str(data.get("content") or ""), validate=False).decode("utf-8").strip()
    except (ValueError, UnicodeDecodeError):
        return False
    return hmac.compare_digest(content.encode(), token.encode())


def _newest_and_oldest(api, path, params):
    """(newest date, oldest date, oldest sha) of a commit list, in at most two requests. Empty repo: Nones."""
    try:
        newest, response = api.json(path, {**params, "per_page": 1})
    except RepoCheckError as exc:
        if exc.code == "empty":
            return None, None, ""
        raise
    pages = _last_page(response)
    oldest = api.json(path, {**params, "per_page": 1, "page": pages})[0] if pages > 1 else newest
    return _commit_time(newest), _commit_time(oldest), _commit_sha(oldest)


def _active_weeks(api, base, github_user_id):
    """Weeks with at least one commit by the user that changed lines, from GitHub's statistics.

    Only the user's own entry is read, so bots never count. Weeks with commits but no changed lines
    (empty commits) do not count. None when GitHub is still computing (202) or did not answer:
    it is only a fact, so the weekly re-check simply fills it in later.
    """
    try:
        data, response = api.json(f"{base}/stats/contributors")
    except RepoCheckError as exc:
        if exc.code == "rate_limited":
            raise
        return None
    if response.status_code == 202:
        return None
    if not isinstance(data, list):
        return 0  # 204: no commits
    for entry in data:
        author = entry.get("author") if isinstance(entry, dict) else None
        if not isinstance(author, dict) or author.get("id") != github_user_id or author.get("type") == "Bot":
            continue
        weeks = [w for w in entry.get("weeks") or [] if isinstance(w, dict) and (w.get("c") or 0) > 0]
        if weeks and not any((w.get("a") or 0) + (w.get("d") or 0) for w in weeks):
            return len(weeks)  # GitHub does not count lines for repositories with 10,000+ commits
        return sum(1 for w in weeks if (w.get("a") or 0) + (w.get("d") or 0) > 0)
    return 0


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


def review_reasons(facts, project):
    """Facts that send a link to a manual review instead of earning Repo owner at once."""
    reasons = []
    if facts.commit_count == 0:
        reasons.append(NO_OWNER_COMMITS)
    margin = timedelta(days=settings.TRUST_IMPORTED_HISTORY_DAYS)
    if facts.root_commit_at and facts.repo_created_at and facts.root_commit_at < facts.repo_created_at - margin:
        reasons.append(IMPORTED_HISTORY)
    if facts.root_commit_sha and (RepoLink.objects.filter(root_commit_sha=facts.root_commit_sha)
                                  .exclude(project=project).exists()):
        reasons.append(DUPLICATE_HISTORY)
    return reasons


def next_review_state(link, reasons):
    """Review state after a check. Staff approval survives re-checks unless a new reason appears."""
    Review = RepoLink.Review
    if link is not None and link.review_state == Review.APPROVED and set(reasons) <= set(link.review_reasons):
        return Review.APPROVED
    return Review.NEEDS_REVIEW if reasons else Review.CLEAR


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


def mark_recheck(link, reason, actor=None, **metadata):
    """Withhold the mark until the next full check, without deleting the link. Logged."""
    if link.review_state == RepoLink.Review.NEEDS_RECHECK:
        return False
    with transaction.atomic():
        link.review_state = RepoLink.Review.NEEDS_RECHECK
        link.save(update_fields=["review_state"])
        audit.log("hallmark.authored.needs_recheck", link.project, actor=actor, repo=link.repo_full_name,
                  reason=reason, **metadata)
    return True


def follow_rename(project, link, facts, actor):
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
        if exc.code in ("not_found", "private", "moved", "taken", "invalid", "blocked"):
            remove_link(project, exc.code, actor=actor)
        raise

    old = RepoLink.objects.filter(project=project).first()
    change = identity_change(old, facts.repo_id, facts.owner_id, facts.full_name)
    if change in ("recreated", "transferred"):
        remove_link(project, change, actor=actor, new_repo_id=facts.repo_id, new_owner_id=facts.owner_id)

    if facts.is_fork or not (facts.is_owner or facts.token_file):
        remove_link(project, "fork" if facts.is_fork else "not_owner", actor=actor)
        return CheckResult(FORK if facts.is_fork else NOT_YOURS, facts)

    follow_rename(project, old, facts, actor)
    if change in ("recreated", "transferred"):
        old = None
    try:
        link = store_link(project, facts, old, actor)
    except IntegrityError as exc:  # another project linked it between our check and the save
        raise RepoCheckError("taken", _("This repository is already linked to another project.")) from exc
    return CheckResult(AUTHORED, facts, link)


def store_link(project, facts, old, actor=None):
    """Save the facts of a repository that passed, with its review state, and log state changes."""
    facts.review_reasons = review_reasons(facts, project)
    state = next_review_state(old, facts.review_reasons)
    now = timezone.now()
    values = {
        "repo_full_name": facts.full_name,
        "github_repo_id": facts.repo_id,
        "github_owner_id": facts.owner_id,
        "is_owner": facts.is_owner,
        "token_file_found": facts.token_file,
        "user_commit_count": facts.commit_count,
        "first_commit_at": facts.first_commit_at,
        "last_commit_at": facts.last_commit_at,
        "repo_created_at": facts.repo_created_at,
        "homepage": facts.homepage,
        "root_commit_sha": facts.root_commit_sha,
        "root_commit_at": facts.root_commit_at,
        "review_state": state,
        "review_reasons": facts.review_reasons if state != RepoLink.Review.APPROVED else old.review_reasons,
        "checked_at": now,
    }
    if facts.active_weeks is not None:  # keep the last known number while GitHub recomputes
        values["active_weeks"] = facts.active_weeks
        values["stats_checked_at"] = now
    was_verified = old is not None and old.is_verified
    with transaction.atomic():
        link, created = RepoLink.objects.update_or_create(project=project, defaults=values)
        if link.is_verified and not was_verified and not created:  # the current run of the mark starts now
            link.earned_at = now
            link.save(update_fields=["earned_at"])
        was = "" if created or old is None else old.review_state
        if state == RepoLink.Review.NEEDS_REVIEW and was != state:
            audit.log("hallmark.authored.needs_review", project, actor=actor, repo=link.repo_full_name,
                      reasons=facts.review_reasons)
        elif link.is_verified and (created or was in (RepoLink.Review.NEEDS_REVIEW, RepoLink.Review.NEEDS_RECHECK)):
            audit.log("hallmark.authored.earned", project, actor=actor, repo=link.repo_full_name)
    return link


# ---------- Re-verification (reverify_repos) ----------

REVERIFY_REMOVE = ("not_found", "private", "blocked")  # definite answers from GitHub or staff


def reverify_link(link, actor=None):
    """Check a stored link again: by repo id first, then the facts. Returns the outcome:

    "confirmed" (still passes), "review" (passes, waits for a review), "removed" (definite: gone,
    private, another repository or owner, blocked) or "kept" (GitHub did not answer properly:
    nothing changes, the next run tries again). A rate limit is raised, so the command can stop.
    Every change is logged in AuditLog (by remove_link, mark_recheck, follow_rename, store_link).
    """
    from accounts.github import github_id  # here: accounts imports projects, which imports this module

    project = link.project
    try:
        with _Api() as api:
            repo = repo_by_id(api, link.github_repo_id)
    except RepoCheckError as exc:
        if exc.code == "rate_limited":
            raise
        if exc.code == "not_found":  # deleted, or private (both look the same to a public request)
            remove_link(project, "gone", actor=actor, source="reverify")
            return "removed"
        return "kept"
    user_id = github_id(project.owner)
    if user_id is None:  # the GitHub sign-in is gone: nothing to compare the owner with
        mark_recheck(link, "no_github_account", actor=actor, source="reverify")
        return "review"
    try:
        facts = fetch_facts(repo["full_name"], user_id, project)
    except RepoCheckError as exc:
        if exc.code == "rate_limited":
            raise
        if exc.code in REVERIFY_REMOVE:
            remove_link(project, exc.code, actor=actor, source="reverify")
            return "removed"
        return "kept"
    change = identity_change(link, facts.repo_id, facts.owner_id, facts.full_name)
    if change in ("recreated", "transferred") or facts.is_fork or not (facts.is_owner or facts.token_file):
        reason = (change if change in ("recreated", "transferred") else "fork" if facts.is_fork
                  else "token_file_missing" if link.token_file_found else "not_owner")
        remove_link(project, reason, actor=actor, source="reverify")
        return "removed"
    follow_rename(project, link, facts, actor)
    link = store_link(project, facts, link, actor)
    return "review" if link.review_state == RepoLink.Review.NEEDS_REVIEW else "confirmed"


def due_links(now=None):
    """Links to re-check: not checked for TRUST_REVERIFY_REPOS_DAYS, waiting for a re-check, or with
    GitHub statistics still pending for more than TRUST_STATS_RETRY_HOURS. Suspended users are skipped."""
    now = now or timezone.now()
    week = now - timedelta(days=settings.TRUST_REVERIFY_REPOS_DAYS)
    stats = now - timedelta(hours=settings.TRUST_STATS_RETRY_HOURS)
    return (RepoLink.objects
            .filter(Q(checked_at__lt=week) | Q(review_state=RepoLink.Review.NEEDS_RECHECK)
                    | Q(active_weeks__isnull=True, checked_at__lt=stats))
            .exclude(project__owner__is_suspended=True)
            .select_related("project", "project__owner").order_by("checked_at"))

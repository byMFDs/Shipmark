"""Hallmarks are computed from facts, never stored (CLAUDE.md section 2).

compute_hallmarks(project) is pure: it reads the project and its related rows and returns
a HallmarkSet. Pages use `project.hallmarks`, which caches the result on the instance, and
instances live for one request, so it is computed once per project per request.

Lists: prefetch "domain_verifications", select "repo_link" and wrap the queryset in
verification.uptime.with_uptime(), then every hallmark is computed without extra queries.
"""
from dataclasses import dataclass
from datetime import datetime

from django.utils import formats
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.utils.translation import ngettext

from verification import domain as domains
from verification import uptime
from verification.models import DomainVerification, RepoLink

HALLMARK_KINDS = ("authored", "live", "steady")

# What each hallmark means, in one or two sentences. Shown next to the large marks.
RULES = {
    "authored": gettext_lazy(
        "The linked public GitHub repository is owned by the author's personal GitHub account and is not a fork."
    ),
    "live": gettext_lazy(
        "The author proved control of the project's domain with a DNS record or a meta tag. "
        "It is checked again every 30 days and must be confirmed within 35."
    ),
    "steady": gettext_lazy(
        # xgettext:no-python-format
        "Live, and at least 95% of uptime checks succeeded over the last 30 days, "
        "with at least 40 checks."
    ),
}


@dataclass(frozen=True)
class Hallmark:
    kind: str
    earned: bool
    reason: str  # one line, already translated: why it is earned, or what is missing
    earned_at: datetime | None = None  # start of the current run, when the facts tell it

    @property
    def rule(self):
        return RULES[self.kind]


class HallmarkSet(tuple):
    """Hallmarks in display order. `hallmarks["live"]` (and `hallmarks.live` in templates) picks one."""

    def __getitem__(self, key):
        if isinstance(key, str):
            for item in self:
                if item.kind == key:
                    return item
            raise KeyError(key)
        return super().__getitem__(key)

    @property
    def earned_count(self):
        return sum(item.earned for item in self)


def _percent_text(ok, total):
    value = uptime.percent(ok, total)
    return formats.number_format(int(value) if value == int(value) else value)


def _authored(project):
    if not project.repo_full_name:
        return Hallmark("authored", False, _("No repository linked."))
    link = getattr(project, "repo_link", None) if project.pk else None  # reverse 1:1, None when missing
    # A link for another repo name is stale: the project now points at a repository nobody checked.
    if link is None or link.repo_full_name.lower() != project.repo_full_name.lower():
        return Hallmark("authored", False, _("The repository check has not passed yet."))
    if link.review_state == RepoLink.Review.NEEDS_REVIEW:
        return Hallmark("authored", False, _("The repository is waiting for a routine manual review."))
    if link.review_state == RepoLink.Review.NEEDS_RECHECK:
        return Hallmark("authored", False, _("The repository is being checked again under the current rules."))
    if link.is_verified:
        return Hallmark("authored", True, _("%(repo)s is owned by the author's GitHub account.")
                        % {"repo": link.repo_full_name}, link.earned_at)
    return Hallmark("authored", False, _("The repository check has not passed yet."))


def _live(project, now):
    if not project.live_url:
        return Hallmark("live", False, _("No live URL."))
    if domains.host_from_url(project.live_url) is None:
        return Hallmark("live", False, _("The live URL is not a public domain name, so it cannot be verified."))
    row = domains.current_row(project)
    if domains.row_is_live(row, now):
        return Hallmark("live", True, _("Control of %(domain)s confirmed %(date)s.") % {
            "domain": row.domain, "date": formats.date_format(row.last_confirmed_at, "DATE_FORMAT"),
        }, row.verified_at)
    if row is None or row.status == DomainVerification.Status.PENDING:
        return Hallmark("live", False, _("The domain has not been verified yet."))
    if row.status == DomainVerification.Status.FAILED:
        return Hallmark("live", False, _("Lost: %(domain)s failed re-verification.") % {"domain": row.domain})
    return Hallmark("live", False, _("Lost: %(domain)s was not confirmed in the last 35 days.") % {"domain": row.domain})


def _steady(project, live, now):
    if not live.earned:
        return Hallmark("steady", False, _("Needs Live first."))
    ok, total = uptime.window_counts(project, now)
    if uptime.steady_rule(ok, total):
        return Hallmark("steady", True, ngettext(
            "%(percent)s%% of %(total)s check succeeded in the last 30 days.",
            "%(percent)s%% of %(total)s checks succeeded in the last 30 days.", total,
        ) % {"percent": _percent_text(ok, total), "total": total})  # no single start date: a rolling window
    if total < uptime.STEADY_MIN_CHECKS:
        return Hallmark("steady", False, _("%(total)s of %(min)s uptime checks so far.") % {
            "total": total, "min": uptime.STEADY_MIN_CHECKS,
        })
    return Hallmark("steady", False, _("%(percent)s%% of checks succeeded in the last 30 days; %(min)s%% needed.") % {
        "percent": _percent_text(ok, total), "min": uptime.STEADY_MIN_PERCENT,
    })


def compute_hallmarks(project, now=None):
    """Return a HallmarkSet (Authored, Live, Steady) for a project. Steady always requires Live."""
    live = _live(project, now)
    return HallmarkSet((_authored(project), live, _steady(project, live, now)))

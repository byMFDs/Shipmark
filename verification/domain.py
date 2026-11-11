"""Domain verification: the Live hallmark (CLAUDE.md section 2).

The owner proves control of the live URL's domain in one of two ways:
- DNS: a TXT record "shipmark-verify=<token>" on the exact host (for www.example.com
  a record on example.com counts too, because www is ignored when comparing domains);
- Meta: <meta name="shipmark-verify" content="<token>"> on the homepage, fetched with safe_fetch.

A failed manual check never removes Live: the owner may simply be trying the other method.
Removal happens in `reverify` (run by the `reverify_domains` cron command), and is logged.
"""
import ipaddress
import logging
import secrets
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit

import dns.exception
import dns.resolver
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from config import branding
from moderation import audit

from .models import Block, DomainVerification
from .net import BlockedURL, FetchError, safe_fetch

logger = logging.getLogger(__name__)

TOKEN_NAME = branding.VERIFY_TOKEN_NAME
DNS_TIMEOUT = 5.0
REVERIFY_AFTER = timedelta(days=30)
LIVE_MAX_AGE = timedelta(days=35)  # Live counts only if confirmed within this time (proof.py)

# Code -> message shown to the owner. Codes are stored in DomainVerification.last_error.
MESSAGES = {
    "no_url": _("Add a live URL and save the project first."),
    "bad_host": _("This address cannot be verified. Use a domain name, not an IP address or a local name."),
    "shared_host": _("This is the main address of a hosting service shared by many sites, so it cannot be "
                     "verified. Use your own address on it (like yourname.github.io) or your own domain."),
    "taken": _("This domain is already verified for another project."),
    "blocked_domain": _("This domain cannot be verified. If you think this is a mistake, write to us."),
    "dns_nxdomain": _("This domain does not exist in DNS. Check the spelling of the live URL."),
    "dns_no_txt": _("No TXT records were found on this name yet. DNS changes can take up to an hour."),
    "dns_wrong_txt": _("TXT records were found, but none has your token. Check the value, character by character."),
    "dns_unavailable": _("DNS did not answer in time. Try again in a few minutes."),
    "blocked": _("This address points to a private network and cannot be checked."),
    "unreachable": _("Your homepage could not be loaded (no answer within 5 seconds, or the connection failed)."),
    "http_error": _("Your homepage did not answer with 200 OK. It must be public, without a login."),
    "server_error": _("Your homepage answered with a server error. Try again when the site is up."),
    "other_host": _("Your homepage redirects to another domain. The tag must be on this domain."),
    "too_large": _("Your homepage is larger than 512 KB. Use the DNS method instead."),
    "meta_missing": _("The page loaded, but the meta tag was not found in it."),
    "meta_wrong": _("The meta tag was found, but its token does not match. Copy it again."),
}
# Problems on our side or a short outage: they never remove a hallmark by themselves.
TEMPORARY = {"dns_unavailable", "unreachable", "server_error"}


class DomainCheckError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code

    @property
    def message(self):
        return str(MESSAGES.get(self.code, MESSAGES["unreachable"]))

    @property
    def temporary(self):
        return self.code in TEMPORARY


def error_message(code):
    return str(MESSAGES[code]) if code in MESSAGES else ""


# ---------- Hosts ----------

def host_from_url(url):
    """Exact host of a live URL (lowercase, punycode, no port, no trailing dot), or None if unusable."""
    if not url:
        return None
    try:
        host = (urlsplit(url).hostname or "").rstrip(".")
        host = host.encode("idna").decode("ascii").lower()
    except (ValueError, UnicodeError):
        return None
    try:
        ipaddress.ip_address(host)
        return None  # an IP address is not a domain
    except ValueError:
        pass
    labels = host.split(".")
    if len(labels) < 2 or not all(labels) or len(host) > 253:
        return None
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".home.arpa", ".test")):
        return None
    return host


def is_shared_host(host):
    """The bare address of a hosting service where every user gets a subdomain (settings list)."""
    return domain_key(host) in settings.TRUST_SHARED_HOST_APEXES


def domain_key(host):
    """What two hosts are compared by: "www.example.com" and "example.com" are the same domain."""
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def record_value(token):
    return f"{TOKEN_NAME}={token}"


def meta_tag(token):
    return f'<meta name="{TOKEN_NAME}" content="{token}">'


def homepage_url(project, host):
    scheme = "http" if project.live_url.lower().startswith("http://") else "https"
    return f"{scheme}://{host}/"


# ---------- Rows ----------

def new_token():
    return secrets.token_hex(16)


def verification_for(project, create=False):
    """The row for the project's current domain, or None. Keeps `domain` in sync (www on or off)."""
    host = host_from_url(project.live_url)
    if host is None:
        return None
    key = domain_key(host)
    row = DomainVerification.objects.filter(project=project, domain_key=key).first()
    if row is None and create:
        try:
            with transaction.atomic():
                row = DomainVerification.objects.create(project=project, domain=host, domain_key=key, token=new_token())
        except IntegrityError:  # a parallel request created it
            row = DomainVerification.objects.filter(project=project, domain_key=key).first()
    if row is not None and row.domain != host:
        row.domain = host
        row.save(update_fields=["domain"])
    return row


def forget_other_domains(project, actor=None):
    """After the live URL changes: delete rows for other domains, so they stop blocking them."""
    key = domain_key(host_from_url(project.live_url) or "")
    for row in DomainVerification.objects.filter(project=project).exclude(domain_key=key):
        if row.status == DomainVerification.Status.VERIFIED:
            audit.log("hallmark.live.removed", project, actor=actor, domain=row.domain, reason="live_url_changed")
        row.delete()


def taken_by_other(row):
    return (DomainVerification.objects
            .filter(domain_key=row.domain_key, status=DomainVerification.Status.VERIFIED)
            .exclude(project_id=row.project_id).exists())


# ---------- Checks ----------

def _txt_values(name):
    resolver = dns.resolver.Resolver()
    try:
        answer = resolver.resolve(name, "TXT", lifetime=DNS_TIMEOUT, search=False)
    except dns.resolver.NXDOMAIN as exc:
        raise DomainCheckError("dns_nxdomain") from exc
    except dns.resolver.NoAnswer:
        return []
    except (dns.exception.Timeout, dns.resolver.NoNameservers, dns.exception.DNSException) as exc:
        raise DomainCheckError("dns_unavailable") from exc
    # A long TXT value arrives split into 255-byte pieces: join them back.
    return [b"".join(rdata.strings).decode("utf-8", errors="replace").strip() for rdata in answer]


def check_dns(host, token):
    names = [host] + ([host[4:]] if host.startswith("www.") else [])
    expected = record_value(token)
    found_any, last_error = False, None
    for name in names:
        try:
            values = _txt_values(name)
        except DomainCheckError as exc:
            last_error = exc
            continue
        found_any = found_any or bool(values)
        if any(value.strip('"') == expected for value in values):
            return
    if found_any:
        raise DomainCheckError("dns_wrong_txt")
    raise last_error or DomainCheckError("dns_no_txt")


class _MetaFinder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            attrs = {k.lower(): (v or "") for k, v in attrs}
            if attrs.get("name", "").strip().lower() == TOKEN_NAME:
                self.values.append(attrs.get("content", "").strip())

    handle_startendtag = handle_starttag


def check_meta(url, host, token):
    try:
        result = safe_fetch(url)
    except BlockedURL as exc:
        raise DomainCheckError("blocked") from exc
    except FetchError as exc:
        raise DomainCheckError("too_large" if exc.code == "too_large" else "unreachable") from exc
    if domain_key(host_from_url(result.url)) != domain_key(host):
        raise DomainCheckError("other_host")  # e.g. a redirect to a page someone else controls
    if result.status_code >= 500:
        raise DomainCheckError("server_error")
    if result.status_code != 200:
        raise DomainCheckError("http_error")
    finder = _MetaFinder()
    try:
        finder.feed(result.text)
        finder.close()
    except Exception:  # noqa: BLE001  broken HTML: use what was parsed
        pass
    if token in finder.values:
        return
    raise DomainCheckError("meta_wrong" if finder.values else "meta_missing")


def run_method(row, method):
    if method == DomainVerification.Method.META:
        check_meta(homepage_url(row.project, row.domain), row.domain, row.token)
    else:
        check_dns(row.domain, row.token)


# ---------- Verify, re-verify ----------

def verify(row, method, actor=None):
    """Manual "Verify now". Returns True on success, raises DomainCheckError otherwise."""
    if method not in DomainVerification.Method.values:
        method = DomainVerification.Method.DNS
    now = timezone.now()
    if is_shared_host(row.domain):
        _save_error(row, "shared_host", now)
        raise DomainCheckError("shared_host")
    if Block.domain_blocked(row.domain_key):
        _save_error(row, "blocked_domain", now)
        raise DomainCheckError("blocked_domain")
    if taken_by_other(row):
        _save_error(row, "taken", now)
        raise DomainCheckError("taken")
    try:
        run_method(row, method)
    except DomainCheckError as exc:
        _save_error(row, exc.code, now)
        raise
    was_verified = row.status == DomainVerification.Status.VERIFIED
    row.method = method
    row.status = DomainVerification.Status.VERIFIED
    row.verified_at = row.verified_at if was_verified else now
    row.last_confirmed_at = row.last_checked_at = now
    row.last_error = ""
    try:
        with transaction.atomic():
            row.save()
            if not was_verified:
                audit.log("hallmark.live.earned", row.project, actor=actor, domain=row.domain, method=method)
    except IntegrityError as exc:  # another project verified it between our check and the save
        row.refresh_from_db()
        _save_error(row, "taken", now)
        raise DomainCheckError("taken") from exc
    return True


def _save_error(row, code, now):
    row.last_error = code
    row.last_checked_at = now
    row.save(update_fields=["last_error", "last_checked_at"])


def reverify(row, now=None):
    """Re-check a verified row with its own method. Returns "confirmed", "kept" or "removed".

    A definite failure removes Live at once. A temporary one (DNS timeout, site down) is retried
    on the next run; after 35 days without a confirmation Live is gone anyway, and the row is failed.
    """
    now = now or timezone.now()
    try:
        if domain_key(host_from_url(row.project.live_url) or "") != row.domain_key:
            raise DomainCheckError("no_url")  # the live URL moved away; Live no longer applies
        if Block.domain_blocked(row.domain_key):
            raise DomainCheckError("blocked_domain")
        run_method(row, row.method)
    except DomainCheckError as exc:
        expired = row.last_confirmed_at is None or row.last_confirmed_at < now - LIVE_MAX_AGE
        if exc.temporary and not expired:
            _save_error(row, exc.code, now)
            return "kept"
        with transaction.atomic():
            row.status = DomainVerification.Status.FAILED
            row.last_error = exc.code
            row.last_checked_at = now
            row.save(update_fields=["status", "last_error", "last_checked_at"])
            audit.log("hallmark.live.removed", row.project, domain=row.domain, method=row.method, reason=exc.code)
        return "removed"
    row.last_confirmed_at = row.last_checked_at = now
    row.last_error = ""
    row.save(update_fields=["last_confirmed_at", "last_checked_at", "last_error"])
    return "confirmed"


def current_row(project):
    """The project's row for the domain of its current live URL, or None. Reads the prefetch cache."""
    if not project.pk:
        return None
    host = host_from_url(project.live_url)
    if host is None:
        return None
    key = domain_key(host)
    return next((row for row in project.domain_verifications.all() if row.domain_key == key), None)


def row_is_live(row, now=None):
    """A verified row confirmed in the last 35 days."""
    cutoff = (now or timezone.now()) - LIVE_MAX_AGE
    return bool(
        row is not None and row.status == DomainVerification.Status.VERIFIED
        and row.last_confirmed_at is not None and row.last_confirmed_at >= cutoff
    )


def is_live(project, now=None):
    """Live hallmark: a verified row for the current domain, confirmed in the last 35 days.

    Reads `project.domain_verifications.all()`, so list views can prefetch it.
    """
    return row_is_live(current_row(project), now)

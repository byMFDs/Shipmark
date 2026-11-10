"""The only way to request a user-supplied URL from the server (CLAUDE.md section 6).

    result = safe_fetch("https://example.com/")      # FetchResult, or raises FetchError
    result.status_code, result.text, result.url

Why each rule exists:
- Only http/https on ports 80/443: no talking to databases, mail servers or admin ports.
- DNS is resolved here and every address is checked. The connection then goes to that exact
  checked IP (the hostname is kept for the Host header and TLS), so a DNS answer that changes
  between "check" and "connect" (DNS rebinding) cannot reach an internal address.
- Redirects are followed by hand (max 3), and every hop goes through the same checks.
- 5 s deadline for the whole fetch, 512 KB body limit (counted after decompression).
"""
import ipaddress
import logging
import time
import zlib
from dataclasses import dataclass, field

import dns.exception
import dns.resolver
import httpx

from config import branding

logger = logging.getLogger(__name__)

TIMEOUT = 5.0  # seconds, for everything: DNS, connect, every redirect and the body
MAX_BODY = 512 * 1024
MAX_REDIRECTS = 3
ALLOWED_SCHEMES = ("http", "https")
ALLOWED_PORTS = (80, 443)
USER_AGENT = f"{branding.SITE_NAME}-verify/1.0"
REDIRECT_CODES = (301, 302, 303, 307, 308)

# Not covered (or not fully) by the ipaddress flags below, so listed explicitly.
EXTRA_BLOCKED = [
    ipaddress.ip_network("100.64.0.0/10"),  # CGNAT, shared address space
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),  # benchmarking
    ipaddress.ip_network("fc00::/7"),  # unique local
    ipaddress.ip_network("fec0::/10"),  # old site-local
]
NAT64 = ipaddress.ip_network("64:ff9b::/96")


class FetchError(Exception):
    """The fetch did not happen or did not finish. `code` says why; the message is for logs only."""

    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


class BlockedURL(FetchError):
    """The URL (or a redirect) points somewhere we never connect to."""


@dataclass
class FetchResult:
    url: str  # final URL after redirects
    status_code: int
    headers: httpx.Headers
    content: bytes
    redirects: list = field(default_factory=list)

    @property
    def text(self):
        charset = "utf-8"
        for part in self.headers.get("content-type", "").split(";")[1:]:
            key, _sep, value = part.strip().partition("=")
            if key.lower() == "charset" and value:
                charset = value.strip("\"' ")
        try:
            return self.content.decode(charset, errors="replace")
        except LookupError:
            return self.content.decode("utf-8", errors="replace")


def _clock():
    return time.monotonic()


# ---------- Address checks ----------

def is_blocked_ip(ip):
    """True for every address that is not plainly public. Unwraps IPv6 forms that carry an IPv4 address."""
    if isinstance(ip, str):
        ip = ipaddress.ip_address(ip)
    if ip.version == 6:
        embedded = ip.ipv4_mapped or ip.sixtofour or (ip.teredo[1] if ip.teredo else None)
        if embedded is None and ip in NAT64:
            embedded = ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
        if embedded is not None and is_blocked_ip(embedded):
            return True
    if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
            or ip.is_unspecified or not ip.is_global):
        return True
    return any(ip in net for net in EXTRA_BLOCKED if net.version == ip.version)


def resolve_host(host, timeout):
    """All A and AAAA addresses of `host`. Raises FetchError("dns") when there are none."""
    resolver = dns.resolver.Resolver()
    addresses = []
    for rdtype in ("A", "AAAA"):
        try:
            answer = resolver.resolve(host, rdtype, lifetime=max(timeout, 0.5), search=False)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            continue
        except (dns.exception.Timeout, dns.exception.DNSException) as exc:
            raise FetchError("dns", exc.__class__.__name__) from exc
        addresses.extend(rdata.address for rdata in answer)
    if not addresses:
        raise FetchError("dns", f"no addresses for {host}")
    return addresses


def _check_url(url):
    """Validates scheme, port, credentials and host. Returns (httpx.URL, ascii host, port)."""
    try:
        parsed = httpx.URL(url)
        host = parsed.raw_host.decode("ascii").lower().rstrip(".")  # IDN already in punycode
        port = parsed.port
    except (httpx.InvalidURL, UnicodeError, ValueError, TypeError) as exc:
        raise BlockedURL("invalid_url", str(exc)) from exc
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise BlockedURL("scheme", parsed.scheme)
    port = port or (443 if parsed.scheme == "https" else 80)
    if port not in ALLOWED_PORTS:
        raise BlockedURL("port", str(port))
    if parsed.userinfo:
        raise BlockedURL("credentials")
    if not host:
        raise BlockedURL("invalid_url", "no host")
    return parsed, host, port


def _pick_address(host, deadline):
    try:
        literal = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        literal = None
    if literal is not None:
        addresses = [str(literal)]
    elif host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".home.arpa")):
        raise BlockedURL("private_ip", host)
    else:
        addresses = resolve_host(host, deadline - _clock())
    # Every address must be public: a mixed answer is how rebinding tricks usually look.
    for address in addresses:
        if is_blocked_ip(address):
            raise BlockedURL("private_ip", f"{host} -> {address}")
    return addresses[0]


# ---------- HTTP ----------

def _client(timeout):
    # trust_env=False: proxy variables or .netrc on the server must not change where we connect.
    return httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False, verify=True)


def _read_body(response, deadline, max_bytes):
    encoding = response.headers.get("content-encoding", "").strip().lower()
    if encoding in ("", "identity"):
        decoder = None
    elif encoding in ("gzip", "x-gzip", "deflate"):
        # Bounded decompression: a tiny gzip "bomb" cannot grow past max_bytes in memory.
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS if "gzip" in encoding else zlib.MAX_WBITS)
    else:
        raise FetchError("encoding", encoding)

    length = response.headers.get("content-length", "")
    if decoder is None and length.isdigit() and int(length) > max_bytes:
        raise FetchError("too_large", length)

    body = bytearray()
    for chunk in response.iter_raw():
        if _clock() > deadline:
            raise FetchError("timeout", "body")
        if decoder is not None:
            try:
                chunk = decoder.decompress(chunk, max_bytes + 1 - len(body))
            except zlib.error as exc:
                raise FetchError("encoding", "bad compressed data") from exc
        body.extend(chunk)
        if len(body) > max_bytes:
            raise FetchError("too_large", f">{max_bytes}")
    return bytes(body)


def safe_fetch(url, *, method="GET", max_bytes=MAX_BODY, timeout=TIMEOUT, read_body=True):
    """Fetch `url` with every SSRF rule applied. Returns FetchResult or raises FetchError.

    Any HTTP status is a result (404 is an answer, not an error). Only GET and HEAD.
    read_body=False: only the status is wanted (uptime), so the body is never downloaded.
    """
    if method not in ("GET", "HEAD"):
        raise ValueError("safe_fetch only does GET and HEAD")
    deadline = _clock() + timeout
    redirects = []
    current = url

    with _client(timeout) as client:
        for _hop in range(MAX_REDIRECTS + 1):
            parsed, host, port = _check_url(current)
            address = _pick_address(host, deadline)
            remaining = deadline - _clock()
            if remaining <= 0:
                raise FetchError("timeout", "before connect")

            default_port = 443 if parsed.scheme == "https" else 80
            host_header = host if port == default_port else f"{host}:{port}"
            pinned = parsed.copy_with(host=address, port=port if port != default_port else None)
            request = client.build_request(
                method, pinned,
                headers={
                    "Host": host_header,
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
                    "Accept-Encoding": "gzip, deflate, identity",
                },
                # TLS: send SNI and check the certificate against the real hostname, not the IP.
                extensions={"sni_hostname": host, "timeout": httpx.Timeout(remaining).as_dict()},
            )
            try:
                response = client.send(request, stream=True)
            except httpx.TimeoutException as exc:
                raise FetchError("timeout", exc.__class__.__name__) from exc
            except httpx.HTTPError as exc:
                raise FetchError("connect", exc.__class__.__name__) from exc

            try:
                if response.status_code in REDIRECT_CODES and "location" in response.headers:
                    target = parsed.join(response.headers["location"])
                    current = str(target.copy_with(fragment=None))
                    redirects.append(current)
                    continue
                content = _read_body(response, deadline, max_bytes) if method == "GET" and read_body else b""
                return FetchResult(
                    url=str(parsed), status_code=response.status_code, headers=response.headers,
                    content=content, redirects=redirects,
                )
            except httpx.TimeoutException as exc:
                raise FetchError("timeout", "body") from exc
            except httpx.HTTPError as exc:
                raise FetchError("connect", exc.__class__.__name__) from exc
            finally:
                response.close()
    raise FetchError("too_many_redirects", str(MAX_REDIRECTS))

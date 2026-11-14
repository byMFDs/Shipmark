"""safe_fetch: the SSRF guard. DNS and HTTP are mocked; nothing leaves the machine."""
import gzip
from unittest.mock import patch

import httpx
from django.test import SimpleTestCase

from . import net
from .net import MAX_BODY, BlockedURL, FetchError, safe_fetch

REAL_CLIENT = httpx.Client
PUBLIC_IP = "93.184.215.14"
PRIVATE = ["127.0.0.1", "10.1.2.3", "172.16.0.9", "192.168.1.1", "169.254.169.254", "100.64.0.1",
           "0.0.0.0", "::1", "fc00::1", "fd12:3456::1", "fe80::1", "::ffff:127.0.0.1", "::ffff:10.0.0.1",
           "64:ff9b::a00:1", "2002:7f00:1::1", "224.0.0.1", "ff02::1", "::"]


class FakeNet:
    """Підробні DNS і HTTP для тестів safe_fetch.

    Patches DNS (host -> addresses) and HTTP (handler by Host header). Records requests."""

    def __init__(self, dns=None, handler=None):
        self.dns = {"example.com": [PUBLIC_IP], **(dns or {})}
        self.handler = handler or (lambda request: httpx.Response(200, text="<html>hi</html>"))
        self.requests = []

    def resolve(self, host, timeout):
        if host not in self.dns:
            raise FetchError("dns", host)
        return self.dns[host]

    def client(self, timeout):
        def handle(request):
            self.requests.append(request)
            response = self.handler(request)
            if hasattr(response, "_content"):  # bytes body: hand out the raw stream again, like a real server
                return httpx.Response(response.status_code, headers=response.headers, stream=response.stream)
            return response
        return REAL_CLIENT(transport=httpx.MockTransport(handle), timeout=timeout, follow_redirects=False)

    def __enter__(self):
        self.patches = [patch.object(net, "resolve_host", self.resolve), patch.object(net, "_client", self.client)]
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in self.patches:
            p.stop()


class BlockedAddressTests(SimpleTestCase):
    """Заблоковані адреси."""
    def test_private_addresses_are_blocked_as_literals(self):
        for ip in PRIVATE:
            url = f"http://[{ip}]/" if ":" in ip else f"http://{ip}/"
            with self.subTest(ip=ip), FakeNet() as fake:
                with self.assertRaises(BlockedURL) as ctx:
                    safe_fetch(url)
                self.assertEqual(ctx.exception.code, "private_ip")
                self.assertEqual(fake.requests, [])  # never connected

    def test_private_addresses_are_blocked_after_dns(self):
        for ip in PRIVATE:
            with self.subTest(ip=ip), FakeNet(dns={"sneaky.example": [ip]}) as fake:
                with self.assertRaises(BlockedURL):
                    safe_fetch("https://sneaky.example/")
                self.assertEqual(fake.requests, [])

    def test_localhost_is_blocked_without_dns(self):
        for url in ("http://localhost/", "http://LOCALHOST./", "http://api.localhost/", "http://printer.local/"):
            with self.subTest(url=url), FakeNet() as fake, self.assertRaises(BlockedURL):
                safe_fetch(url)
            self.assertEqual(fake.requests, [])

    def test_one_private_address_in_the_answer_blocks_the_host(self):
        with FakeNet(dns={"mixed.example": [PUBLIC_IP, "10.0.0.1"]}), self.assertRaises(BlockedURL):
            safe_fetch("https://mixed.example/")

    def test_public_addresses_are_allowed(self):
        for ip in ("8.8.8.8", "93.184.215.14", "2606:4700::1111"):
            self.assertFalse(net.is_blocked_ip(ip), ip)


class UrlRuleTests(SimpleTestCase):
    """Правила адрес."""
    def test_only_ports_80_and_443(self):
        for url in ("http://example.com:8080/", "https://example.com:22/", "http://example.com:6379/"):
            with self.subTest(url=url), FakeNet() as fake:
                with self.assertRaises(BlockedURL) as ctx:
                    safe_fetch(url)
                self.assertEqual(ctx.exception.code, "port")
                self.assertEqual(fake.requests, [])
        with FakeNet():
            self.assertEqual(safe_fetch("https://example.com:443/").status_code, 200)

    def test_only_http_and_https(self):
        for url in ("ftp://example.com/", "file:///etc/passwd", "gopher://example.com/", "javascript:alert(1)",
                    "data:text/html,hi", "//example.com/"):
            with self.subTest(url=url), FakeNet(), self.assertRaises(BlockedURL):
                safe_fetch(url)

    def test_credentials_in_url_are_refused(self):
        with FakeNet(), self.assertRaises(BlockedURL):
            safe_fetch("https://user:pass@example.com/")

    def test_only_get_and_head(self):
        with self.assertRaises(ValueError):
            safe_fetch("https://example.com/", method="POST")


class FetchTests(SimpleTestCase):
    """Запити safe_fetch."""
    def test_normal_public_url(self):
        with FakeNet() as fake:
            result = safe_fetch("https://example.com/page?x=1")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.text, "<html>hi</html>")
        self.assertEqual(result.url, "https://example.com/page?x=1")
        request = fake.requests[0]
        # Connected to the checked IP, while Host and TLS name stay the real hostname (no DNS rebinding).
        self.assertEqual(request.url.host, PUBLIC_IP)
        self.assertEqual(request.headers["host"], "example.com")
        self.assertEqual(request.extensions["sni_hostname"], "example.com")
        self.assertEqual(request.headers["user-agent"], net.USER_AGENT)
        self.assertLessEqual(request.extensions["timeout"]["read"], net.TIMEOUT)

    def test_status_only_does_not_read_the_body(self):
        with FakeNet(handler=lambda request: httpx.Response(200, content=b"x" * (MAX_BODY + 10))):
            result = safe_fetch("https://example.com/", read_body=False)
        self.assertEqual((result.status_code, result.content), (200, b""))

    def test_redirect_to_private_ip_is_blocked(self):
        def handler(request):
            return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data/"})
        with FakeNet(handler=handler) as fake:
            with self.assertRaises(BlockedURL):
                safe_fetch("https://example.com/")
        self.assertEqual(len(fake.requests), 1)

    def test_redirect_to_host_that_resolves_private_is_blocked(self):
        def handler(request):
            return httpx.Response(301, headers={"Location": "https://internal.example/admin"})
        with FakeNet(dns={"internal.example": ["192.168.0.10"]}, handler=handler) as fake:
            with self.assertRaises(BlockedURL):
                safe_fetch("https://example.com/")
        self.assertEqual(len(fake.requests), 1)

    def test_redirect_to_other_port_or_scheme_is_blocked(self):
        for location in ("http://example.com:8080/", "ftp://example.com/x"):
            with self.subTest(location=location), FakeNet(
                handler=lambda r, loc=location: httpx.Response(302, headers={"Location": loc})
            ), self.assertRaises(BlockedURL):
                safe_fetch("https://example.com/")

    def test_redirects_are_followed_up_to_three(self):
        def handler(request):
            hop = int(request.url.params.get("hop", "0"))
            if hop < 3:
                return httpx.Response(302, headers={"Location": f"/?hop={hop + 1}"})
            return httpx.Response(200, text="done")
        with FakeNet(handler=handler) as fake:
            result = safe_fetch("https://example.com/")
        self.assertEqual(result.text, "done")
        self.assertEqual(result.url, "https://example.com/?hop=3")
        self.assertEqual(len(fake.requests), 4)

    def test_more_than_three_redirects_fail(self):
        with FakeNet(handler=lambda r: httpx.Response(302, headers={"Location": "/again"})) as fake:
            with self.assertRaises(FetchError) as ctx:
                safe_fetch("https://example.com/")
        self.assertEqual(ctx.exception.code, "too_many_redirects")
        self.assertEqual(len(fake.requests), 4)

    def test_body_over_512_kb_is_refused(self):
        big = b"a" * (MAX_BODY + 1)
        cases = {
            "declared": lambda r: httpx.Response(200, content=big),
            "streamed": lambda r: httpx.Response(200, content=iter([b"a" * 65536] * 9)),  # no Content-Length
            "gzip": lambda r: httpx.Response(200, content=gzip.compress(b"a" * (5 * MAX_BODY)),
                                             headers={"Content-Encoding": "gzip"}),
        }
        for name, handler in cases.items():
            with self.subTest(name), FakeNet(handler=handler), self.assertRaises(FetchError) as ctx:
                safe_fetch("https://example.com/")
            self.assertEqual(ctx.exception.code, "too_large")

    def test_body_at_the_limit_is_fine(self):
        with FakeNet(handler=lambda r: httpx.Response(200, content=b"a" * MAX_BODY)):
            self.assertEqual(len(safe_fetch("https://example.com/").content), MAX_BODY)

    def test_gzip_body_is_decoded(self):
        handler = lambda r: httpx.Response(200, content=gzip.compress(b"<p>ok</p>"), headers={"Content-Encoding": "gzip"})  # noqa: E731
        with FakeNet(handler=handler):
            self.assertEqual(safe_fetch("https://example.com/").text, "<p>ok</p>")

    def test_timeout_from_the_server(self):
        def handler(request):
            raise httpx.ReadTimeout("slow", request=request)
        with FakeNet(handler=handler), self.assertRaises(FetchError) as ctx:
            safe_fetch("https://example.com/")
        self.assertEqual(ctx.exception.code, "timeout")

    def test_slow_drip_body_hits_the_deadline(self):
        """A server sending a byte now and then cannot hold the request past 5 seconds."""
        clock = {"now": 1000.0}

        def drip():
            for _ in range(100):
                clock["now"] += 1.0  # each chunk takes a second
                yield b"x"

        with FakeNet(handler=lambda r: httpx.Response(200, content=drip())), \
                patch.object(net, "_clock", lambda: clock["now"]), self.assertRaises(FetchError) as ctx:
            safe_fetch("https://example.com/")
        self.assertEqual(ctx.exception.code, "timeout")
        self.assertLessEqual(clock["now"], 1000.0 + net.TIMEOUT + 1)

    def test_connection_error(self):
        def handler(request):
            raise httpx.ConnectError("refused", request=request)
        with FakeNet(handler=handler), self.assertRaises(FetchError) as ctx:
            safe_fetch("https://example.com/")
        self.assertEqual(ctx.exception.code, "connect")

    def test_unknown_host(self):
        with FakeNet(), self.assertRaises(FetchError) as ctx:
            safe_fetch("https://no-such-host.example/")
        self.assertEqual(ctx.exception.code, "dns")

    def test_error_status_is_a_result(self):
        with FakeNet(handler=lambda r: httpx.Response(404, text="nope")):
            self.assertEqual(safe_fetch("https://example.com/").status_code, 404)

    def test_no_direct_httpx_use_outside_allowed_modules(self):
        """Only net.py may request user URLs. repo.py talks to the fixed api.github.com host."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parent.parent
        offenders = []
        for path in root.rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            if rel.startswith((".venv/", "venv/")) or "/tests" in rel or "/test_" in rel or rel.endswith("tests.py"):
                continue
            if rel in ("verification/net.py", "verification/repo.py"):
                continue
            if "import httpx" in path.read_text(encoding="utf-8"):
                offenders.append(rel)
        self.assertEqual(offenders, [])

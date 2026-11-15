"""Не дозволяє підмінити IP-ключ ліміту через початок forwarded chain."""
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.contrib.auth.models import AnonymousUser

from accounts.people import visitor_key

from support.antispam import client_ip, ip_key


class ProxyIpTests(SimpleTestCase):
    """Прямий довірений router додає справжню адресу після вхідних значень."""

    @override_settings(CLIENT_IP_HEADER="HTTP_X_FORWARDED_FOR")
    def test_spoofed_prefix_does_not_change_the_support_or_people_ip(self):
        keys = []
        people_keys = []
        for prefix in ("192.0.2.10", "192.0.2.11, 192.0.2.12"):
            request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR=prefix + ", 198.51.100.23")
            self.assertEqual(client_ip(request), "198.51.100.23")
            keys.append(ip_key(client_ip(request)))
            request.user = AnonymousUser()
            people_keys.append(visitor_key(request))
        self.assertEqual(keys[0], keys[1])
        self.assertEqual(people_keys[0], people_keys[1])

    @override_settings(CLIENT_IP_HEADER="")
    def test_forwarded_header_is_ignored_without_an_explicit_trusted_proxy(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="192.0.2.10", REMOTE_ADDR="198.51.100.23")
        self.assertEqual(client_ip(request), "198.51.100.23")

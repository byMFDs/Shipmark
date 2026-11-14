"""The public "<n> people joined" stat: who counts, caching, formatting and the header."""
import re

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import translation

from accounts.models import User
from accounts.system import SYSTEM_USERNAME
from projects.tests import make_user

from . import stats


class CountingTests(TestCase):
    """Лічба людей."""
    def setUp(self):
        cache.clear()

    def test_counts_active_people_and_not_the_system_account(self):
        self.assertTrue(User.objects.filter(username=SYSTEM_USERNAME).exists())  # made by a migration
        make_user("ann")
        make_user("bob", is_suspended=True)  # suspended people did join
        make_user("gone", is_active=False)
        self.assertEqual(stats.count_people(), 2)
        User.objects.get(username="bob").delete()
        self.assertEqual(stats.count_people(), 1)

    def test_cached_for_a_minute_without_fake_changes(self):
        make_user("ann")
        self.assertEqual(stats.public_user_count(), 1)
        make_user("bob")
        with self.assertNumQueries(0):
            self.assertEqual(stats.public_user_count(), 1)  # the cached value, not a guess
        cache.delete(stats.CACHE_KEY)
        self.assertEqual(stats.public_user_count(), 2)
        self.assertEqual(stats.CACHE_SECONDS, 60)


class FormatTests(TestCase):
    """Формат числа."""
    def test_exact_with_grouping_up_to_99999(self):
        with translation.override("en"):
            self.assertEqual(stats.format_count(7), "7")
            self.assertEqual(stats.format_count(12480), "12,480")
            self.assertEqual(stats.format_count(99999), "99,999")

    def test_compact_above_and_never_rounded_up(self):
        with translation.override("en"):
            self.assertEqual(stats.format_count(100000), "100K")
            self.assertEqual(stats.format_count(128999), "128K")
            self.assertEqual(stats.format_count(999999), "999K")
            self.assertEqual(stats.format_count(1_250_000), "1.2M")
            self.assertEqual(stats.format_count(2_000_000), "2M")
            self.assertEqual(stats.format_count(12_345_678), "12M")

    def test_other_languages_group_and_shorten_their_own_way(self):
        with translation.override("uk"):
            self.assertEqual(stats.format_count(12480).replace("\xa0", " "), "12 480")
            self.assertEqual(stats.format_count(128999).replace("\xa0", " "), "128 тис.")
        with translation.override("de"):
            self.assertEqual(stats.format_count(12480), "12.480")


@override_settings(PUBLIC_USER_COUNT_ENABLED=True)
class HeaderTests(TestCase):
    """Число в хедері."""
    def setUp(self):
        cache.clear()

    def stat(self, html):
        match = re.search(r'<p class="site-count" title="([^"]+)">(.*?)</p>', html, re.S)
        return match and (match.group(1), match.group(2))

    def test_header_shows_the_number_with_tooltip_and_full_label(self):
        for name in ("ann", "bob", "cid"):
            make_user(name)
        html = self.client.get("/explore/").content.decode()
        title, body = self.stat(html)
        self.assertEqual(title, "Registered accounts")
        self.assertIn('<span class="visually-hidden">3 people joined</span>', body)
        self.assertIn('data-count-to="3">3</span>', body)
        self.assertIn('aria-hidden="true"', body)
        self.assertIn("js/count.js", html)
        self.assertEqual(html.count('class="site-count"'), 2)  # the bar and the phone menu
        for word in ("live", "pulse", "online"):
            self.assertNotIn(word, body)

    def test_plurals_in_every_language(self):
        make_user("ann")
        for code, _name in settings.LANGUAGES:
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = code
            with self.subTest(language=code):
                _title, body = self.stat(self.client.get("/explore/").content.decode())
                hidden = re.search(r'<span class="visually-hidden">([^<]+)</span>', body).group(1)
                self.assertIn("1", hidden)
                self.assertNotIn("%(", hidden)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uk"
        for count, word in ((1, "людина"), (2, "людини"), (5, "людей")):
            cache.clear()
            while stats.count_people() < count:
                make_user(f"u{stats.count_people()}x")
            with self.subTest(count=count):
                self.assertIn(word, self.stat(self.client.get("/explore/").content.decode())[1])

    def test_compact_numbers_do_not_count_up(self):
        cache.set(stats.CACHE_KEY, 250_000, 60)
        _title, body = self.stat(self.client.get("/explore/").content.decode())
        self.assertIn("250K", body)
        self.assertNotIn("data-count-to", body)
        self.assertIn("250,000 people joined", body)

    @override_settings(PUBLIC_USER_COUNT_MIN=5)
    def test_hidden_until_above_the_minimum(self):
        for name in ("ann", "bob", "cid", "dan", "eve"):
            make_user(name)
        self.assertIsNone(self.stat(self.client.get("/explore/").content.decode()))
        make_user("fay")
        cache.clear()
        self.assertIsNotNone(self.stat(self.client.get("/explore/").content.decode()))

    @override_settings(PUBLIC_USER_COUNT_ENABLED=False)
    def test_switched_off(self):
        make_user("ann")
        self.assertIsNone(self.stat(self.client.get("/explore/").content.decode()))

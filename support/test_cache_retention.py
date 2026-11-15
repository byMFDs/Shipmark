"""Перевіряє фізичне видалення прострочених IP-хешів із кешу бази даних."""
from io import StringIO

from django.core.cache import caches
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase, override_settings


@override_settings(CACHES={"default": {
    "BACKEND": "django.core.cache.backends.db.DatabaseCache",
    "LOCATION": "launch_retention_cache",
}})
class CacheRetentionTests(TransactionTestCase):
    """Щоденна команда прибирає прострочене, зберігаючи чинні ліміти."""

    def test_daily_command_removes_expired_rows_without_reading_the_keys(self):
        call_command("createcachetable", stdout=StringIO())
        cache = caches["default"]
        try:
            cache.set("support:rl:day:ip:expired-hash", 1, timeout=-60)
            cache.set("support:rl:day:ip:active-hash", 2, timeout=86400)
            cache.set("other:permanent", 3, timeout=None)
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM launch_retention_cache")
                self.assertEqual(cursor.fetchone()[0], 3, "Expiry alone leaves the row stored")
            call_command("prune_support", stdout=StringIO())
            with connection.cursor() as cursor:
                cursor.execute("SELECT cache_key FROM launch_retention_cache")
                keys = [row[0] for row in cursor.fetchall()]
            self.assertEqual(len(keys), 2)
            self.assertFalse(any("expired-hash" in key for key in keys))
            self.assertEqual(cache.get("support:rl:day:ip:active-hash"), 2)
            self.assertEqual(cache.get("other:permanent"), 3)
            call_command("prune_support", stdout=StringIO())  # safe to repeat
        finally:
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE launch_retention_cache")

"""Redraw the raster icons from static/brand/logo-mark.svg (logo C).

    python manage.py make_icons

Writes static/brand/favicon.ico (16, 32, 48 px) and static/brand/apple-touch-icon.png (180 px).
favicon.svg, logo.svg and logo-mark.svg are edited by hand; og-default.png has text in it and is made separately.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from config import branding
from pages.brand_icons import apple_touch_icon, favicon_ico


class Command(BaseCommand):
    help = "Redraw favicon.ico and apple-touch-icon.png from the logo mark."

    def handle(self, *args, **options):
        static_dir = settings.STATICFILES_DIRS[0]
        for name, data in ((branding.FAVICON_ICO, favicon_ico()), (branding.APPLE_TOUCH_ICON, apple_touch_icon())):
            (static_dir / name).write_bytes(data)
            self.stdout.write(f"Wrote static/{name} ({len(data)} bytes)")

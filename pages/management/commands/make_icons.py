"""Команда make_icons: перемальовує растрові іконки з logo-mark.svg.

Redraw the raster icons from static/brand/logo-mark.svg (S mark).

    python manage.py make_icons

Writes favicon.ico (16/32/48 px), favicon.png (32 px), apple-touch-icon.png (180 px), and og-default.png (1200×630).
The SVG mark and outlined wordmark are the source for every raster export.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from config import branding
from pages.brand_icons import apple_touch_icon, favicon_ico, favicon_png, og_default_image


class Command(BaseCommand):
    """Команда make_icons."""
    help = "Redraw favicon.ico and apple-touch-icon.png from the logo mark."

    def handle(self, *args, **options):
        """Записує favicon.ico і apple-touch-icon."""
        static_dir = settings.STATICFILES_DIRS[0]
        for name, data in ((branding.FAVICON_ICO, favicon_ico()), ("brand/favicon.png", favicon_png()),
                           (branding.APPLE_TOUCH_ICON, apple_touch_icon()), (branding.OG_DEFAULT_IMAGE, og_default_image())):
            (static_dir / name).write_bytes(data)
            self.stdout.write(f"Wrote static/{name} ({len(data)} bytes)")

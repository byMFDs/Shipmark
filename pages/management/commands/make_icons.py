"""Команда make_icons: перемальовує растрові іконки й картинку поширення.

Redraw the raster icons from docs/new_logo/logo.png and the share image from static/brand/logo.svg.

    python manage.py make_icons

Writes favicon.ico (16/32/48 px), favicon.png (32 px), apple-touch-icon.png (180 px), and og-default.png (1200×630).
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from config import branding
from pages.brand_icons import apple_touch_icon, favicon_ico, favicon_png, og_default_image


class Command(BaseCommand):
    """Команда make_icons."""
    help = "Redraw the tab and touch icons from docs/new_logo/logo.png and the share image from the logo."

    def handle(self, *args, **options):
        """Записує favicon.ico і apple-touch-icon."""
        static_dir = settings.STATICFILES_DIRS[0]
        for name, data in ((branding.FAVICON_ICO, favicon_ico()), ("brand/favicon.png", favicon_png()),
                           (branding.APPLE_TOUCH_ICON, apple_touch_icon()), (branding.OG_DEFAULT_IMAGE, og_default_image())):
            (static_dir / name).write_bytes(data)
            self.stdout.write(f"Wrote static/{name} ({len(data)} bytes)")

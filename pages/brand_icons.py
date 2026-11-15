"""Растрові іконки, намальовані з SVG-знака логотипа.

Raster icons drawn from the logo mark (static/brand/logo-mark.svg), so every icon is the same logo C.

    python manage.py make_icons     # after changing logo-mark.svg: rewrites favicon.ico and apple-touch-icon.png

The mark is one path of straight lines (M, H, V, L, Z; even-odd). It is drawn 16x larger and scaled down,
which gives clean edges without an SVG renderer.
"""
import io
import re

from django.contrib.staticfiles import finders
from PIL import Image, ImageDraw

from config import branding

INK = "#071C1E"  # --text (light theme)
PAPER = "#F3F6F7"  # --paper (light theme)
ICO_SIZES = (16, 32, 48)
TOUCH_SIZE = 180
TOUCH_MARK = 96  # the mark inside the touch icon; the rest is the dark plate around it
SCALE = 16


def mark_path():
    """Атрибут d першого контуру logo-mark.svg.

    The `d` of the first <path> in logo-mark.svg."""
    with open(finders.find(branding.LOGO_MARK), encoding="utf-8") as fh:
        match = re.search(r'<path[^>]*\sd="([^"]+)"', fh.read())
    return match.group(1)


def polygons(d):
    """Перетворює команди контуру на списки точок.

    M/H/V/L/Z absolute commands -> list of point lists (viewBox units)."""
    shapes, points, x, y = [], [], 0.0, 0.0
    for cmd, args in re.findall(r"([MHVLZ])([^MHVLZ]*)", d.replace(",", " ")):
        nums = [float(n) for n in args.split()]
        if cmd == "M":
            if points:
                shapes.append(points)
            x, y = nums[0], nums[1]
            points = [(x, y)]
            nums = nums[2:]
            cmd = "L"  # extra pairs after M are lines
        if cmd == "Z":
            if points:
                shapes.append(points)
            points = []
            continue
        if cmd == "H":
            for x in nums:
                points.append((x, y))
        elif cmd == "V":
            for y in nums:
                points.append((x, y))
        elif cmd == "L":
            for i in range(0, len(nums), 2):
                x, y = nums[i], nums[i + 1]
                points.append((x, y))
    if points:
        shapes.append(points)
    return shapes


def draw_mark(size, ink, hole, background=None, mark_size=None, units=32):
    """Малює знак заданого розміру.

    The mark at `size` px. The first shape is the square, the others are cut out (filled with `hole`)."""
    mark_size = mark_size or size
    big, offset = size * SCALE, (size - mark_size) * SCALE / 2
    factor = mark_size * SCALE / units
    image = Image.new("RGBA", (big, big), background or (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for i, shape in enumerate(polygons(mark_path())):
        draw.polygon([(offset + px * factor, offset + py * factor) for px, py in shape], fill=ink if i == 0 else hole)
    return image.resize((size, size), Image.Resampling.BOX)  # area average: no ringing at the edges


def favicon_ico():
    """Іконка favicon.ico.

    Opaque: a dark square with the slash and stop in paper color, readable on light and dark tab bars."""
    images = [draw_mark(size, INK, PAPER) for size in ICO_SIZES]  # each size drawn on its own: sharp at 16 px
    out = io.BytesIO()
    images[-1].save(out, format="ICO", sizes=[(s, s) for s in ICO_SIZES], append_images=images[:-1])
    return out.getvalue()


def apple_touch_icon():
    """Іконка apple-touch-icon.

    A paper-colored mark on a dark plate (iOS rounds the corners itself)."""
    image = draw_mark(TOUCH_SIZE, PAPER, INK, background=INK, mark_size=TOUCH_MARK).convert("RGB")
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()

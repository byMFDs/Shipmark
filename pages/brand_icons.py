"""Растрові іконки вкладки з артворка й зображення поширення з векторного логотипа.

Uses Pillow only. Tab and touch icons are cut from docs/new_logo/logo.png; the share image reads the current SVG logo.
The supported SVG paths use absolute M, L, H, V, Q, C and Z commands. Curves are sampled before supersampling.
"""
import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from django.contrib.staticfiles import finders
from PIL import Image, ImageChops, ImageDraw

from config import branding

ICON_SOURCE = Path(__file__).resolve().parent.parent / "docs" / "new_logo" / "logo.png"
INK = "#20251F"
GREEN = "#B6FF3B"
ICO_SIZES = (16, 32, 48)
TOUCH_SIZE = 180
SCALE = 16


def mark_path():
    """Читає контур знака з єдиного SVG-джерела."""
    root = ET.parse(finders.find(branding.LOGO_MARK)).getroot()
    return root.find("{http://www.w3.org/2000/svg}path").get("d")


def polygons(d):
    """Перетворює прямі та криві SVG на контури для Pillow."""
    shapes, points = [], []
    x = y = 0.0
    for cmd, args in re.findall(r"([A-Za-z])([^A-Za-z]*)", d):
        if cmd not in "MLHVQCZ":
            raise ValueError(f"Unsupported SVG command: {cmd}")
        nums = [float(n) for n in re.findall(r"-?[0-9]+(?:[.][0-9]+)?", args)]
        if cmd == "Z":
            if points:
                shapes.append(points)
            points = []
            continue
        step = {"M": 2, "L": 2, "H": 1, "V": 1, "Q": 4, "C": 6}[cmd]
        if not nums or len(nums) % step:
            raise ValueError("Incomplete SVG coordinates")
        for offset in range(0, len(nums), step):
            values = nums[offset:offset + step]
            if cmd == "M":
                if points:
                    shapes.append(points)
                x, y = values
                points = [(x, y)]
                cmd = "L"
            elif cmd in "LHV":
                x, y = values if cmd == "L" else (values[0], y) if cmd == "H" else (x, values[0])
                points.append((x, y))
            else:
                controls = [(x, y), *list(zip(values[::2], values[1::2]))]
                for index in range(1, 33):
                    t = index / 32
                    sampled = controls
                    while len(sampled) > 1:
                        sampled = [((1-t)*a[0]+t*b[0], (1-t)*a[1]+t*b[1])
                                   for a, b in zip(sampled, sampled[1:])]
                    points.append(sampled[0])
                x, y = values[-2:]
    if points:
        shapes.append(points)
    return shapes


def path_mask(d, size, factor, origin=(0, 0), scale=SCALE):
    """Малює маску контуру з отворами та згладженими краями."""
    big = (size[0] * scale, size[1] * scale)
    mask = Image.new("L", big, 128)
    for shape in polygons(d):
        layer = Image.new("L", big)
        ImageDraw.Draw(layer).polygon(
            [((origin[0] + px * factor) * scale, (origin[1] + py * factor) * scale) for px, py in shape], fill=1)
        winding = sum(a[0]*b[1] - b[0]*a[1] for a, b in zip(shape, [*shape[1:], shape[0]]))
        mask = ImageChops.add(mask, layer) if winding > 0 else ImageChops.subtract(mask, layer)
    # SVG's default nonzero fill preserves overlapping stems and cuts reverse-wound counters.
    return mask.point(lambda value: 255 if value != 128 else 0).resize(size, Image.Resampling.BOX)


def icon_artwork():
    """Вирізає заокруглений квадрат із білого тла джерела.

    Alpha is how far the blue channel falls from white (255) to the artwork green (59); the S is darker still, so
    the inside stays opaque. Edge pixels take the pure green, so no white fringe survives the cut.
    """
    source = Image.open(ICON_SOURCE).convert("RGB")
    alpha = source.getchannel("B").point(lambda blue: min(255, round((255 - blue) * 255 / 196)))
    fringe = alpha.point(lambda value: 255 if value < 255 else 0)
    artwork = Image.composite(Image.new("RGB", source.size, GREEN), source, fringe)
    artwork.putalpha(alpha)
    return artwork.crop(alpha.getbbox())


def icon_image(size):
    """Зменшує артворк до квадратної іконки заданого розміру.

    At 16 px the S strokes are thinner than a pixel, so their tones are pushed towards pure ink or pure green.
    """
    image = icon_artwork().resize((size, size), Image.Resampling.LANCZOS)
    if size > 16:
        return image
    tone = image.getchannel("G").point(lambda value: max(0, min(255, round(127.5 + (value - 127.5) * 1.6))))
    crisp = ImageChops.multiply(Image.merge("RGB", (tone, tone, tone)), Image.new("RGB", image.size, GREEN))
    crisp.putalpha(image.getchannel("A"))
    return crisp


def favicon_png():
    """Експортує PNG-фавікон 32 пікселі з прозорими кутами."""
    out = io.BytesIO()
    icon_image(32).save(out, format="PNG", optimize=True)
    return out.getvalue()


def favicon_ico():
    """Експортує фавікон у трьох розмірах ICO."""
    images = [icon_image(size) for size in ICO_SIZES]
    out = io.BytesIO()
    images[-1].save(out, format="ICO", sizes=[(s, s) for s in ICO_SIZES], append_images=images[:-1])
    return out.getvalue()


def apple_touch_icon():
    """Експортує іконку для iOS із прозорими кутами."""
    out = io.BytesIO()
    icon_image(TOUCH_SIZE).save(out, format="PNG", optimize=True)
    return out.getvalue()


def og_default_image():
    """Експортує знак і чинний вордмарк на зеленому тлі 1200×630."""
    image = Image.new("RGB", (1200, 630), GREEN)
    root = ET.parse(finders.find(branding.LOGO)).getroot()
    _, _, width, height = [float(n) for n in root.get("viewBox").split()]
    factor = 5
    size = (round(width * factor), round(height * factor))
    logo = Image.new("RGB", size, GREEN)
    for path in root.findall("{http://www.w3.org/2000/svg}path"):
        logo.paste(INK, (0, 0, *size), path_mask(path.get("d"), size, factor, scale=4))
    image.paste(logo, ((1200-size[0])//2, (630-size[1])//2))
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()

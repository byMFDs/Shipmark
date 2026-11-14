"""Єдиний конвеєр картинок: лише зображення, перевірка Pillow, перекодування.

Screenshot uploads (CLAUDE.md section 6): images only, checked with Pillow, re-encoded.

Re-encoding to a fresh WebP file drops EXIF/GPS and any data hidden in the original file.
The user's file name and bytes are never stored.
"""
import io

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 25_000_000  # checked before decoding, so a small "decompression bomb" file cannot eat memory
MAX_SIDE = 1600  # stored size; bigger images are scaled down
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def clean_image(upload, fit=None):
    """Перевіряє файл і повертає WebP.

    Validate an uploaded file and return a ContentFile with WebP bytes. Raises ValidationError.

    `fit=(width, height)` scales and centre-crops to exactly that size (avatars, covers); without it the image
    is only scaled down to MAX_SIDE (screenshots). Metadata is dropped either way.
    """
    if upload.size > MAX_BYTES:
        raise ValidationError(_("The image is larger than 5 MB."), code="too_big")
    try:
        probe = Image.open(upload)
        probe.verify()  # checks the file structure; the image must be opened again after this
        upload.seek(0)
        image = Image.open(upload)
        if image.format not in ALLOWED_FORMATS:
            raise ValidationError(_("Use a PNG, JPEG or WebP image."), code="bad_type")
        width, height = image.size
        if width < 1 or height < 1 or width * height > MAX_PIXELS:
            raise ValidationError(_("The image is too big (too many pixels). Use a smaller one."), code="too_large_dimensions")
        image = ImageOps.exif_transpose(image)  # apply the camera rotation before metadata is dropped
        image = image.convert("RGBA" if "A" in image.getbands() or image.mode == "P" else "RGB")
        if fit:
            image = ImageOps.fit(image, fit, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        else:
            image.thumbnail((MAX_SIDE, MAX_SIDE))
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=85, method=4)  # no exif= argument: metadata is not copied
    except ValidationError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise ValidationError(_("We could not open this file as an image."), code="invalid") from None
    return ContentFile(buffer.getvalue(), name="image.webp")  # real name is random, see the upload_to functions


def clean_screenshot(upload):
    return clean_image(upload)


AVATAR_SIZE = (512, 512)
COVER_SIZE = (1500, 500)


def clean_avatar(upload):
    return clean_image(upload, fit=AVATAR_SIZE)


def clean_cover(upload):
    return clean_image(upload, fit=COVER_SIZE)


THUMB_BOX = (640, 640)  # longest sides; lists show it at 80-640 CSS pixels, so this is enough for 2x screens


def make_thumbnail(fileobj):
    """Маленька WebP-копія для списків і карток.

    A small WebP copy of an already cleaned image (clean_image output), for lists and cards. Returns ContentFile.

    The full image stays for the project page; feeds, profiles and Explore load this one (a few KB, not hundreds)."""
    image = Image.open(fileobj)
    image.load()
    image = image.convert("RGBA" if "A" in image.getbands() or image.mode == "P" else "RGB")
    image.thumbnail(THUMB_BOX, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=78, method=4)
    return ContentFile(buffer.getvalue(), name="thumb.webp")

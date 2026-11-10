"""Screenshot uploads (CLAUDE.md section 6): images only, checked with Pillow, re-encoded.

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


def clean_screenshot(upload):
    """Validate an uploaded file and return (ContentFile with WebP bytes). Raises ValidationError."""
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
            raise ValidationError(_("The image has too many pixels."), code="too_large_dimensions")
        image = ImageOps.exif_transpose(image)  # apply the camera rotation before metadata is dropped
        image.thumbnail((MAX_SIDE, MAX_SIDE))
        image = image.convert("RGBA" if "A" in image.getbands() or image.mode == "P" else "RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=85, method=4)  # no exif= argument: metadata is not copied
    except ValidationError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise ValidationError(_("This file is not a valid image."), code="invalid") from None
    return ContentFile(buffer.getvalue(), name="screenshot.webp")  # real name is random, see screenshot_path

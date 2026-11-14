"""Картинки тем і відповідей через єдиний конвеєр зображень сайту.

Pictures on threads and replies. Validation and re-encoding are the site's one pipeline (projects.images):
PNG, JPEG or WebP, at most 5 MB and 25 million pixels, re-encoded to WebP without metadata, random file names.
Each picture is stored twice: a display copy (longest side 1600) and a 640 thumbnail for lists.
Every read, write and delete goes through the storage API, so media can move to S3 by settings alone.
"""
from projects.images import clean_image, make_thumbnail

from .models import CommunityImage


def clean_upload(upload):
    """Перевіряє завантажений файл і повертає копію для показу.

    An uploaded file -> ContentFile with the display copy. Raises ValidationError."""
    return clean_image(upload)


def store_images(contents, uploader, *, thread=None, reply=None):
    """Зберігає перевірені картинки для теми чи відповіді в заданому порядку.

    Save already cleaned images (ContentFile) for one thread or one reply, in the given order."""
    stored = []
    for order, content in enumerate(contents):
        content.seek(0)
        thumb = make_thumbnail(content)
        content.seek(0)
        image = CommunityImage(thread=thread, reply=reply, uploader=uploader, order=order)
        image.image.save("image.webp", content, save=False)
        image.thumb.save("thumb.webp", thumb, save=False)
        image.save()
        stored.append(image)
    return stored


def delete_images(**target):
    """Видаляє рядки картинок; файли зникають після коміту.

    Delete the rows of a thread or reply (`thread=` / `reply=` / `uploader=`); the files follow on commit
    (community/signals.py). Returns how many rows went."""
    rows = list(CommunityImage.objects.filter(**target))
    for row in rows:
        row.delete()
    return len(rows)

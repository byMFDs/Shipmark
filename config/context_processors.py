"""Змінні для всіх шаблонів: бренд, навігація хедера, кількість людей."""
from types import SimpleNamespace

from config import branding

# Built once: only the UPPERCASE names of branding.py become `brand.<NAME>` in templates.
_BRAND = SimpleNamespace(**{name: getattr(branding, name) for name in dir(branding) if name.isupper()})


def brand(request):
    return {"brand": _BRAND}

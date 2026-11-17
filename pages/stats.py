"""Публічне число «<n> людей приєдналося» в хедері.

The public "<n> people joined" number in the site header."""
import math

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.formats import number_format
from django.utils.translation import gettext, ngettext

from accounts.people import DEMO_DOMAIN, DEMO_PREFIX

CACHE_KEY = "stats:public_user_count"
CACHE_SECONDS = 60
EXACT_UP_TO = 99_999


def count_people():
    """Скільки людей приєдналося (правило в одному місці).

    How many people have joined: the rule, in one place.

    Counted: every account row that exists (a deleted account is gone from the table) and is active
    (`is_active`; Django's flag for an account that may sign in). Not counted: system accounts that are not
    people (`is_system_account`, today the official account that publishes news), and the demo accounts of seed_community
    (`demo-…` with an @example.invalid address). Suspended and banned people still count: they did join. Nothing
    is added or estimated; the number moves only when accounts are created or deleted.
    """
    people = get_user_model().objects.filter(is_active=True).exclude(is_system_account=True)
    return people.exclude(username__startswith=DEMO_PREFIX, email__endswith=DEMO_DOMAIN).count()


def public_user_count():
    """Те саме число з кешем на 60 секунд.

    count_people(), cached for 60 seconds so the header costs at most one query a minute."""
    value = cache.get(CACHE_KEY)
    if value is None:
        value = count_people()
        cache.set(CACHE_KEY, value, CACHE_SECONDS)
    return value


def format_count(value):
    """Число для показу з групуванням цифр або скорочене.

    Exact with the language's digit grouping up to 99,999 ("12,480", "12 480"); compact above, rounded down so
    the number is never larger than the truth ("128K", "1.2M")."""
    if value <= EXACT_UP_TO:
        return number_format(value, force_grouping=True)
    if value < 1_000_000:
        return gettext("%(n)sK") % {"n": number_format(value // 1000, force_grouping=True)}
    millions = math.floor(value / 100_000) / 10 if value < 10_000_000 else value // 1_000_000
    decimals = 1 if isinstance(millions, float) and millions % 1 else 0
    return gettext("%(n)sM") % {"n": number_format(millions, decimal_pos=decimals, force_grouping=True)}


def header_stat():
    """Дані для хедера або None, якщо показ вимкнено.

    {value, text} for the header, or None when the stat is switched off or not above PUBLIC_USER_COUNT_MIN."""
    if not settings.PUBLIC_USER_COUNT_ENABLED:
        return None
    value = public_user_count()
    if value <= settings.PUBLIC_USER_COUNT_MIN:
        return None
    text = format_count(value)
    sentence = ngettext("%(count)s person joined", "%(count)s people joined", value)
    before, _sep, after = sentence.partition("%(count)s")
    exact = sentence.replace("%(count)s", number_format(value, force_grouping=True))
    return {"value": value, "text": text, "before": before, "after": after, "exact": exact,
            "animate": value <= EXACT_UP_TO}

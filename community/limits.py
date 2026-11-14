"""Усі числа правил спільноти в одному місці.

Every number of the community rules, in one place (docs/COMMUNITY_PLAN.md section 5)."""
from datetime import timedelta

MAX_TITLE = 120
MIN_TITLE = 5
MAX_THREAD_BODY = 8000
MAX_REPLY_BODY = 4000
MAX_DEPTH = 3
MAX_THREAD_IMAGES = 4
MAX_REPLY_IMAGES = 2
MAX_ALT = 120

# Age of the account (User.date_joined). Moderators and superusers are exempt.
MIN_ACCOUNT_AGE = timedelta(minutes=10)  # younger: no threads, replies or votes
YOUNG_ACCOUNT_AGE = timedelta(hours=24)  # younger: at most one link per post, no images
YOUNG_MAX_LINKS = 1

# Per person, per hour (config.ratelimit).
HOUR = 3600
THREADS_PER_HOUR = 5
REPLIES_PER_HOUR = 30
VOTES_PER_HOUR = 120
UPLOADS_PER_HOUR = 10  # counted per image, before Pillow opens it
EDITS_PER_HOUR = 30
DELETES_PER_HOUR = 60

# The same text again is refused for this long.
DUPLICATE_THREAD_WINDOW = 24 * 3600
DUPLICATE_REPLY_WINDOW = 10 * 60
# A short reply ("Thanks!") is only a duplicate under the same parent; a long one anywhere.
DUPLICATE_SHORT = 20

EDIT_SILENT_WINDOW = timedelta(minutes=15)  # later edits show "edited"; the title can only change inside it

# Reply notifications: kept this long, then deleted by `manage.py community_daily`.
NOTIFICATION_RETENTION = timedelta(days=90)
NOTIFICATIONS_PER_PAGE = 30

THREADS_PER_PAGE = 20
REPLIES_PER_PAGE = 30  # top-level replies; their branches come with them
MAX_SEARCH = 80
MIN_SEARCH = 2

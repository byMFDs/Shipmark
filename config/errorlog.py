"""Error log files: one JSON object per line, for `manage.py show_errors`.

- errors.jsonl: unhandled exceptions, 5xx responses, 403 (including CSRF failures) and other ERROR records.
- notfound.jsonl: 404s, the same path at most once per minute (per process), so bots cannot flood it.

Both files rotate at 5 MB and keep 5 old copies. The folder is settings.LOG_DIR (env LOG_DIR).

Privacy (docs/DATA_INVENTORY.md): a line holds only the fields in `_fields()`. Never the IP, user agent,
cookies, headers, query string or POST body. Usernames in paths are masked, and every text field goes
through `scrub()`, which removes emails, IP addresses, tokens and secret-looking values.
"""
import json
import logging
import re
import threading
import time
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5
ERRORS_FILE = "errors.jsonl"
NOTFOUND_FILE = "notfound.jsonl"
NOTFOUND_WINDOW = 60  # seconds
MAX_MESSAGE = 2000
MAX_TRACEBACK = 20000

# The request being handled, set by config.middleware.RequestIdMiddleware. Lets records from any logger
# (not only django.request, which attaches the request itself) carry the request id, method and path.
current_request = ContextVar("current_request", default=None)


# ---------- Scrubbing ----------

_SECRET_KEY = r"[\w-]*(?:password|passwd|secret|token|api_?key|apikey|private_?key|access_?key|session_?id|sessionid|session_?key|csrf\w*|authorization|cookie|signature)[\w-]*"
_RULES = [
    # Anything that looks like a query string: "?a=1&b=2" (the path is kept, the query is not).
    (re.compile(r"\?[^\s\"'<>()\[\]]*=[^\s\"'<>()\[\]]*"), "?[query removed]"),
    # Before the key=value rule, so "Authorization: Bearer <token>" loses the token too.
    (re.compile(r"(?i)\b(bearer|basic|token)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 [redacted]"),
    # key=value / key: value / "key": "value" where the key sounds secret.
    (re.compile(r"(?i)(\b" + _SECRET_KEY + r"\b[\"']?\s*[=:]\s*)([\"']?)[^\s\"',;&]+"), r"\1\2[redacted]"),
    (re.compile(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{10,}"), "[redacted]"),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[email]"),
    (re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])"), "[ip]"),
    (re.compile(r"(?i)(?<![\w:])(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}(?![\w:])"), "[ip]"),
    (re.compile(r"(?i)(?<![\w:])(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){0,6})?::(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){0,6})?(?![\w:])"), "[ip]"),
    # Long random-looking strings (keys, signed values): letters and digits mixed, 32+ characters.
    (re.compile(r"\b(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{32,}\b"), "[redacted]"),
]
# Profile and badge paths name a person: /u/<username>/..., /badge/<username>.svg
_USER_PATH = re.compile(r"(/(?:u|badge)/)[^/\s?#.\"']+")


def mask_path(path):
    return _USER_PATH.sub(r"\1[user]", path or "")


def scrub(text, limit=MAX_MESSAGE):
    text = str(text or "")
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    text = mask_path(text)
    return text if len(text) <= limit else text[:limit] + " [cut]"


# ---------- Records ----------

def _exception_name(exc_type):
    if exc_type is None:
        return ""
    module = getattr(exc_type, "__module__", "")
    name = getattr(exc_type, "__qualname__", exc_type.__name__)
    return name if module in ("builtins", "") else f"{module}.{name}"


def _fields(record, with_traceback=True):
    request = getattr(record, "request", None) or current_request.get()
    match = getattr(request, "resolver_match", None) if request is not None else None
    exc_info = record.exc_info if record.exc_info and record.exc_info[0] else None
    data = {
        "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
        "level": record.levelname,
        "request_id": getattr(request, "request_id", "") if request is not None else "",
        # request.path never contains the query string.
        "method": getattr(request, "method", "") or "" if request is not None else "",
        "path": mask_path(getattr(request, "path", "")) if request is not None else "",
        "status": getattr(record, "status_code", None),
        "view": (match.view_name or "") if match else "",
        "exception": _exception_name(exc_info[0]) if exc_info else "",
        "message": scrub(record.getMessage()),
    }
    if with_traceback:
        data["traceback"] = scrub("".join(traceback.format_exception(*exc_info)), MAX_TRACEBACK) if exc_info else ""
    return data


class ErrorJsonFormatter(logging.Formatter):
    def format(self, record):
        # json.dumps escapes newlines and quotes: text a visitor controls cannot forge a second line.
        return json.dumps(_fields(record), ensure_ascii=False, default=str)


class NotFoundJsonFormatter(logging.Formatter):
    def format(self, record):
        data = _fields(record, with_traceback=False)
        for key in ("exception", "message", "view"):
            data.pop(key)
        return json.dumps(data, ensure_ascii=False, default=str)


# ---------- Filters ----------

class ErrorsFilter(logging.Filter):
    """Unhandled exceptions, 5xx, 403 (CSRF failures are 403 too), and ERROR records outside a response."""

    def filter(self, record):
        status = getattr(record, "status_code", None)
        if status is not None:
            return status >= 500 or status == 403
        return record.levelno >= logging.ERROR


class NotFoundFilter(logging.Filter):
    """404s only, each path at most once per NOTFOUND_WINDOW seconds in this process."""

    _seen = {}
    _lock = threading.Lock()

    def filter(self, record):
        if getattr(record, "status_code", None) != 404:
            return False
        request = getattr(record, "request", None)
        key = mask_path(getattr(request, "path", "")) if request is not None else ""
        now = time.monotonic()
        with self._lock:
            last = self._seen.get(key)
            if last is not None and now - last < NOTFOUND_WINDOW:
                return False
            if len(self._seen) > 10_000:  # bounded memory; the worst case is one extra line per path
                self._seen.clear()
            self._seen[key] = now
        return True

    @classmethod
    def reset(cls):
        with cls._lock:
            cls._seen.clear()


# ---------- Handler ----------

class JsonLinesFileHandler(RotatingFileHandler):
    """RotatingFileHandler that creates its folder. The file is opened on the first line written."""

    def __init__(self, filename, **kwargs):
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        kwargs.setdefault("maxBytes", MAX_BYTES)
        kwargs.setdefault("backupCount", BACKUP_COUNT)
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("delay", True)
        super().__init__(filename, **kwargs)


def file_handlers(log_dir):
    """dictConfig pieces for the two files. Returned as (formatters, filters, handlers)."""
    log_dir = Path(log_dir)
    formatters = {
        "error_json": {"()": "config.errorlog.ErrorJsonFormatter"},
        "notfound_json": {"()": "config.errorlog.NotFoundJsonFormatter"},
    }
    filters = {
        "errors_only": {"()": "config.errorlog.ErrorsFilter"},
        "notfound_only": {"()": "config.errorlog.NotFoundFilter"},
    }
    handlers = {
        "errors_file": {
            "()": "config.errorlog.JsonLinesFileHandler", "filename": str(log_dir / ERRORS_FILE),
            "level": "WARNING", "formatter": "error_json", "filters": ["errors_only"],
        },
        "notfound_file": {
            "()": "config.errorlog.JsonLinesFileHandler", "filename": str(log_dir / NOTFOUND_FILE),
            "level": "WARNING", "formatter": "notfound_json", "filters": ["notfound_only"],
        },
    }
    return formatters, filters, handlers

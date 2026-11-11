"""One-line JSON log records on stdout (production). Standard library only.

Used by config/settings/prod.py (Django) and gunicorn.conf.py (gunicorn's own logs), so every
line the server writes has the same shape and can be read with `jq` or shipped to a log service.
"""
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Set by django.request on 4xx/5xx responses.
        status_code = getattr(record, "status_code", None)
        if status_code is not None:
            data["status"] = status_code
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        # json.dumps escapes quotes and newlines, so text a visitor controls (a request path)
        # cannot break out of its field or forge a second log line.
        return json.dumps(data, ensure_ascii=False, default=str)


def logging_config(level="INFO", log_dir=None, stdout=True):
    """dictConfig: JSON lines on stdout, plus the error files in `log_dir` (config/errorlog.py) when given.

    Privacy: no IP addresses and no user agents are logged. gunicorn.conf.py calls this without `log_dir`
    (gunicorn's master process has no Django settings); Django adds the files in each worker.
    """
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": "config.jsonlog.JsonFormatter"}},
        "filters": {},
        "handlers": {},
        "root": {"handlers": [], "level": level},
        "loggers": {},
    }
    if stdout:
        config["handlers"]["stdout"] = {"class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "json"}
        config["root"]["handlers"].append("stdout")
        # gunicorn.access writes one line per request; keep it from also reaching the root handler.
        config["loggers"] = {
            "gunicorn.error": {"handlers": ["stdout"], "level": level, "propagate": False},
            "gunicorn.access": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        }
    if log_dir:
        from config.errorlog import file_handlers

        formatters, filters, handlers = file_handlers(log_dir)
        config["formatters"].update(formatters)
        config["filters"].update(filters)
        config["handlers"].update(handlers)
        config["root"]["handlers"] += list(handlers)
    return config

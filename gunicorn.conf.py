"""Налаштування gunicorn для production; усе можна змінити змінними оточення.

gunicorn settings. Start with:  gunicorn config.wsgi -c gunicorn.conf.py
Run it from the project root, with DJANGO_SETTINGS_MODULE=config.settings.prod and the .env variables set
(wsgi.py already defaults to prod). Every value can be overridden from the environment.
"""
import os

from config.jsonlog import logging_config

# Listen on localhost only: the reverse proxy (nginx, Caddy, ...) is the one facing the internet.
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")

# Rule of thumb is 2 x CPU cores + 1. Each worker holds one DB connection (CONN_MAX_AGE in prod.py),
# so keep workers well below PostgreSQL's max_connections (default 100).
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))

# A request that takes longer is killed and the worker restarted. Outbound checks (safe_fetch) time out
# after 5 s, so 30 s is generous. Restarting workers now and then also caps slow memory growth.
timeout = 30
graceful_timeout = 30
keepalive = 5
max_requests = 2000
max_requests_jitter = 200

# Logs: JSON on stdout (see config/jsonlog.py). The access line is "METHOD /path STATUS BYTES MILLISECONDS".
# No query string, no client IP, no user agent: the privacy page says we do not record IP addresses.
accesslog = "-"
access_log_format = "%(m)s %(U)s %(s)s %(B)s %(M)sms"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
logconfig_dict = logging_config(loglevel.upper())

# Not needed for HTTPS detection: Django reads X-Forwarded-Proto itself (SECURE_PROXY_SSL_HEADER),
# which is why the proxy must overwrite that header. See docs/DEPLOY_NOTES.md.

# gunicorn 25+ opens an admin control socket (default /run/user/<uid>/gunicorn.ctl). We do not use it.
control_socket_disable = True

# Deploy notes

## Cron jobs

Background work runs as Django management commands from cron (no Celery).
Paths below assume the app lives in `/srv/shipmark` with its virtualenv in `.venv`; change them to yours.

`manage.py` defaults to the dev settings, so every line sets `DJANGO_SETTINGS_MODULE` explicitly.
`flock -n` skips a run if the previous one is still going, so slow sites never pile up runs.

```cron
SHELL=/bin/bash
DJANGO_SETTINGS_MODULE=config.settings.prod

# Uptime (Steady hallmark): every 15 minutes. Each project is still checked at most once per 3 hours;
# the frequent run only spreads the work. Also deletes checks older than 90 days.
*/15 * * * *  cd /srv/shipmark && flock -n /tmp/shipmark-uptime.lock .venv/bin/python manage.py check_uptime >> /var/log/shipmark/uptime.log 2>&1

# Domain re-verification (Live hallmark): once a day. Re-checks domains not confirmed in 30 days.
30 4 * * *    cd /srv/shipmark && flock -n /tmp/shipmark-reverify.lock .venv/bin/python manage.py reverify_domains >> /var/log/shipmark/reverify.log 2>&1
```

Create the log directory once: `mkdir -p /var/log/shipmark` (owned by the user that runs cron).

Steady needs at least 40 checks in 30 days. With checks every 3–3.25 hours a project gets about
220 a month, so a few missed runs do not matter. If cron stops for more than a few days,
Steady disappears until enough new checks are collected.

## Checking by hand

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py check_uptime -v 2   # lists sites that are down
DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py reverify_domains -v 2
```

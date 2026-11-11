# Deploy notes

No hosting provider is chosen yet. Everything here works on any Linux server with PostgreSQL, a reverse proxy and cron.
Paths assume the app lives in `/srv/shipmark` with its virtualenv in `.venv`; change them to yours.

## Environment variables

Set them in the real environment or in `/srv/shipmark/.env` (gitignored; real variables win over the file).
`.env.example` has the same list with comments.

| Variable | Required in prod | Meaning |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | yes (`config.settings.prod`) | `wsgi.py` defaults to prod, but `manage.py` defaults to **dev**, so cron and shell commands must set it |
| `SECRET_KEY` | yes | Signs sessions and CSRF tokens. `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `SECRET_KEY_FALLBACKS` | no | Old keys while rotating (see below) |
| `DATABASE_URL` | yes | `postgres://USER:PASSWORD@HOST:5432/DBNAME` (percent-encode special characters in the password) |
| `ALLOWED_HOSTS` | yes | Comma-separated host names, e.g. `example.com,www.example.com` |
| `CSRF_TRUSTED_ORIGINS` | yes | With scheme, e.g. `https://example.com` |
| `SITE_URL` | no | Public address used in embed snippets, Open Graph, canonical links and the data export. Default `https://shipmark.me` (from `SITE_DOMAIN`); must be https. Dev default `http://localhost:8000` |
| `ADMIN_URL` | yes | Private admin address, e.g. `staff-4f8k2/`. `admin/` is refused at startup |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | yes | OAuth App. Callback URL: `https://YOUR.DOMAIN/accounts/github/login/callback/` |
| `GITHUB_API_TOKEN` | recommended | Token with **no scopes**; lifts the repo check limit from 60 to 5000 requests/hour |
| `MEDIA_ROOT` | no | Folder for uploads. Default `<project>/media` |
| `SECURE_HSTS_SECONDS` | no | Default 3600. Raise to 31536000 after HTTPS has worked for a few days |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | no | Default true |
| `LOG_LEVEL` | no | Default `INFO` |
| `LOG_DIR` | no | Folder for `errors.jsonl` and `notfound.jsonl`. Default `<project>/logs`. Must be writable by the gunicorn user |
| `GUNICORN_BIND`, `WEB_CONCURRENCY` | no | Default `127.0.0.1:8000`, 3 workers |
| `DEBUG` | no | Ignored in prod (always off) |

## Each release

```bash
cd /srv/shipmark && source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.prod
git pull
pip install -r requirements/prod.txt
pip-audit -r requirements/prod.txt              # no known vulnerabilities
python manage.py collectstatic --noinput        # copies static/ to staticfiles/ with hashed names
python manage.py migrate
python manage.py createcachetable               # first deploy only; harmless to repeat
python manage.py check --deploy                 # must print "no issues"
# then restart gunicorn
```

Start command (from the project root): `gunicorn config.wsgi -c gunicorn.conf.py`.
Settings are in `gunicorn.conf.py` (bind to localhost, 3 workers, 30 s timeout, workers recycled after ~2000 requests).
Run it under a process manager (systemd or similar) so it restarts after a crash or reboot.

Things that must be true on the server:

- The reverse proxy **overwrites** `X-Forwarded-Proto` (never passes the client's value through). Django trusts it
  (`SECURE_PROXY_SSL_HEADER`); if gunicorn is reachable directly, anyone can fake HTTPS.
- The proxy serves `/media/` from `MEDIA_ROOT` and allows request bodies a bit above the 5 MB image limit
  (nginx: `client_max_body_size 10m;`).
- The user running gunicorn can write to `MEDIA_ROOT`. Static files need nothing from the proxy: WhiteNoise serves them
  (hashed names, gzip/brotli, far-future cache) from `staticfiles/`, so run `collectstatic` before every restart.
- Static files: if `collectstatic` or a page fails with "Missing staticfiles manifest entry", a template points to a
  file that does not exist in `static/`. Fix the reference; do not work around it.

### Uploads and later S3-compatible storage

Screenshots are stored on the server's disk in `MEDIA_ROOT`. This is fine for one server, but the folder is part of the
data: back it up (below), and it does not follow you if the app runs on more than one machine.
`config/settings/prod.py` has a 4-step note for moving to S3-compatible storage. It needs `django-storages`, which is not
on the allowed list yet, so decide that together first. No model or view changes are needed.

### Logs

Everything is one JSON object per line on stdout: the app, Django errors (`django.request` for 4xx/5xx), and gunicorn
(`gunicorn.access`: `METHOD /path STATUS BYTES MILLISECONDS`). The process manager collects it
(systemd: `journalctl -u shipmark -o cat | jq .`). Client IP addresses and user agents are **not** logged by the app,
because the privacy page says we do not record IPs. The reverse proxy has its own access log; decide its retention
(see the checklist).

### Error log files and `show_errors`

Besides stdout, every worker writes two JSON-lines files to `LOG_DIR` (`config/errorlog.py`):

- `errors.jsonl`: unhandled exceptions, 5xx, 403 and CSRF failures.
- `notfound.jsonl`: 404s, the same path at most once per minute per worker, so scanners cannot flood it.

Each line: `timestamp, level, request_id, method, path, status, view, exception, message, traceback`
(404 lines have no view, exception, message or traceback). The path has no query string and `/u/<name>/` is written
as `/u/[user]/`; message and traceback are scrubbed of emails, IPs, tokens and secret-looking values. Never logged:
IP, user agent, cookies, headers, query string, POST body. Both files rotate at 5 MB and keep 5 old copies
(`errors.jsonl.1` … `.5`), so they never take more than 60 MB together; no `logrotate` rule is needed.

Every response has an `X-Request-ID` header. The 500, 403 and "form expired" pages show the same id as
"Reference: 3f9a1c2e", so when someone reports an error you can find its line.

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py show_errors                 # last 20 errors, grouped by exception, newest first
python manage.py show_errors --last 100 --full   # with tracebacks
python manage.py show_errors --summary       # one line per exception: count, first/last time, top paths
python manage.py show_errors --notfound      # most requested missing paths
grep 3f9a1c2e "$LOG_DIR"/errors.jsonl* | jq . # one reference
```

Error pages: 400, 403, 404, 500 and the CSRF failure are custom (`config/errors.py`, `templates/`). The 500, 400 and
CSRF pages use no database, session or context processor. With `DEBUG=True` locally you still see Django's yellow
debug pages; preview the real ones at `/_dev/errors/<400|403|404|500|csrf>/` (linked from `/styleguide/`).

## Run against PostgreSQL on your own machine (Pop!_OS 24.04)

Do this before the first deploy: SQLite is lenient, PostgreSQL is not, so a full test run on PostgreSQL is the real check.

```bash
# 1. Install and start (Pop!_OS 24.04 ships PostgreSQL 16; the service starts by itself)
sudo apt update
sudo apt install postgresql postgresql-contrib
systemctl is-active postgresql                     # -> active

# 2. Create a user and a database. CREATEDB lets the test runner create its own test database.
sudo -u postgres psql <<'SQL'
CREATE ROLE shipmark WITH LOGIN PASSWORD 'local-dev-password' CREATEDB;
CREATE DATABASE shipmark_dev OWNER shipmark;
SQL

# 3. Check that the login works over TCP (the app connects this way)
psql "postgres://shipmark:local-dev-password@localhost:5432/shipmark_dev" -c "select version();"

# 4. Point the project at it. psycopg is in requirements/prod.txt only.
cd ~/shipmark && source .venv/bin/activate
pip install -r requirements/prod.txt
echo 'DATABASE_URL=postgres://shipmark:local-dev-password@localhost:5432/shipmark_dev' >> .env

# 5. Migrate and run the whole test suite on PostgreSQL
python manage.py migrate
python manage.py test                              # creates and drops test_shipmark_dev
python manage.py createsuperuser
python manage.py runserver                         # dev settings, now on PostgreSQL
```

Then try the production settings the way the server will run them (two terminals):

```bash
# terminal 1
export DJANGO_SETTINGS_MODULE=config.settings.prod
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
export ADMIN_URL=staff-local/ ALLOWED_HOSTS=localhost
python manage.py check --deploy                    # "no issues"
python manage.py createcachetable
python manage.py collectstatic --noinput
gunicorn config.wsgi -c gunicorn.conf.py

# terminal 2: prod redirects http to https, so pretend to be the proxy
curl -i -H 'X-Forwarded-Proto: https' -H 'Host: localhost' http://127.0.0.1:8000/
```

Expect `200`, and JSON log lines in terminal 1. Plain `curl http://127.0.0.1:8000/` without the header gives `301`.
Uploads in this mode are not served (the proxy does that in production); use `runserver` to click through the site.

Remove everything again: `sudo -u postgres dropdb shipmark_dev && sudo -u postgres dropuser shipmark`, and delete the
`DATABASE_URL` line from `.env` to go back to SQLite.

## Cron jobs

Background work runs as Django management commands from cron (no Celery).
`manage.py` defaults to the dev settings, so every line sets `DJANGO_SETTINGS_MODULE` explicitly.
The commands read `/srv/shipmark/.env` themselves, so cron needs no other variables.
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
These logs are not rotated by themselves: add a small `logrotate` rule for `/var/log/shipmark/*.log`.

Steady needs at least 40 checks in 30 days. With checks every 3–3.25 hours a project gets about
220 a month, so a few missed runs do not matter. If cron stops for more than a few days,
Steady disappears until enough new checks are collected.

Check by hand:

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py check_uptime -v 2   # lists sites that are down
DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py reverify_domains -v 2
```

## Backups

Two things hold data: the **database** and the **media folder** (screenshots). Back up both, daily, and keep a copy
**off the server** (another provider or your own machine); a backup on the same disk dies with it.

One-time setup for the user that runs cron (never put the password on the command line):

```bash
mkdir -p /var/backups/shipmark
printf 'localhost:5432:shipmark:shipmark:THE_DB_PASSWORD\n' > ~/.pgpass && chmod 600 ~/.pgpass
# format: host:port:database:user:password. Use your real database name and user.
```

```cron
# Database: 03:15 every day, custom format (compressed, restorable with pg_restore). Keep 14 days.
# In crontab a % must be written \% or cron cuts the line there.
15 3 * * *  pg_dump -Fc -h localhost -U shipmark shipmark -f /var/backups/shipmark/db-$(date +\%F).dump && find /var/backups/shipmark -name 'db-*.dump' -mtime +14 -delete

# Media: 03:30 every day. Same 14-day rotation.
30 3 * * *  tar -czf /var/backups/shipmark/media-$(date +\%F).tar.gz -C /srv/shipmark media && find /var/backups/shipmark -name 'media-*.tar.gz' -mtime +14 -delete
```

(`&&` means old backups are only deleted after a new one was written. If `MEDIA_ROOT` is elsewhere, change the `-C` path.)
Copy `/var/backups/shipmark/` off the server with `rsync`/`rclone` from another cron line or from your own computer.

**Test a restore** once before launch, then every few months. A backup you never restored is a hope, not a backup:

```bash
createdb -h localhost -U shipmark shipmark_restore            # needs CREATEDB, or use the postgres user
pg_restore -h localhost -U shipmark --no-owner -d shipmark_restore /var/backups/shipmark/db-YYYY-MM-DD.dump
DATABASE_URL=postgres://shipmark:PASSWORD@localhost:5432/shipmark_restore python manage.py shell -c "from accounts.models import User; print(User.objects.count())"
dropdb -h localhost -U shipmark shipmark_restore
```

Privacy note: a deleted account stays in backups until the last backup containing it is rotated out (14 days here).
Say so on the privacy page.

## Rotating SECRET_KEY

What depends on it: sessions, CSRF tokens. Nothing in the database is encrypted with it (verification tokens are random
values stored as they are, GitHub tokens are not stored), so rotating can never make data unreadable.
Worst case: everyone has to sign in with GitHub again.

**Planned rotation (nobody is signed out):**

1. Generate a new key: `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
2. In `.env`: put the **old** key into `SECRET_KEY_FALLBACKS=` and the **new** key into `SECRET_KEY=`.
3. Restart gunicorn. Existing sessions and forms signed with the old key are still accepted.
4. After 2 weeks (sessions live 14 days) delete the `SECRET_KEY_FALLBACKS` line and restart again.

**If the key leaked:** do the same but leave `SECRET_KEY_FALLBACKS` empty. The old key stops working at once,
everyone is signed out, nothing else breaks. Also rotate `GITHUB_CLIENT_SECRET` and the database password if the whole `.env` leaked.

Do not use the same key as in development, and never commit it.

## Pre-launch checklist

Server
- [ ] HTTPS works; the proxy overwrites `X-Forwarded-Proto` and serves `/media/`; upload size limit is set.
- [ ] `check --deploy` prints "no issues"; `pip-audit -r requirements/prod.txt` is clean.
- [ ] `migrate`, `createcachetable`, `collectstatic` ran; `createsuperuser` done; admin opens at the private `ADMIN_URL` and `/admin/` is 404.
- [ ] Full test suite passed once on PostgreSQL (section above).
- [ ] Cron lines installed; each command run once by hand with `-v 2`; `logrotate` rule added.
- [ ] Backups run, one copy is off the server, **a restore was tested**.
- [ ] gunicorn restarts by itself after a crash and a reboot (kill it once and look).
- [ ] Logs are JSON on stdout and show no IP addresses; you know where to read them.
- [ ] `LOG_DIR` is writable by the app user; open a missing page and check that `show_errors --notfound` lists it.

Accounts and secrets
- [ ] GitHub OAuth App uses the production callback URL; a real sign-in works end to end.
- [ ] `.env` is `chmod 600`, owned by the app user; `SECRET_KEY` differs from dev; no secrets in git (`git log -p | grep -i secret`).
- [ ] After a few days on HTTPS: `SECURE_HSTS_SECONDS=31536000`. Do not use hstspreload.org until you are sure.

Content and law
- [ ] `config/branding.py`: real site name, `CONTACT_EMAIL`, `LEGAL_OWNER_NAME`; logo files in `static/brand/` replaced.
- [ ] Privacy, terms and cookies texts reviewed by a lawyer. Update them for: proxy access-log retention (decide it; see
      `docs/DATA_INVENTORY.md`), backup retention, and the rate-limit counters (the text says "memory", prod uses the database cache).
      Bump `TERMS_VERSION` if the Terms change.
- [ ] pl, de, es, fr, pt-br translations reviewed by native speakers, or remove those languages from `LANGUAGES` for now.

By hand, on the live site (phone and desktop)
- [ ] Sign in with GitHub, create a project, **upload a screenshot** (checks the media folder permissions), publish it.
- [ ] Verify a domain, run the repo check, open the badge SVG, like and follow from a second account.
- [ ] Report a project and handle the report in the admin; export your data; delete a test account.
- [ ] Open the browser console on the main pages: no CSP errors.

## Security headers

CSP and Permissions-Policy are added by `config/middleware.py`; the policy is `CONTENT_SECURITY_POLICY` in
`config/settings/base.py`. Pages must not use inline `<script>`, `<style>`, `style="..."` or `onclick="..."` (a test checks this).
The admin is excluded from the CSP because django-unfold needs inline code.

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
| `BAN_HASH_KEY` | yes | Key for the ban-evasion hash. `python -c "import secrets; print(secrets.token_urlsafe(50))"`, at least 32 characters, not the `SECRET_KEY`. **Never rotate it while a ban is active** (see "BAN_HASH_KEY" below) |
| `DATABASE_URL` | yes | `postgres://USER:PASSWORD@HOST:5432/DBNAME` (percent-encode special characters in the password) |
| `ALLOWED_HOSTS` | yes | Comma-separated host names, e.g. `example.com,www.example.com` |
| `CSRF_TRUSTED_ORIGINS` | yes | With scheme, e.g. `https://example.com` |
| `SITE_URL` | no | Public address used in embed snippets, Open Graph, canonical links and the data export. Default `https://shipmark.me` (from `SITE_DOMAIN`); must be https. Dev default `http://localhost:8000` |
| `ADMIN_URL` | yes | Private admin address, e.g. `staff-4f8k2/`. `admin/` is refused at startup |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | yes | OAuth App. Callback URL: `https://YOUR.DOMAIN/accounts/github/login/callback/` |
| `GITHUB_API_TOKEN` | **yes** (for `reverify_repos`) | Fine-grained or classic token with **no scopes** (public data only). Lifts GitHub's limit from 60 to 5000 requests/hour. One repo check costs up to ~10 requests, so without it the weekly re-check of repositories stops at the limit after a handful of repos (nothing breaks: it continues next run) |
| `MEDIA_ROOT` | no | Folder for uploads. Default `<project>/media` |
| `SUPPORT_INBOX_EMAIL` | no | Where the notice about each support message goes. Empty: no email, messages wait in the admin inbox |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | with `SUPPORT_INBOX_EMAIL` | SMTP for that notice (Gmail: see "Support inbox"). Prod uses the SMTP backend; dev prints emails in the terminal |
| `SUPPORT_ROOT` | no | Private folder for support attachments, **outside** `MEDIA_ROOT`, never served. Default `<project>/private/support` |
| `CLIENT_IP_HEADER` | recommended | `HTTP_X_REAL_IP` when nginx sets `proxy_set_header X-Real-IP $remote_addr;`. Without it every visitor looks like the proxy and shares one support rate limit |
| `COMMUNITY_ENABLED` | no | `true` switches the community on (`/community/`, the header link). Default **false** in prod: every community route is 404. See "Community: switching it on" |
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
- The proxy serves `/media/` from `MEDIA_ROOT` and allows request bodies a bit above 20 MB: the project form
  uploads up to 4 screenshots of 5 MB each with one Save (nginx: `client_max_body_size 25m;`). See "Serving media".
- The user running gunicorn can write to `MEDIA_ROOT`. Static files need nothing from the proxy: WhiteNoise serves them
  (hashed names, gzip/brotli, far-future cache) from `staticfiles/`, so run `collectstatic` before every restart.
- Static files: if `collectstatic` or a page fails with "Missing staticfiles manifest entry", a template points to a
  file that does not exist in `static/`. Fix the reference; do not work around it.

### Serving media (screenshots, avatars, covers)

Django serves uploads only when `DEBUG` is on (`config/urls.py`, development). With `DEBUG` off it does not serve
`/media/` at all, so without a proxy rule every screenshot is a broken image while the rows exist in the database.
The web server in front of gunicorn must map `MEDIA_URL` (`/media/`) to `MEDIA_ROOT`, for example in nginx:

```nginx
location /media/ {
    alias /srv/shipmark/media/;      # MEDIA_ROOT, with the trailing slash
    add_header X-Content-Type-Options nosniff;
    expires 30d;                      # file names are random and never reused
}
```

Files are always re-encoded WebP with random names (`screenshots/`, `avatars/`, `covers/` + 32 hex + `.webp`), never the user's bytes or name, so
the folder holds no executable content. Do not enable directory listing. Check after deploy: upload a screenshot, open
the project page, the image loads (status 200, `Content-Type: image/webp`). Backups: see "Backups" (the media folder is
backed up daily together with the database; restore both from the same day).

**Thumbnails (once after this release):** `python manage.py make_thumbs`. New screenshots get a small copy
(`screenshots/thumbs/<32 hex>.webp`, max 640 px) when they are saved; this command builds it for the ones saved before.
Safe to repeat; a file it cannot read is reported and skipped (the list then shows the full image). Lists, the feed and
profile rows read the thumbnail, the project page reads the full image; both are in `MEDIA_ROOT` and in the media backup.

### Uploads and later S3-compatible storage

All uploads are stored on the server's disk in `MEDIA_ROOT`: `screenshots/` (+ `screenshots/thumbs/`), `avatars/`
(profile pictures, 512×512), `covers/` (profile covers, 1500×500) and `community/<year>/<month>/` (community pictures,
up to 1600 px, thumbnails of 640 px in `t/` next to them). This is fine for one server, but the folder is part
of the data: back it up (below), and it does not follow you if the app runs on more than one machine.

- What goes in: only re-encoded WebP files with random names, made by one Pillow pipeline (`projects/images.py`).
  "Use my GitHub picture" downloads the picture **once** through `safe_fetch`, only from `avatars.githubusercontent.com`,
  so the server needs outbound HTTPS to that host (and to `api.github.com` for the repo check). Pages never hotlink GitHub.
- What goes out: a file is deleted from disk (through the storage API) when the person replaces or removes it, when a
  moderator clears the picture and cover, when a screenshot or project is deleted, and when the account is deleted.
  After that the only copies are in the backups, for up to 14 days (the privacy page says so).
- Community pictures leave the disk when the author deletes the post, when a moderator removes it (at once, the text
  is kept for appeals) and when the uploader deletes the account.
- Limits: 5 MB per upload, 20 profile-picture or cover uploads and 5 GitHub downloads per person per hour; community:
  10 pictures per person per hour, 4 per thread, 2 per reply, none in the first 24 hours of an account.
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
export BAN_HASH_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
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

# Repository re-verification (Repo owner): once a day. Each link is re-checked when its last check is
# 7 days old (TRUST_REVERIFY_REPOS_DAYS), plus links waiting for a re-check or for GitHub statistics.
# Needs GITHUB_API_TOKEN. A rate limit ends the run early; the rest is done the next day.
45 4 * * *    cd /srv/shipmark && flock -n /tmp/shipmark-repos.lock .venv/bin/python manage.py reverify_repos >> /var/log/shipmark/repos.log 2>&1

# Ban hashes (ban evasion): once a day. Deletes the salted GitHub-id hashes of bans that have ended.
# Bans themselves need no cron: expiry is checked per request.
15 4 * * *    cd /srv/shipmark && .venv/bin/python manage.py prune_bans >> /var/log/shipmark/bans.log 2>&1

# Support: once a day. Deletes closed support messages older than 12 months, with their attachment files.
30 5 * * *    cd /srv/shipmark && .venv/bin/python manage.py prune_support >> /var/log/shipmark/support.log 2>&1

# Community: once a day. Recounts scores and reply counts (votes of suspended or banned accounts stop counting)
# and deletes reply notifications older than 90 days (the privacy page promises it). Safe with the flag off.
0 5 * * *     cd /srv/shipmark && flock -n /tmp/shipmark-community.lock .venv/bin/python manage.py community_daily >> /var/log/shipmark/community.log 2>&1
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
DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py reverify_repos -v 2      # lists removed / review
```

## Trust hardening: one-time steps after deploying it

The trust-hardening migrations only add fields. Links that earned Repo owner by commit count alone
(a rule that no longer exists) become "needs re-check": the mark is withheld with a neutral message and
each one is logged in AuditLog. Nothing is deleted by the migration.

1. Set `GITHUB_API_TOKEN` (see the table above).
2. Try it on a copy first: restore last night's `pg_dump` into a scratch database and point
   `DATABASE_URL` at it for the next two commands. Locally: `cp db.sqlite3 /tmp/copy.sqlite3` and
   `DATABASE_URL=sqlite:////tmp/copy.sqlite3`.
3. `python manage.py migrate`
4. `python manage.py backfill_repo_facts --dry-run`, read the output, then without `--dry-run`.
   It fills owner ids, repository dates, first commits and active weeks. It never removes a mark:
   review facts -> "needs review", a repository that changed on GitHub -> "needs re-check". A rate limit
   stops it; run it again, it continues where it stopped.
5. `python manage.py reverify_repos --all -v 2`: decides every "needs re-check" link with the current
   rules (removed marks are logged).
6. Admin -> Verification -> Review queue: approve, revoke or block what is waiting.

When the copy looks right, run steps 3-5 on production (with `DJANGO_SETTINGS_MODULE=config.settings.prod`).
To re-check everything later (for example after changing a threshold in `config/settings/base.py`):
`python manage.py reverify_repos --all`.

## Backups

Two things hold data: the **database** and the **media folder** (screenshots and their thumbnails, profile pictures,
covers). Back up both, daily, and keep a copy **off the server** (another provider or your own machine); a backup on
the same disk dies with it. Restore both from the **same day**: an older media folder with a newer database shows
broken images (rows point to files that are missing); a newer media folder with an older database only leaves unused
files on disk.

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

# Support attachments (private folder, SUPPORT_ROOT): 03:40, same 14 days. Keep these archives as private as the database.
40 3 * * *  tar -czf /var/backups/shipmark/support-$(date +\%F).tar.gz -C /srv/shipmark private && find /var/backups/shipmark -name 'support-*.tar.gz' -mtime +14 -delete
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
Worst case: everyone has to sign in with GitHub again. The ban hashes do **not** use it any more (see "BAN_HASH_KEY"),
except old ones that `rehash_bans` could not convert (see below).

**Planned rotation (nobody is signed out):**

1. Generate a new key: `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
2. In `.env`: put the **old** key into `SECRET_KEY_FALLBACKS=` and the **new** key into `SECRET_KEY=`.
3. Restart gunicorn. Existing sessions and forms signed with the old key are still accepted.
4. After 2 weeks (sessions live 14 days) delete the `SECRET_KEY_FALLBACKS` line and restart again.

**If the key leaked:** do the same but leave `SECRET_KEY_FALLBACKS` empty. The old key stops working at once,
everyone is signed out, nothing else breaks. Also rotate `GITHUB_CLIENT_SECRET` and the database password if the whole `.env` leaked.

Do not use the same key as in development, and never commit it.

## BAN_HASH_KEY

When someone is banned we keep `HMAC-SHA256(BAN_HASH_KEY, "shipmark.moderation.banned-identity:github:<GitHub id>")`
(`moderation/bans.py`), never the id, so deleting the account and signing up again with the same GitHub account still
shows the ban page. The label is only a prefix that keeps this HMAC apart from any other; the secret is the key.
It is separate from `SECRET_KEY` on purpose: rotating `SECRET_KEY` (routine) must not free banned people.

- **Generate it once:** `python -c "import secrets; print(secrets.token_urlsafe(50))"`, put it in `.env` (chmod 600).
  Production refuses to start if it is missing, shorter than 32 characters, or equal to `SECRET_KEY`.
  Dev uses an insecure built-in default.
- **Never rotate it while any ban is active, permanent ones included.** The hashes cannot be recomputed with a new key
  (the GitHub ids are not stored), so after a rotation every hash made with the old key stops matching and every
  banned person can sign up again. If you must rotate: do it when `Moderation > Banned identities` is empty (bans end
  and are pruned daily), or accept that those bans lapse.
- **Keep it secret like a password.** GitHub ids are small numbers, so anyone who has the key and the hashes could test
  which ids are banned. Without the key the hashes tell nothing.
- **Backups:** the key lives in `.env`, not in the database, so a database backup alone does not contain it. Keep a copy
  of `.env` where your other secrets are, or a restored database cannot match its ban hashes.

**First deploy of this version:** `python manage.py rehash_bans` once (safe to repeat). It converts ban hashes made
before `BAN_HASH_KEY` existed (they were keyed from `SECRET_KEY`) for every ban whose account still exists. A ban whose
account was deleted cannot be converted (nothing to compute the new hash from); the command says how many there are,
and they keep matching through `SECRET_KEY` / `SECRET_KEY_FALLBACKS` until they expire, so do not rotate `SECRET_KEY`
without a fallback before then. When the command reports "No old-scheme hashes left", `SECRET_KEY` has nothing to do
with bans any more. **Do not roll the migration back after `rehash_bans`:** converted rows only match with this code.

## Support inbox (форма підтримки і пошта)

Повідомлення з `/support/` завжди зберігаються в адмінці (розділ Support → Inbox). Лист на пошту — лише
сповіщення «прийшло нове повідомлення» (простий текст, без вкладень). Якщо пошта не налаштована або не працює,
повідомлення все одно зберігається.

**Хто бачить інбокс.** Суперкористувач і персонал (`is_staff`), якому в адмінці дали дозволи
`support | support message | Can view` (читати й завантажувати вкладення) і `Can change` (статус, нотатки).
Іншим працівникам розділ не показується, а посилання на вкладення дає 404.

**Вкладення лежать приватно.** Папка `SUPPORT_ROOT` (типово `/srv/shipmark/private/support`) — поза `MEDIA_ROOT`,
nginx її **не** роздає (не додавай для неї `location`). Права: власник — користувач, від якого працює gunicorn,
`chmod 700`. Резервна копія — окремим рядком cron (розділ Backups). Перенесення в S3: у `config/settings/prod.py`
зміни лише `STORAGES["support"]` на приватний бакет або префікс (`default_acl: private`), потрібен `django-storages`
(його немає в дозволеному списку, спершу погодь).

**IP для ліміту.** У nginx: `proxy_set_header X-Real-IP $remote_addr;` і в `.env`: `CLIENT_IP_HEADER=HTTP_X_REAL_IP`.
Адреса не зберігається: з неї рахується солений хеш, який живе в кеші до 24 годин.

### Gmail як скринька підтримки (покроково)

1. Заведи окремий акаунт Gmail для сайту (наприклад, `shipmark.support@gmail.com`), щоб не давати серверу пароль
   від особистої пошти.
2. Увімкни **двоетапну перевірку**: myaccount.google.com → «Безпека» → «Двоетапна перевірка». Без неї паролі
   застосунків недоступні.
3. Створи **пароль застосунку**: myaccount.google.com → пошук «Паролі застосунків» (App passwords) → назва,
   наприклад, `shipmark server` → «Створити». Google покаже 16 літер (`abcd efgh ijkl mnop`). Скопіюй їх без
   пробілів. Цей пароль працює лише для пошти і його можна відкликати там само, не змінюючи основний пароль.
4. Заповни `/srv/shipmark/.env`:

   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=true
   EMAIL_HOST_USER=shipmark.support@gmail.com
   EMAIL_HOST_PASSWORD=abcdefghijklmnop
   DEFAULT_FROM_EMAIL=Shipmark <shipmark.support@gmail.com>
   SUPPORT_INBOX_EMAIL=shipmark.support@gmail.com
   ```

   `SUPPORT_INBOX_EMAIL` може бути й іншою адресою (твоя особиста пошта): тоді лист прийде туди, а відправником
   буде акаунт із кроку 1. Gmail підставляє в «Від» свій акаунт, тому `DEFAULT_FROM_EMAIL` має бути тією ж адресою.
5. Перезапусти gunicorn і перевір: `python manage.py sendtestemail SUPPORT_INBOX_EMAIL_тут` (з
   `DJANGO_SETTINGS_MODULE=config.settings.prod`). Потім надішли повідомлення через `/support/` з іншого браузера.
6. Відповідати просто: у листі-сповіщенні натисни «Відповісти» (Reply-To — адреса людини) або в адмінці «Reply by
   email». Після відповіді постав статус «Answered», коли тема вичерпана — «Closed».

Якщо лист не прийшов: дивись `show_errors` (рядок `support notification failed ... SMTPAuthenticationError` означає
неправильний пароль застосунку або вимкнену двоетапну перевірку). Gmail обмежує ~500 листів на добу, для сповіщень
цього вистачає. Пароль застосунку лежить лише в `.env` (`chmod 600`) і в копії секретів.

## Community: switching it on

The community ships switched off (`COMMUNITY_ENABLED` unset = false): no link, every `/community/` route is 404, and
no community code runs on a request. Export and account deletion handle community rows either way.

1. Back up the database and the media folder (section "Backups"); community pictures go into the same media backup,
   under `MEDIA_ROOT/community/`, so nothing new is needed there.
2. Make sure at least one person besides you has the moderator badge (`manage.py grant_badge`): there is no
   pre-moderation, so reports need someone to answer them (risk 1 in `docs/COMMUNITY_PLAN.md`).
3. Add the `community_daily` cron line (section "Cron jobs") and run it once by hand.
4. Post the pinned welcome thread from the official account: `manage.py post_welcome` (once; `--board <slug>` to choose
   the board, `--force` for a new one). It works with the flag still off, so you can check it in the admin first.
5. Set `COMMUNITY_ENABLED=true` in `.env` and restart gunicorn. Open `/community/`, post a thread with a picture from a
   second account, reply with a sticker, report it and handle the report in `/mod/`.
6. The proxy's upload limit (`client_max_body_size 25m`) already covers a thread with 4 pictures of 5 MB.
7. The Terms changed for the community (`TERMS_VERSION` 2026-11-13): signed-in people accept them again on their next
   visit. The texts are drafts: have the community parts of Terms and Privacy reviewed with the rest.

To switch it off again, unset the variable and restart: posts stay in the database and come back when it is on.
`seed_community` (demo content) refuses to run without `DEBUG`; never copy a development database with demo
accounts (`demo-*`) to production.

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
- [ ] `.env` is `chmod 600`, owned by the app user; `SECRET_KEY` and `BAN_HASH_KEY` differ from dev (and from each other), and `.env` is backed up with your other secrets; no secrets in git (`git log -p | grep -i secret`).
- [ ] After a few days on HTTPS: `SECURE_HSTS_SECONDS=31536000`. Do not use hstspreload.org until you are sure.

Content and law
- [ ] `config/branding.py`: real site name, `CONTACT_EMAIL`, `LEGAL_OWNER_NAME`; logo files in `static/brand/` replaced.
- [ ] Privacy, terms and cookies texts reviewed by a lawyer. Update them for: proxy access-log retention (decide it; see
      `docs/DATA_INVENTORY.md`) and backup retention. The texts were updated on 2026-11-12 (profile data, pictures,
      moderator access, appeals, language cookie) without bumping `TERMS_VERSION`, because the site is not public yet.
      After launch, bump `TERMS_VERSION` whenever the Terms change.
- [ ] pl, de, es, fr, pt-br translations reviewed by native speakers, or remove those languages from `LANGUAGES` for now.
- [ ] Support: `SUPPORT_INBOX_EMAIL` and SMTP set, `sendtestemail` arrives, a test message with an attachment shows in
      the admin inbox and its attachment downloads; `/support/attachment/<id>/` is 404 when signed out; `SUPPORT_ROOT`
      is outside `MEDIA_ROOT` and not served by nginx; `CLIENT_IP_HEADER` set; `prune_support` in cron.
- [ ] Community (only if it launches): the steps in "Community: switching it on"; rules, Terms and Privacy community
      parts reviewed; a second moderator exists.

By hand, on the live site (phone and desktop)
- [ ] Sign in with GitHub, create a project, **upload a screenshot** (checks the media folder permissions), publish it.
- [ ] Verify a domain, run the repo check, open the badge SVG, like and follow from a second account.
- [ ] Report a project and handle the report in the admin; export your data; delete a test account.
- [ ] Open the browser console on the main pages: no CSP errors.

## Security headers

CSP and Permissions-Policy are added by `config/middleware.py`; the policy is `CONTENT_SECURITY_POLICY` in
`config/settings/base.py`. Pages must not use inline `<script>`, `<style>`, `style="..."` or `onclick="..."` (a test checks this).
The admin is excluded from the CSP because django-unfold needs inline code.

# Shipmark

Public place where people who build with AI show work they actually shipped, with verified proof.
(Working name; it lives only in `config/branding.py`.)

See `CLAUDE.md` for the product, rules and conventions.

## Setup (Linux)

Needs Python 3.12+ and git.

```bash
git clone <repo-url> shipmark && cd shipmark
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Always open **http://localhost:8000/**, not 127.0.0.1. GitHub sign-in works only there (the OAuth
app's callback is a localhost URL), and a browser keeps cache, theme and cookies per address, so the
two can look different. In development `127.0.0.1` is redirected to `localhost` automatically, and
static files are sent with `Cache-Control: no-cache`, so CSS and JS edits show on a normal reload.

## Everyday commands

```bash
source .venv/bin/activate
python manage.py check
python manage.py test               # all tests
python manage.py test pages         # one app
python manage.py makemigrations && python manage.py migrate
```

## Settings

- `config.settings.dev` is the default for `manage.py` (SQLite, DEBUG on, insecure dev key).
- `config.settings.prod` is the default for `wsgi.py`/`asgi.py`. It requires `SECRET_KEY`,
  `BAN_HASH_KEY` and `DATABASE_URL` (PostgreSQL) and fails at startup if they are missing.
- All variables are documented in `.env.example`.

## Production dependencies

```bash
pip install -r requirements/prod.txt
python manage.py collectstatic --noinput
gunicorn config.wsgi
```

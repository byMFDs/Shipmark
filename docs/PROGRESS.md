# Progress log

- 2026-11-10: Task 1 done. Django 5.2 project (`config` with base/dev/prod settings), six app stubs, custom `accounts.User` with migration, `config/branding.py` + `brand` context processor, `base.html`, landing at `/`, requirements, README, tests. Next: design foundation (tokens/base CSS, fonts) or GitHub sign-in.
- 2026-11-10: Task 2 done. docs/DESIGN.md; self-hosted Plex fonts (+ size-adjusted fallbacks); tokens/base/components CSS; light/dark with no-flash toggle (theme.js); menu.js, toast.js; logo, mark, favicon, apple-touch-icon, OG image; {% load ui %} tags (inline_svg, icon, avatar, hallmark, site_header, site_footer); /styleguide/ (DEBUG only).
  Dark ink chosen: #8EA8F1 (same hue as the light ink). Next: landing hero (specimen plate) or GitHub sign-in.
- 2026-11-10: Task 3 done. i18n (en, uk): `UserLocaleMiddleware` (saved preference > cookie > Accept-Language > en), POST `set_language` at `/i18n/set-language/` (also saves choice on the account), footer switcher, uk translations compiled. `pages/content.py` loads `content/<lang>/<slug>.md` (fallback en, markdown + nh3), `/about/` placeholders, `docs/EDITING.md`, tests.
  Styleguide (DEBUG only) is not translated on purpose. Next: GitHub sign-in (Task 4).
- 2026-11-10: Task 4 done. GitHub-only sign-in (allauth, scopes read:user + user:email, no email/password routes), `/login/`, `/logout/` (POST), `/signup/` confirm step (username + Terms, saves version/time), `/settings/`, header avatar menu, username rules (lowercase, reserved list, `-2` suffix), `config/ratelimit.py`, uk translations, 32 tests.
  Avatars are NOT shown yet (initials only): `avatar_url` holds GitHub's URL, never hotlinked. Next: Task 5 (projects) or the safe_fetch task, which also unlocks avatar download.

## Next

- Avatars: download GitHub avatars and store them locally (needs `safe_fetch` + Pillow re-encode), then pass `src` to `{% avatar %}`.
- On every login refresh `github_login` (GitHub users can rename), needed before the Authored check.
- Prod: configure a shared cache (DB or Redis-free file cache) so `config/ratelimit.py` works across gunicorn workers.
- Task 3: add latin-ext font subset when Polish is added (later, not now).
- Task 4: move the inline theme script to a hashed or external file before enabling CSP.

# Progress log

- 2026-11-10: Task 1 done. Django 5.2 project (`config` with base/dev/prod settings), six app stubs, custom `accounts.User` with migration, `config/branding.py` + `brand` context processor, `base.html`, landing at `/`, requirements, README, tests. Next: design foundation (tokens/base CSS, fonts) or GitHub sign-in.
- 2026-11-10: Task 2 done. docs/DESIGN.md; self-hosted Plex fonts (+ size-adjusted fallbacks); tokens/base/components CSS; light/dark with no-flash toggle (theme.js); menu.js, toast.js; logo, mark, favicon, apple-touch-icon, OG image; {% load ui %} tags (inline_svg, icon, avatar, hallmark, site_header, site_footer); /styleguide/ (DEBUG only).
  Dark ink chosen: #8EA8F1 (same hue as the light ink). Next: landing hero (specimen plate) or GitHub sign-in.
- 2026-11-10: Task 3 done. i18n (en, uk): `UserLocaleMiddleware` (saved preference > cookie > Accept-Language > en), POST `set_language` at `/i18n/set-language/` (also saves choice on the account), footer switcher, uk translations compiled. `pages/content.py` loads `content/<lang>/<slug>.md` (fallback en, markdown + nh3), `/about/` placeholders, `docs/EDITING.md`, tests.
  Styleguide (DEBUG only) is not translated on purpose. Next: GitHub sign-in (Task 4).

## Next

- Task 4: download GitHub avatars on first login and store them locally, do not hotlink.
- Task 3: add latin-ext font subset when Polish is added (later, not now).
- Task 4: move the inline theme script to a hashed or external file before enabling CSP.

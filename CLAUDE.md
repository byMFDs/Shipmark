# Shipmark: project memory for Claude Code

Working name: **Shipmark** (may change; it lives only in `config/branding.py`).
This file is loaded every session. Keep it accurate; keep it short.

---

## 0. How to work with the developer

- Developer: Danylo, 18. Knows basic Django, HTML, CSS, Git; learning JavaScript.
  He reviews logic and security himself, so explain non-obvious decisions in 1-2 sentences.
- **Reply in Ukrainian, briefly.** Code, comments, commit messages, identifiers: English.
- **Do not paste whole files back.** Summarize: which files changed and why.
- One task = one prompt. Do only what the prompt asks. If you notice something else
  that should be done, list it under "Пропозиції" at the end. Do not do it.
- Make reasonable decisions on your own and state them. Ask only when truly blocked.
- New dependency not listed in section 3: ask first.
- Do not run `runserver` (it blocks). The developer runs it himself.
- **Finish every task with:**
  1. `python manage.py check` and the relevant tests (`python manage.py test <app>`).
  2. Append ≤5 lines to `docs/PROGRESS.md` (date, what was done, what is next).
  3. A short list "Що перевірити вручну" (what to click and what should happen).
  4. A suggested commit message. Do not commit yourself unless asked.

---

## 1. Product

Shipmark is a public place where people who build with AI (vibecoders, indie hackers)
show work they actually shipped, with **verified proof** instead of claims.
GitHub shows code, LinkedIn shows claims; Shipmark shows verified outcomes.

- The core unit is a **Project**, not a profile. A profile is a collection of projects.
- Each project earns **hallmarks** (proof marks), like an assay office stamps metal.
- Audience for MVP: people building products with AI tools. English-first, global.
- Growth comes from inside the product: embeddable badges, profile links in bios,
  a feed of launches people return to.

### MVP: in scope
GitHub sign-in · profiles · projects (create/edit/publish) · repo authorship check ·
domain verification (DNS TXT or meta tag) · uptime checks · hallmarks · build log ·
follow + like · feed · explore/search · SVG badges · reports + moderation ·
beautiful admin · legal pages · account deletion + data export · i18n (en, uk, later more) ·
support form + admin inbox (`support/`) · public "people joined" count in the header.

### Community (`community/`, branch `community-1`, behind `COMMUNITY_ENABLED`)
A small forum inside Shipmark: boards, threads, replies (depth max 3), upvotes only (no downvotes,
none on your own post), own sticker set, images through the one image pipeline, in-app reply
notifications (no email). Moderation is the existing system (/mod/, Report, Sanction, Notice, AuditLog).
Flag off (production default): every community route is 404, no link, no code path runs; export and
account deletion still cover existing rows. Plan, rules and numbers: `docs/COMMUNITY_PLAN.md`,
progress: `docs/COMMUNITY_STATUS.md`. Terms/Privacy cover it (`TERMS_VERSION` 2026-11-13); switch-on steps in
`docs/DEPLOY_NOTES.md`. Rules page: `content/<lang>/community-rules.md`. Pages share `templates/community/_layout.html`.

### MVP: out of scope (do not build)
Payments, subscriptions, messaging/DMs, comments on projects (discussion lives in Community), company/investor accounts,
notifications by email (the only email is the support notice to the team inbox), revenue/analytics integrations, native apps, AI features,
Celery/Redis, Docker (unless asked), any social login except GitHub.

---

## 2. Hallmarks (proof rules)

Computed by one pure function `projects/proof.py::compute_hallmarks(project)`.
Never store the level as truth; derive it from facts. Cache if needed.

| Hallmark | Earned when |
|---|---|
| **Repo owner** (id `authored`; never claim code authorship) | Linked public GitHub repo is owned by the user's GitHub account, OR user has ≥10 commits in it |
| **Live** (shown as "Domain verified"; id `live`) | User proved control of the project domain (DNS TXT or meta tag), re-confirmed in the last 35 days |
| **Steady** | Has Live AND ≥95% successful uptime checks over the last 30 days, with ≥40 checks |
| *(Used)* | Post-MVP. Do not build. Show nothing for it. |

Anti-gaming:
- A domain can be verified for only one project at a time. A repo can link to only one project.
- Verification tokens are random, per project+domain, never reused.
- If re-verification fails, the hallmark is removed and the change is logged.
- "Built with" AI tools are **self-declared** and must be labeled as such in the UI.

---

## 3. Stack and conventions

- Python 3.12+, **Django 5.2 LTS**.
- Server-rendered Django templates. **Vanilla JavaScript (ES modules, no build step,
  no frameworks)** only where the page must update without reload (likes, follows,
  copy buttons, theme toggle, verification status, language switch).
  JS calls Django views that return JSON. Everything important must also work
  without JS where reasonable (plain POST fallback).
- **CSS: hand-written. No Bootstrap, no Tailwind, no CSS frameworks.**
  Files: `static/css/tokens.css`, `base.css`, `components.css`, `pages/*.css`.
- DB: **SQLite in development, PostgreSQL in production** via `DATABASE_URL`.
  Write code that works on both. No DB-specific features without a fallback.
- Background work: Django management commands run by cron. No Celery.
- Tests: Django test runner. Test permissions, proof rules, verification, SSRF guard,
  i18n detection. Do not write tests for trivial template views.

Allowed dependencies: `django`, `django-environ`, `django-allauth`, `django-unfold`,
`Pillow`, `markdown`, `nh3`, `dnspython`, `httpx`, `whitenoise`;
prod only: `gunicorn`, `psycopg[binary]`. Dev only: `pip-audit`.

---

## 4. Structure

```
config/            settings/{base,dev,prod}.py, urls.py, branding.py
accounts/          custom User (AbstractUser), profiles, badges + roles.py, settings, data export, deletion
projects/          Project, Tag, Screenshot, BuildLogEntry, proof.py, images.py (the one image pipeline)
verification/      net.py (safe_fetch), repo.py, domain.py, uptime.py, commands
social/            Follow, Like, feed + ranking.py
pages/             landing, explore, legal and content pages, styleguide (DEBUG only)
moderation/        Report, Sanction, Notice, BannedIdentity, AuditLog, /mod/, decisions, admin actions
news/              NewsPost (written in the admin only, published as the system account "shipmark")
community/         Board, Thread, Reply, CommunityImage, Vote, ReplyNotification, stickers.py, ranking.py, services.py
support/           SupportMessage, SupportAttachment (private storage), antispam.py, notify.py (SMTP notice), admin inbox
templates/  static/{css,js,fonts,brand,img}/  content/<lang>/*.md  locale/  docs/
```

URLs: `/` landing · `/feed/` (shown as "For You") · `/explore/` ("Discover": projects, `?tab=people` people search by username) · `/new/` · `/settings/` ·
`/u/<username>/` · `/u/<username>/<project-slug>/` · `/badge/<username>.svg` ·
`/badge/<username>/<project-slug>.svg` · `/legal/<slug>/` · `/how-proof-works/` · `/news/` · `/support/` · `/community/` (`b/<slug>/`, `t/<id>-<slug>/`, `new/`, `rules/`) ·
`/mod/` (moderator badge or superuser) · admin at `ADMIN_URL` from env (never `/admin/` in production).

Reserved usernames: admin, api, static, media, badge, legal, settings, new, feed,
explore, login, logout, signup, u, p, help, about, support, root, system, shipmark, official,
moderator, mod, team, staff, news.

---

## 5. Data model (MVP)

- **User**: username, display_name, headline (≤80), about (markdown ≤1000), location, status, skills (M2M Tag ≤10),
  avatar, avatar_source, cover, github_login, avatar_url (never shown), preferred_language, terms_version_accepted,
  terms_accepted_at, is_suspended. `bio` and `website` are deprecated (not editable, to be dropped).
  **ProfileLink** (≤6), **PinnedProject** (≤3), **UserBadge** (official / moderator; `can_moderate` comes from it).
- **Project**: owner, name, slug (unique per owner), tagline (≤120),
  description (markdown), live_url, repo_full_name, tags (M2M Tag),
  built_with (M2M Tool, self-declared), status (draft/published/hidden/removed),
  launched_at, created_at, updated_at.
- **Screenshot**: project, image, order (max 4 per project).
- **RepoLink**: project (1:1), repo_full_name (unique), is_owner, user_commit_count,
  first_commit_at, last_commit_at, checked_at.
- **DomainVerification**: project, domain (unique while verified), method (dns/meta),
  token, status, verified_at, last_confirmed_at.
- **UptimeCheck**: project, checked_at, ok, status_code, response_ms. Keep 90 days.
- **BuildLogEntry**: project, text (≤500, limited markdown), kind (update/launch), created_at.
- **Follow**: follower, following (unique pair). **Like**: user, project (unique pair).
- **Report**: reporter, target (project, user or build-log entry), reason, details, status
  (open/in review/resolved/dismissed), resolution note, handled_by. **Sanction** (mute/ban, reason, start, end),
  **Notice** (what the person is told), **BannedIdentity** (HMAC of a banned GitHub id). **NewsPost**.
- **AuditLog**: actor, action, target, metadata JSON, created_at
  (hallmark changes, moderation actions, account deletion).

Always use `select_related`/`prefetch_related` on lists. No N+1 queries.

---

## 6. Security rules (non-negotiable)

- Every write view checks object ownership. Others' drafts and hidden items return **404**.
- CSRF on every POST, including `fetch` (send `X-CSRFToken`).
- **Any server-side request to a user-supplied URL goes through
  `verification/net.py::safe_fetch` only.** It must: allow only http/https and ports 80/443;
  resolve DNS and block private, loopback, link-local, reserved, multicast, CGNAT
  (IPv4 and IPv6); re-validate every redirect (max 3); timeout 5s; max body 512 KB;
  fixed User-Agent. Never call `httpx` directly anywhere else.
- User markdown is rendered then sanitized with `nh3` (allowlist). No raw HTML.
  External links get `rel="nofollow ugc noopener"`.
- Uploads: images only, verified with Pillow, re-encoded (strips metadata),
  max 5 MB, random filenames.
- GitHub OAuth scopes: `read:user` and `user:email` only. Never request `repo`.
- Rate-limit writes, likes, follows, reports, verification attempts (cache-based).
- Secrets only from env. `.env` is gitignored. `.env.example` documents every variable.
- Never show a user's email publicly. No third-party trackers. Self-hosted fonts only.
- Support attachments live in `STORAGES["support"]` (outside MEDIA_ROOT, no URL); only the staff view serves them.
  No IP or user agent is stored anywhere; the support rate limit uses a salted IP hash in the cache only.
- Suspended users cannot write; their projects are hidden.

---

## 7. Branding and editable content (the developer edits these himself)

- **`config/branding.py` is the single source** for: SITE_NAME, TAGLINE (gettext_lazy),
  CONTACT_EMAIL, LEGAL_OWNER_NAME, SOCIAL_LINKS, logo file paths.
  Exposed to templates by a context processor as `brand`. Never hard-code the name elsewhere.
- Logo files: `static/brand/logo.svg`, `logo-mark.svg`, `favicon.svg`,
  `apple-touch-icon.png`, `og-default.png`. Replacing a file must be enough to rebrand.
- UI text: English source in templates (`{% translate %}`) and Python (`gettext`).
  Translations live in `locale/<lang>/LC_MESSAGES/django.po`.
- Long text (legal, about, FAQ, how proof works): `content/<lang>/<slug>.md`,
  falling back to `content/en/`. Editing the .md file changes the page.
- `docs/EDITING.md` explains all of the above in Ukrainian, in plain words.

---

## 8. Languages

- Detection order: user's saved preference → language cookie → browser
  `Accept-Language` → English. **No IP geolocation** (VPNs, travelers, multilingual
  countries make it wrong; browser language is what the person chose).
- MVP: `en` (default), `uk`. Later: `pl`, `de`, `es`, `fr`, `pt-br`.
  **Never add Russian.**
- No language prefixes in URLs. Switcher in the footer and the account menu.
- The language cookie follows the saved preference (written at sign-in and when it differs), so pages and the
  "signed in / signed out" notices stay in one language, also after signing out.
- User-generated content is never auto-translated.

---

## 9. Design direction

Concept: **a public record of shipped work.** Each project is a framed record; proof is a flat mark on it.
Warm paper, 1px hairline frames, square corners, one action color. Restrained and precise, not playful.
Full rules and measured contrast: `docs/DESIGN.md`; values: `static/css/tokens.css` (light / dark).

Palette (light / dark): Paper `#F4F3EE` / `#141A17` (page) · Surface `#FFFEFA` / `#1B231F` (records, inputs) ·
Text `#20251F` / `#EFEDE4` · Muted `#5C635B` / `#A2AAA1` · Line `#D9D8D0` / `#2B3530` (dividers) ·
Line-strong `#868A80` / `#6D7771` (control borders, 3:1) · **Accent (terracotta) `#BD4B27` / `#F5803F`:
the primary action only** · Proof green `#2B5A3F` on `#E3EBDA` / `#A9D1B4` on `#22362A`: earned marks and
proof only · Danger `#A8322D` / `#F08A80`: errors and destructive actions only. Dark `.band` strips on the
landing always use the dark tokens.

Type (self-hosted, OFL, Latin + Latin-ext + Cyrillic): **Manrope** (headlines, 500), **Inter** (body, UI),
**IBM Plex Mono** (mono labels, code, record numbers). Scale 1.25. Body 17px desktop / 16px mobile,
line-height 1.55, max line ~68ch. Mono uppercase labels (12px, tracked) name records, meta lines and
eyebrows; that is part of the style now. Do not put mono caps on long sentences.

Objects: **records** (`.record`: frame + mono header row) hold a project's proof, build log, embed badge and
filters; **panels** (`.panel`) are form sections; list rows (`.plate-row`) and landing cards are quieter.
Badges after a name (official, moderator) are one component: glyph button, tooltip, shared popover with the real date.
Hallmarks are flat chips (check + mono label, "Repo owner" / "Domain verified" / "Steady"), pale green when earned,
dashed outline + "Not yet" when not. Depth = surface color + hairlines; no bevels or gradients, one shadow only on floating menus and toasts.
One gradient on purpose: the "halo" (`.btn--halo`), a rotating light ring on GitHub sign-in buttons, "New project" and
"Publish project", on hover/focus/loading only (plus a slow idle turn on the landing hero button).
Radius 0 everywhere except buttons (`--radius-btn` 10px; states: hover, press, focus, disabled, loading)
and avatars (round). Icons: own inline SVG set, 1.5px stroke. No icon fonts, no emoji as icons.
Layout: left-aligned text, max width 1200px. Every page uses the shell: `.container.shell` (`--narrow` 46rem for reading,
`--card` 32rem for single cards, both centred) + `.page-head` header block (eyebrow, h1, lede, actions, hairline) or a
`.sheet` (head/aside 4 + panels 8, both to the edges). Pages declare their own 12-column grids from 64em; one column on phones.
Logo: mark C "struck slash" + lowercase wordmark "shipmark" (Manrope 700, outlined);
`SITE_NAME` stays "Shipmark" in running text, `SITE_DOMAIN` is `shipmark.me`.

Motion (`motion.css`, `motion.js`): animations are transform and opacity only (plus hover colour/border fades, no
layout); loops run only while on screen and pause in a hidden tab (pause rules need `.js`, so without JS nothing
freezes); at most 3 loops visible at once; `prefers-reduced-motion` shows the final state everywhere. Landing: the
hero strike, pulse, tick, sign-in button shimmer (3 loops), closing cursor, section reveal. Project page: marks strike
in order on load, one tick over the uptime strip. Every inner page (once; CSS except the count-up): the page rises in, list items
enter one after another, cards answer hover/press, profile stats count up (`[data-count]`), empty-state marks are set
down and the first fails to stamp. Plus hover/press/focus answers, menu/toast fades and a page cross-fade
(`@view-transition`, ignored where unsupported).

Contrast (measured both themes, table in `docs/DESIGN.md`): every text pair >= 4.5:1, every control edge and
focus ring >= 3:1. Recheck after any token change. Performance and accessibility numbers are in the same file.

Avoid: coloring or italicizing one word in a headline; gradient washes; identical card grids with the same
soft shadow; `→` glued to button text (use the inline arrow icon); neon accents; Bootstrap look; filler copy.
Copy: plain, specific. Buttons say what happens ("Publish project", "Verify domain"), and the result uses
the same word ("Published"). **Never claim who wrote the code**: the first mark is "Repo owner".

---

## 10. Quality bar: every device

- Mobile-first. Check at 360, 390, 768, 1024, 1280, 1440 px widths.
- Must work in: Safari iOS, Chrome Android, Firefox, Chrome, Edge, Safari macOS.
- iOS rules: form inputs ≥16px font (prevents zoom), use `dvh` not `vh`,
  respect `env(safe-area-inset-*)`, no hover-only actions, tap targets ≥44px.
- Viewport: `width=device-width, initial-scale=1, viewport-fit=cover`.
- Accessibility: WCAG AA contrast, visible focus, full keyboard use, labels on inputs,
  alt text, `prefers-reduced-motion`, `prefers-color-scheme` + manual theme toggle.
- Performance: no layout shift from fonts (`font-display: swap` + size-adjusted fallback),
  images sized and lazy-loaded, JS deferred, pages usable before JS loads.

---

## 11. Admin

`django-unfold`, branded from `config/branding.py`. Sidebar sections: Users, Projects,
Verification, Moderation, Audit log. Dashboard: counts of users, published projects,
hallmarks by type, open reports, signups last 7 days. Actions: hide/unhide project,
suspend/unsuspend user, resolve report, re-run verification. Every admin action → AuditLog.
Staff only, at `ADMIN_URL`.

---

## 12. Legal and privacy

Pages from `content/<lang>/`: privacy, terms, cookies. They must describe **what the
code actually does** (data collected, why, retention, GitHub as a processor, rights,
contact). Only strictly necessary cookies (session, CSRF, language, theme), so no
cookie banner. Users can export their data (JSON) and delete their account
(confirmation step; projects removed; reports anonymized; AuditLog entry).
Signup records the accepted terms version and timestamp.
These texts are drafts; the developer gets them reviewed before public launch.

---

## 13. Saving usage limits (rules for you)

- Read only the files the task needs. Do not scan the whole repo "for context".
- Do not reformat or rename code outside the task.
- Run targeted tests, not the whole suite, unless the task is a final check.
- Keep explanations short. No summaries of things the developer did not ask about.
- If a task grows beyond the prompt, stop and say so instead of continuing.

---

## 14. Commands

```bash
source .venv/bin/activate
python manage.py runserver            # developer runs this
python manage.py test <app>
python manage.py makemigrations && python manage.py migrate
python manage.py makemessages -l uk --ignore=.venv && python manage.py compilemessages
python manage.py check_uptime         # cron in production
python manage.py reverify_domains     # cron in production
python manage.py community_daily      # cron in production (scores, 90-day notification cleanup)
python manage.py prune_support        # cron in production (closed support messages older than 12 months)
python manage.py post_welcome         # once: pinned welcome thread from the system account
python manage.py seed_community       # DEBUG only: demo community content (--clear removes it)
```

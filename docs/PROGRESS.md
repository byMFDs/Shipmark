# Progress log

- 2026-11-10: Task 1 done. Django 5.2 project (`config` with base/dev/prod settings), six app stubs, custom `accounts.User` with migration, `config/branding.py` + `brand` context processor, `base.html`, landing at `/`, requirements, README, tests. Next: design foundation (tokens/base CSS, fonts) or GitHub sign-in.
- 2026-11-10: Task 2 done. docs/DESIGN.md; self-hosted Plex fonts (+ size-adjusted fallbacks); tokens/base/components CSS; light/dark with no-flash toggle (theme.js); menu.js, toast.js; logo, mark, favicon, apple-touch-icon, OG image; {% load ui %} tags (inline_svg, icon, avatar, hallmark, site_header, site_footer); /styleguide/ (DEBUG only).
  Dark ink chosen: #8EA8F1 (same hue as the light ink). Next: landing hero (specimen plate) or GitHub sign-in.
- 2026-11-10: Task 3 done. i18n (en, uk): `UserLocaleMiddleware` (saved preference > cookie > Accept-Language > en), POST `set_language` at `/i18n/set-language/` (also saves choice on the account), footer switcher, uk translations compiled. `pages/content.py` loads `content/<lang>/<slug>.md` (fallback en, markdown + nh3), `/about/` placeholders, `docs/EDITING.md`, tests.
  Styleguide (DEBUG only) is not translated on purpose. Next: GitHub sign-in (Task 4).
- 2026-11-10: Task 4 done. GitHub-only sign-in (allauth, scopes read:user + user:email, no email/password routes), `/login/`, `/logout/` (POST), `/signup/` confirm step (username + Terms, saves version/time), `/settings/`, header avatar menu, username rules (lowercase, reserved list, `-2` suffix), `config/ratelimit.py`, uk translations, 32 tests.
  Avatars are NOT shown yet (initials only): `avatar_url` holds GitHub's URL, never hotlinked. Next: Task 5 (projects) or the safe_fetch task, which also unlocks avatar download.

- 2026-11-10: Task 5 done. Public profile `/u/<username>/` (avatar initials, name, bio, website, GitHub, join date, counts, empty state; 404 for unknown/suspended; `/u/Name/` redirects to lowercase; OG/description meta), `static/css/pages/profile.css`, uk translations, 8 tests.
  Counts and project list come from `accounts/profile.py` and return zeros/empty until Project/Follow models exist. Next: projects task (fill `profile_projects`, `profile_stats`, header "New project" link).

- 2026-11-10: Task 6 done. `projects` app: Project, Tag, Tool (19 seeded AI tools), Screenshot; `/new/` (+ markdown preview via JS), edit, publish/unpublish, delete with confirmation, up to 4 screenshots (Pillow check, re-encode to WebP, no EXIF, random names), reorder with Up/Down POST buttons; project page `/u/<user>/<slug>/` with plate, hallmark row (all "not yet" via the stub `projects/proof.py`); profile lists published projects (+ own drafts for the owner). Owner URLs go through `owner_project` (404 for others). 47 tests, uk translations.
  Next: safe_fetch + repo/domain verification (real `compute_hallmarks`), or follow/like/feed.

- 2026-11-10: Task 7 done. Authored hallmark: `verification/repo.py` (GitHub REST via httpx, owner by numeric GitHub id, fork never counts as owned, contributors paging, first/last commit dates, all API errors and rate limits handled), `RepoLink` model (only successful checks are stored, so nobody can block another person's repo), real `compute_hallmarks` for Authored, "Check repository" button (1 per 10 min per project), stale link removed when the repo name changes. 30 tests with mocked HTTP, uk translations.
  Decision: no per-user tokens (`SOCIALACCOUNT_STORE_TOKENS` stays False); optional server `GITHUB_API_TOKEN` raises the API limit. Next: safe_fetch + domain verification (Live), or follow/like/feed.

- 2026-11-10: Task 8 done. `verification/net.py::safe_fetch` (http/https, ports 80/443, DNS checked and the connection pinned to the checked IP with SNI kept, private/loopback/link-local/CGNAT/ULA/IPv4-in-IPv6 blocked, redirects re-checked (max 3), 5 s deadline, 512 KB incl. gzip, fixed UA). Domain verification (Live): `DomainVerification` (token per project+domain, one verified domain per project via partial unique index), DNS TXT or meta tag, editor section with copy buttons + "Verify now" via fetch (5/10 min), `reverify_domains` cron. `moderation.AuditLog` + `moderation/audit.py`. dnspython added. 61 new tests.
  Decisions: a failed manual check never removes Live (only the cron does); temporary errors are retried until 35 days. Next: uptime checks (Steady), or follow/like/feed.

- 2026-11-10: Task 9 done. Steady hallmark: `UptimeCheck` model, `verification/uptime.py` (HEAD, GET fallback via safe_fetch with `read_body=False`; ok = status < 400), `check_uptime` (Live projects only, max 1 check / 3 h, batches of 50, errors logged, prunes > 90 days), Steady = Live + ≥40 checks + ≥95% in 30 days, `with_uptime()` annotation for lists (no N+1). Project page: uptime %, last check, 30-day strip with text alternative. `docs/DEPLOY_NOTES.md` with cron lines. 28 new tests, uk translations.
  Decisions: % is rounded down (100% only when every check passed); no GET retry after a timeout or a blocked URL. Next: follow/like/feed, or explore.

- 2026-11-10: Task 10 done. `compute_hallmarks` returns a `HallmarkSet` of `Hallmark(kind, earned, reason, earned_at)` (lookup by kind: `marks["live"]`), cached per instance as `Project.hallmarks`. Project page: each large mark is a `<details>` with the rule, earned date and a link to `/how-proof-works/#<kind>`; profile rows show small marks; profile count uses it. `/how-proof-works/` (en, uk), heading anchors via `{#id}`. `RepoLink.earned_at` (+ migration 0004). 26 tests in `projects/test_proof.py`.
  Decisions: Steady has no earned_at (rolling 30-day window); `is_live` split into `current_row` + `row_is_live`. Next: follow/like/feed, or explore.

## Next

- Avatars: download GitHub avatars and store them locally (needs `safe_fetch` + Pillow re-encode), then pass `src` to `{% avatar %}`.
- On every login refresh `github_login` (GitHub users can rename), needed before the Authored check.
- Prod: configure a shared cache (DB or Redis-free file cache) so `config/ratelimit.py` works across gunicorn workers.
- Task 3: add latin-ext font subset when Polish is added (later, not now).
- Task 4: move the inline theme script to a hashed or external file before enabling CSP.

- 2026-11-10: Task 11 done. Build log: `BuildLogEntry` (≤500 chars, update/launch, one launch per project via partial unique index), inline markdown only (`render_log_markdown`: bold, italic, links, inline code; nh3), timeline on the project page (newest first, latest 50, `ago` filter: "3 days ago" / "щойно"), add/delete via fetch (`static/js/build-log.js`) with plain POST fallback (errors re-render the page with the text kept), 10 entries/day per project (DB count + cache counter, so delete does not refund), delete 60/h per user. 26 tests, uk translations.
  Decisions: a launch entry sets `launched_at` to its time; deleting it keeps `launched_at`. Next: follow/like/feed, or explore.

- 2026-11-10: Task 12 done. `social` app: Follow/Like (unique pairs, DB check against self-follow), idempotent follow/unfollow/like/unlike POST endpoints (JSON for fetch, redirect for plain POST, `next` only on this site; follow 60/h, like 120/h per user, suspended users 403), `static/js/social.js` (optimistic, rollback + toast, disabled while pending). `/feed/`: "Following" (projects + build log updates, launch entries left out) and "Latest launches"; "Load more" (`feed.js`) and Newer/Load more links without JS; signed-out = latest only. Real follower count on profiles. 44 tests, uk translations.
  Decisions: no likes on your own project (400, count shown as text); suspended users' content, follows and likes are excluded everywhere. Feed = 5 queries signed in (6 on "Following"), 3 signed out, whatever the page size. Next: explore, or moderation/reports.

- 2026-11-10: Task 13 done. SVG badges: `/badge/<user>/<slug>.svg` (site mark, name, one stamp per earned hallmark) and `/badge/<user>.svg` (@user, hallmark count), built in `projects/badges.py`, served by `projects/badge_views.py`. System font stack, `textLength` fixes the layout, hostile names stay valid XML. Public cache 1 h, no cookies, no `Vary` (middleware skips locale/user for `/badge/`). Unknown, draft, hidden, suspended: same neutral "not found" badge, status 200, cache 5 min. "Embed badge" panel (preview, Markdown, HTML, copy) for the owner on project and profile pages. 14 tests, uk translations.
  Next: explore, or moderation/reports.

- 2026-11-10: Task 14 done. Landing `/` (signed-in users go to `/feed/`): hero with the example plate struck on load (CSS only, reduced motion shows the final state), what it is, how proof works (rules from `proof.RULES`), 6 recent launches with empty fallback, one-click GitHub sign-in. `/explore/` (`pages/explore.py`): search name/tagline (icontains), tag/tool/hallmark filters, sort newest/most liked/most proven, all GET (shareable, no JS), 24 per page, out-of-range page 404. Open Graph blocks in `base.html` (type/url/title/description/image); project uses its first screenshot. `.project-thumb` moved to components.css (it was unstyled on the feed). 24 tests in `pages/test_explore.py`.
  Decision: hallmark filter and "most proven" use `compute_hallmarks` itself (DB narrows, Python checks), no second copy of the rules in SQL. Next: moderation/reports, or legal pages.

- 2026-11-10: Task 15 done. `moderation.Report` + `/report/project/<user>/<slug>/` and `/report/user/<user>/` (signed in, 5 per hour, one open report per person and target, "Something else" needs details; reporter/target are SET_NULL so reports survive deletions). django-unfold admin (name, logo, colors from `config/branding.py` and tokens), sidebar and dashboard from section 11 (`moderation/dashboard.py`), admins for every model, actions in `moderation/actions.py` (hide/unhide, suspend/unsuspend, resolve, re-run verification) all write AuditLog; form edits of status/suspension and admin deletes are logged too. AuditLog is read-only. `ADMIN_URL` from env; `prod.py` refuses "admin/". Suspended content was already filtered everywhere; now covered by tests. Tests in `moderation/tests.py`.
  Decision: admin labels and report pages are translated (uk); `reverify` runs synchronously in the admin action, max 20 rows. Next: legal pages, data export and account deletion.

- 2026-11-10: Task 16 done. `docs/DATA_INVENTORY.md` (every personal field: source, purpose, retention, who sees it, third parties). `/legal/privacy|terms|cookies/` (en, uk) written from it, "Draft" note on top, `{{ contact_email }}`-style placeholders filled from `branding.py`; footer links appear by themselves. `TermsAcceptanceMiddleware`: after a `TERMS_VERSION` bump signed-in users get `/terms/accept/` (legal pages, sign-out, export, delete stay open; badges untouched). Settings: "Download my data" (POST, JSON, `accounts/export.py`, 13 queries flat) and "Delete account" (type username; `accounts/deletion.py`: cascade, reports anonymized, AuditLog `account.deleted` without username). 24 tests in `accounts/test_rights.py`, uk translations.
  Decisions: accounts with no accepted version (createsuperuser) are not asked; suspended users can export and delete. Next: avatars stored locally, or a final pre-launch check.

- 2026-11-10: Task 17 done. Languages pl, de, es, fr, pt-br added (`LANGUAGES`, `locale/*/django.po` with 446 strings each, `content/<lang>/` with all 5 pages; legal pages carry "Translation for convenience; the English version prevails"). Glossary at the top of `docs/EDITING.md`; Authored/Live/Steady stay English (same as on badges). IBM Plex latin-ext fonts added for Polish; `hyphens: auto` on headings/prose fixes German h1 overflow at 360px (checked 7 langs x 8 pages in Firefox, no horizontal scroll). Migration `accounts/0003` (language choices). 13 tests in `pages/test_languages.py`.
  Next: native-speaker review of the new translations before launch; optionally uk legal "convenience" note.

- 2026-11-10: Task 18 done (cross-device, a11y, performance pass). Measured every page at 360/390/768/1024/1280/1440, light and dark, in Firefox (360 and 390 through an exact-width iframe, because headless Firefox cannot go below ~500px). Fixed: long repo name widened the project page on phones; theme switch, landing section links, profile GitHub link and footer links are now 44px tap targets; "Built with" had no space above it; failed forms get an error summary (`role="alert"`, focused by `static/js/form-errors.js`, links to each field); condensed 600 heading font preloaded. Verified without changes: contrast (all pairs AA, both themes), focus styles and tab order, reduced motion, image sizes and lazy loading, iOS font sizes, `aria-invalid`/`aria-describedby` on fields. 1 new test (`SettingsTests`), uk string added.
  Next: fix what the real-device checklist finds; native review of pl/de/es/fr/pt-br (the new error-summary string is English there).

- 2026-11-10: Task 19 done (security audit). `check --deploy` clean (HSTS subdomains/preload via env); `pip-audit -r requirements/prod.txt`: no known vulnerabilities (added to dev.txt). Fixed: CSP + Permissions-Policy middleware (theme bootstrap moved from inline `<script>` to `static/js/theme-init.js`), prod rate limits now use a shared DatabaseCache (run `createcachetable`), admin login throttle (10/15 min per username), explicit `X_FRAME_OPTIONS`/cookie flags. Every view, markdown path, upload and outbound request reviewed: no high issues found. 11 new tests in `config/tests.py`; deploy checklist in `docs/DEPLOY_NOTES.md`.
  Next: set up the server (proxy must overwrite X-Forwarded-Proto), real-browser pass with the CSP, then launch checklist.

- 2026-11-10: Task 20 done (production readiness). `prod.py`: DB connections kept 60 s with health checks, `MEDIA_ROOT` from env (+ 4-step note for S3-compatible storage later), `SECRET_KEY_FALLBACKS` for rotation, JSON logs on stdout (`config/jsonlog.py`, no IPs/user agents). `gunicorn.conf.py` (localhost, 3 workers, JSON access log). Smoke-tested prod settings + gunicorn + WhiteNoise (hashed, gzip, immutable) on SQLite. `docs/DEPLOY_NOTES.md` rewritten: env table, release steps, local PostgreSQL on Pop!_OS, cron, pg_dump + media backups with restore test, key rotation, pre-launch checklist. 4 tests in `config/tests.py`.
  Not verified: migrations/tests on real PostgreSQL (needs `sudo apt install postgresql`; commands are in DEPLOY_NOTES). Next: run them, then pick hosting together.

- 2026-11-11: Legal sync. `docs/DATA_INVENTORY.md` and `content/*/privacy.md` (7 languages) now match the code: rate-limit counters live in the DB cache (up to 24 h, not "memory, 1 h"), app logs have no IP, backups kept 14 days. Reverse-proxy and app log retention, and off-server backup retention, are marked TODO (visible in the privacy draft).
  Next: decide those retentions, then replace the TODOs; lawyer review.

- 2026-11-11: Redesign phase 0. `docs/REDESIGN_PLAN.md`: what is taken from the Figma images, deviations, tokens, fonts (Geologica + Inter + Plex Mono), components, 3 logo options, motion plan, phases, open points.
  Next: developer approves the plan (and the 5 open points), then phase 1 (foundation + styleguide).

- 2026-11-11: Redesign phase 1 (foundation). New tokens (warm paper, square corners, terracotta action, green proof, dark `.band`), fonts Manrope (headlines) + Inter (body) + Plex Mono (labels), size-adjusted fallbacks; components rewritten with the same class names (hallmark is now a flat chip, new: record, card, proof note, section head, link-arrow); `motion.css` + `motion.js` (strike, pulse, tick strip, drift, cursor, reveal, view transitions, pause offscreen/hidden tab). Logo: 3 options in `static/brand/options/`, B "corner stamp" in use (A read as a checkbox at 16px); favicon, touch icon, OG image regenerated. `SITE_DOMAIN`, new TAGLINE. Styleguide shows logos, motion and both themes.
  Next: phase 2 (landing). Old token names are aliased in tokens.css until phase 3.

- 2026-11-11: Redesign phase 1 fixes. Logo switched to C "struck slash" (one 8-unit punch, 2:1 slash, 4×4 px stop at 16px) in logo/mark/favicon SVGs and both PNGs; A and B only on /styleguide/. Dark primary button `#E5835C` → `#F5803F` with dark text (6.76:1); every token pair measured in both themes, table in `docs/DESIGN.md`. localhost vs 127.0.0.1: server output identical (HTML, CSS, fresh-profile screenshots pixel-equal); cause is per-origin browser state (static had no Cache-Control → heuristic cache; theme in localStorage). Dev-only `LocalhostRedirectMiddleware` + static `no-cache` via WhiteNoise in dev; 7 tests; README note.
  Next: developer approves, then phase 2 (landing).

- 2026-11-11: Redesign phase 2 (landing). `/` rebuilt from the Figma images: hero + illustrative "project record" (labelled, relay.example, 99.9%), statement band, 01 marks (rule text from `proof.RULES`), 02 real recent projects or 3 labelled illustrative cards (never mixed), 03 build log + badge picture, closing band; footer flush. Motion: strike once; pulse, tick strip, drift in the hero; cursor in the closing band; reveal on 01-03. "Submit your project" = GitHub sign-in with next=/new/.
  Copy honesty: mark shown as "Repo owner / Власник репозиторію" everywhere (UI, badges, admin, Explore filter, content pages in 7 languages; id `authored` unchanged); "wrote the code" removed. Fixed duplicated uk Steady rule. Checked 360/390/768/1440, light/dark, en/uk.
  Next: phase 3 (feed, explore, profile, project pages).

- 2026-11-11: Redesign phase 3 done. 3a project page (head, cover, proof column with marks + 30-cell uptime strip, build log, embed, editor, delete confirm; badge colors/corners), 3b feed, explore, profile, settings, delete account (shared `.page-head`, `.sheet`, `.panel`), 3c auth cards, content pages (`content.css`), styled 404/403/500/400/CSRF pages (`errors/`, root templates), admin palette + light logo (`LOGO_DARK`), DESIGN.md and CLAUDE.md section 9 rewritten to match.
  Copy honesty re-checked (no "Authored"/code-authorship text left; `docs/DATA_INVENTORY.md` fixed). Motion: marks strike in order, one uptime tick loop. uk strings added for the error pages; pl/de/es/fr/pt-br fall back to English for them.
  Not tested: real iOS/Android devices, signup confirmation page in a browser (needs a live GitHub login), the 500 page on a real crash. Next: phase 4 (motion polish, full 360-1440 x light/dark pass, a11y).

- 2026-11-11: Redesign phase 4a (motion and performance). Audit: every animation is transform/opacity (only hover colour/border fades and the menu/toast fades are not layout-affecting), max 3 loops visible (landing hero: pulse, tick, drift; project page: 1 tick; closing cursor is far from the hero), reduced motion = final state. Fixed: pause rules now also hit `::before/::after` (pulse and cursor did not pause in a hidden tab) and only apply with `.js` (without JS the strike on the project page stayed frozen at its first frame). Removed dead CSS: old token aliases, `.grid`/`.col-*`, `.plate__media`, `.section-head__titles`, `.arrow--nudge`. CSS 94,967 -> 93,923 B (gzip 20,866 -> 20,680); core CSS per page 55 KB raw / 14 KB gz, core JS 5.9 KB raw / 2.7 KB gz, fonts 243 KB total (latin set ~88 KB per page, woff2). Prod `collectstatic` hashes all files.
  Not done: font subsetting (no fonttools here). Next: 4b accessibility and devices.

- 2026-11-11: Redesign phase 4b (accessibility, devices, copy). Scripted Firefox (Marionette) audit: 13 pages x 360/390/768/1440 x light/dark (uk; de at 360 for clipping): no horizontal scroll, no unlabeled fields/missing alt, inputs >= 16px, visible focus on every focusable element, skip link first, no positive tabindex, one h1; contrast 0 failures (DOM check + token table in `docs/DESIGN.md`). Fixed: feed empty-state headings h3 -> h2 (h1>h3 skip), footer logo link 44px, skip link 44px, profile GitHub link 44px on touch, owner-bar buttons full width on phones. Copy: the OG image still said "Authored" -> regenerated with "Repo owner"; no other claim about who wrote code (grep of templates, .po, content, docs, brand); hero example stays labelled illustrative.
  Not tested: real iOS/Android (safe-area, dvh, touch targets only by CSS reading; 360/390 emulated by zoom in a 540/585px window); screen readers; error pages 500/400/403_csrf only as rendered HTML. Next: 4c docs and cleanup.

- 2026-11-11: Redesign phase 4c (cleanup and docs). `docs/DESIGN.md` and CLAUDE.md section 9 now match the shipped design (tokens, fonts, palette, logo C, components, motion rules incl. the hover-colour exception, performance numbers, accessibility, contrast table); `docs/EDITING.md` (SITE_DOMAIN, dark logo files, OG image text, fonts and tokens paths); `docs/REDESIGN_PLAN.md` marked completed. Decision: `SITE_NAME` stays "Shipmark" (used in sentences and titles); only the logo files and OG image are lowercase.

## Redesign done (phases 0-4, branch `redesign`, not merged)
Warm-paper design with terracotta action, green proof, square corners; Manrope + Inter + Plex Mono; logo C; every page rebuilt; motion audited; contrast 0 failures; copy says "Repo owner", never code authorship.
Before merging: look at the final manual checklist (real phone, keyboard, reduced motion) and replace the footer placeholders `LEGAL_OWNER_NAME = "Your Name"` and `CONTACT_EMAIL = hello@example.com` in `config/branding.py`.

## Next
1. Single feed page with a filter (following / latest in one place).
2. Avatar and profile customization.
3. About page content.
4. Achievements.
5. Verification fixes (forks, link a repository to its domain).
6. `seed_demo` command (demo users and projects for screenshots and local work).
7. Project type adapters (web app, CLI, library, mobile: what "Live" means for each).
8. Deploy (see `docs/DEPLOY_NOTES.md`).

- 2026-11-11: Fix pass after manual test (branch `redesign`). 1) Custom 400/403/404/500/CSRF views (`config/errors.py`; 500/400/CSRF without DB), new copy + "mark fails to stamp", `X-Request-ID` + "Reference" on 500/403/CSRF, JSON error files `errors.jsonl`/`notfound.jsonl` (scrubbed, rotating, `LOG_DIR`), `show_errors` command, `/_dev/errors/<code>/` previews.
  2) `SITE_URL` (dev localhost:8000, prod https://shipmark.me) for embed snippets, OG, canonical, export; favicon: files were already logo C, the tab showed a stale browser favicon cache (same URL since phase 1) and there was no favicon.ico -> content-versioned icon URLs, `favicon.ico` + `/favicon.ico`, `make_icons`; embed "how to use" hint.
  3) About page in all 7 languages from facts in CLAUDE.md/docs/code (proof rules, what is not verified, what builders get, who, next, contact); visible TODOs for the developer to confirm.
  4) Translations: cause = makemessages ran only for `uk` during the redesign (87 strings never reached pl/de/es/fr/pt-br) and the old test only looked for empty entries; no hardcoded UI strings found. All 537 strings in 6 catalogs, no fuzzy, compiled; privacy pages synced; new `pages/test_translations.py`. Next: native-speaker review of pl/de/es/fr/pt-br, confirm About TODOs, real CONTACT_EMAIL.

- 2026-11-12: Trust hardening, stage 1 (audit only, no app code). `docs/TRUST_AUDIT.md`: what each hallmark checks today, attack scenarios a–l run as temporary mocked tests (deleted), ranked bypasses, fix evaluation, honest wording en/uk.
  Main gaps: fork + 10 commits, no repo re-verification, own copy of someone's code, contributor gets "Repo owner", uptime follows redirects to other hosts.
  Next: stage 2 (A–F) after approval.

- 2026-11-12: Trust hardening, stage 2 (branch trust-hardening, commits A–F + token file). Repo owner only for own non-fork repos (or the project's `.shipmark-verify` file); ids instead of names; login refreshed at every sign-in; review states + admin queue + blocks; weekly `reverify_repos`; uptime must answer from the verified domain; shared-host apexes refused; "What was checked" panel; texts in 7 languages; attack tests a–l.
  Next: run the one-time steps in `docs/DEPLOY_NOTES.md` ("Trust hardening") on a DB copy, then production; add the `reverify_repos` cron line.

- 2026-11-12: Features round, stage 0 (plan only, no code). `docs/FEATURES_PLAN.md`: model changes (badges, news, sanctions, reports, profile fields), URL map, permission matrix, "For you" formula, risks, 10 open questions. `docs/FEATURES_STATUS.md` created.
  Next: answers to the open questions, then "GO 1" (screenshots bug first, then badges, news models, sanctions).

- 2026-11-12: Features stage 1. Screenshots fixed (cause: separate upload form; now one form with Save/Publish, tests). `UserBadge` + `accounts/roles.py` (moderation only from the badge), badge admin (superusers only) + `grant_badge`, reserved names, system account `shipmark`, official/moderator marks next to names. `news` app (model + admin). `Sanction` model + admin. Staff can no longer grant themselves superuser in the admin. 7 languages, 672 tests.
  Next: "GO 2" (moderation: /mod/, report statuses, enforcement of mute/ban).

- 2026-11-12: Features stage 2 (moderation). Report statuses + log-entry reports; `/mod/` queue, detail, "Moderate" while browsing; decisions with a reason the person sees (dismiss, remove project, clear profile, mute ≤7 d, ban ≤14 d; restore/purge superuser-only); guardrails + rate limit; mute enforced via `can_write`, ban ends sessions and refuses sign-in; salted GitHub-id hash against ban evasion (`prune_bans` cron); notices; legal texts in 7 languages. 708 tests.
  Next: "GO 3" (profiles).

- 2026-11-12: Features stage 3 (profiles). New profile fields, links, skills, pinned projects; avatar and cover (upload or one-time GitHub download via `safe_fetch`, cropped, re-encoded, local files, deleted with the account); profile card with tabs Projects / Build log / About; settings as grouped sections with a live preview; export and moderation "clear profile" updated; 7 languages; 750 tests. Not checked in a real browser.
  Next: "GO 4" (feed and news pages).

- 2026-11-12: Stage 3 follow-ups. Muted accounts: the whole public profile (name, headline, About, location, status, skills, links, pinned, pictures) is read-only, only the language is saved; link validator now rejects a backslash and control characters (`https://evil.example\.github.com` passed before); tests for look-alike hosts and schemes, one image pipeline and limits for screenshots/avatars/covers, export without `bio`/`website`. All media deletes go through `storage.delete` (storage API); `media/` is gitignored and untracked.
  Next: GO 4 (feed and news pages). **Cleanup to do later: remove the deprecated `User.bio` and `User.website` columns** (migration after the stage 6 final check; nothing reads or writes them, `about` and `ProfileLink` replaced them).

- 2026-11-12: Ban hash: dedicated key. `BAN_HASH_KEY` (env, required and checked in production, dev default) replaces SECRET_KEY for ban-evasion hashes; HMAC-SHA256 with the constant label as a prefix; `BannedIdentity.hash_scheme` (migration 0005), lookups try the new key first and the old scheme only while old rows exist; `manage.py rehash_bans` converts old rows whose account still exists (tested on a DB copy). Docs: `.env.example`, DEPLOY_NOTES ("BAN_HASH_KEY"), DATA_INVENTORY.
  To do later: when `rehash_bans` reports no old-scheme hashes on production, delete the legacy lookup (`_legacy_hashes`) from `moderation/bans.py`.

- 2026-11-12: Features stage 4 (feed and public news). `/feed/` with tabs For you (default) / Following / News, filters in the URL (tag, tool, hallmark, time range, sort), SQL ranking documented in `social/ranking.py` (parity-tested against `compute_hallmarks`), richer cards (thumbnail cover, badges, marks, latest update, optimistic like/follow), three-column layout, no dashed empty frames. `/news/` and `/news/<slug>/` public. Screenshot thumbnails (`make_thumbs` after deploy). Constant query counts; Explore untouched, merge proposal in FEATURES_PLAN section 7. 7 languages.
  Next: "GO 5" (design pass, buttons, effect, motion, copy). Not checked in a real browser.

- 2026-11-12: Features stage 5 (design pass + copy). Hero text for builders, "Live" shown as "Domain verified" everywhere (7 languages, id unchanged). One page shell on every page (centred narrow/card widths, header block, balanced sheets and feed), 10px buttons with full states and a loading ring, rotating "halo" border on GitHub sign-in and two main actions (idle shimmer on the hero only; specimen drift removed to stay at 3 loops), inner-page motion (rise, staggered lists, card hover/press, count-up, empty marks). Feed card marks on phones fixed. 850 tests.
  Next: "GO 6" (leftovers, docs, legal, final tests).

- 2026-11-12: Features stage 6 (leftovers). Repo check: cooldown per project + repository, hourly caps, neutral wait message with minutes, no stale result. Sign-in/sign-out toasts in the page's language (saved language at sign-in, language cookie follows it). Legal drafts updated in 7 languages (profile data, pictures, moderator access, appeals, retention, language cookie). CLAUDE.md, EDITING, DEPLOY_NOTES, DATA_INVENTORY updated. 858 tests, `check --deploy` clean.
  Next: review the whole features-1 branch, set a real `LEGAL_OWNER_NAME`, lawyer review of the legal drafts, then merge; later drop `User.bio` / `User.website`.

- 2026-11-12: Community round, stage 0 (plan only, no code; branch `community-1`). `docs/COMMUNITY_PLAN.md`: models, URL map, permission matrix, hot formula, abuse numbers, 32 stickers, image pipeline, risks, 10 open questions. `docs/COMMUNITY_STATUS.md` created. Baseline: 858 tests green (serial run; `test --parallel` crashes with a pickling error, not looked into).
  Next: answers to the open questions (2, 3, 4, 5, 9 affect stage 1), then "GO 1" (backend).

- 2026-11-13: Community stage 1 (backend). App `community/` behind `COMMUNITY_ENABLED` (dev on, prod off): boards, threads, replies (depth 3), images, upvotes; reports on threads/replies in /mod/; remove/lock/pin with reasons, notices, AuditLog; age, link, image, rate and duplicate limits; Hot/New/Top in SQL; deletion and export cover it; minimal templates; 7 languages. Details: `docs/COMMUNITY_STATUS.md`.
  Next: "GO 2a" (reply notifications, sticker files), then 2b (UI).

- 2026-11-13: Community stage 2a. In-app reply notifications (`ReplyNotification`, `/community/notifications/`, header dot from `User.community_notified_at` at zero queries, 90-day pruning in `community_daily`, export), 32 original sticker SVGs with safety and manifest tests, sticker sheet on /styleguide/, 7 languages.
  Next: "GO 2b" (UI: picker, composer, image grids and lightbox, pages).

- 2026-11-13: Community stage 2b (UI). Pages in the feed shell, community.css, composer with previews, sticker picker, image grids, lightbox, rules page, Load more; adopted and fixed an unapproved draft from `stash@{0}` (kept). 50 UI tests; translations in 6 languages.
  Next: "GO 3" (seed_community, post_welcome, rules in 6 languages, Terms/Privacy/DATA_INVENTORY, DEPLOY_NOTES, `check --deploy`); look at the pages in a browser first.

- 2026-11-13: Community stage 3. `post_welcome` and `seed_community` (DEBUG only) with tests; rules page in 7 languages; Terms/Privacy community sections (drafts), `TERMS_VERSION` 2026-11-13; DATA_INVENTORY 6a; DEPLOY_NOTES (switch-on steps, cron), EDITING, CLAUDE.md. Full suite green, `check --deploy` clean.
  Next: look at the pages in a browser (both themes, 360-1440 px); native-speaker and lawyer review of the new texts; decide about `stash@{0}`; then review and merge `community-1`.

- 2026-11-13: Polish round (branch `polish-2`, from `community-1`). Footer on one 12-column grid with shared control sizes; support form + private attachments + admin inbox + SMTP notice (Gmail steps in DEPLOY_NOTES); official/moderator badges as one popover component with the real date; "<n> people joined" in the header (honest count, cached 60 s, PUBLIC_USER_COUNT_MIN). Legal drafts, DATA_INVENTORY, DESIGN, EDITING, CLAUDE.md updated. Full suite green, `check --deploy` clean.
  Next: look at footer, support pages, badge panel and header count in a browser (both themes, 360-1440 px, de/fr); set up the Gmail inbox; fix the multi-line `{# #}` comments in five community templates (they print as text).

- 2026-11-13: Polish-3 stage 0 (branch `polish-3`). /community/new/ printed "<Block Node ...>": views passed a context variable `block`, which Django shadows inside `{% block %}` with the BlockNode; renamed to `post_block_reason` (also fixes the thread page for locked threads / muted members, who now see the real reason). Leak tests for every community page and role, main pages, error pages, plus template source checks. 1075 tests green.
  Next: "GO 1" (names and copy). Status: `docs/POLISH3_STATUS.md`.

- 2026-11-14: Polish-3 stage 1 (names and copy). "Feed" → "For You" / "For You Page", inner tab "Recommended", "Explore" → "Discover"; header bar fits de/fr (menu below 80em, self-hiding tagline); all 1146 UI strings swept (plainer words, real plurals in admin, delete page matches the code); untranslated form labels fixed with a test; Privacy/Terms easier to read, same facts, 7 languages. 1076 tests green.
  Next: "GO 7" (people search). Native + lawyer review of POLISH3_COPY.md / POLISH3_LEGAL_CHANGES.md.

- 2026-11-14: Polish-3 stage 7 (people search). Discover tabs Projects / People; username search (prefix first, ≥2 chars, 20 per page, hidden/system/demo accounts excluded, wildcards inert), rows with badges, counts and Follow / "You" / "Sign in to follow"; header search (icon from 80em, field in the menu); rate limit per account or salted IP hash (Privacy + DATA_INVENTORY updated); constant query count; 33 tests; 7 languages.
  Next: "GO 2" (button glow). Not tested on PostgreSQL.

- 2026-11-14: Polish-3 stage 2 (button glow). Halo ring keeps its resting colour on hover; the running light is the text colour + an accent spark in both themes (was invisible on the light theme); every ring colour >= 3:1 on page and surface, measured and tested from tokens.css. File-input button radius matches buttons.
  Next: "GO 3a" (design audit, POLISH3_DESIGN.md).

- 2026-11-14: Polish-3 stage 3a (design audit, no code). 18 pages at 360/768/1024/1440, both themes, CSS scan: 11 layout problems, one spacing / icon / alignment rule set, dark theme proposal with a new `--raised` level and measured contrast, add/remove list. All in docs/POLISH3_DESIGN.md.
  Next: "GO 3b" (implement the approved parts).

- 2026-11-14: Polish-3 stage 3b (design pass). Layout fixes (tabs, badges, hyphens, thread facts, /mod/ and settings on phones, footer language, main action at 768-1279px, touch target); one spacing + icon scale as tokens; dark theme with three levels (`--raised`) and visible hairlines, AA tested from tokens.css, before/after on /styleguide/; header tagline removed, zero like counts hidden, one accent per page area, landing invite card, "/" for search. 7 languages.
  Next: "GO 4" (motion).

- 2026-11-14: Polish-3 stage 4 (motion). Current-tab mark slides between tabs on navigation (cross-document view transitions, one name per tab row), theme switch cross-fades, scroll-driven reading hairline on legal/content/news pages, disclosures drop in, new build log entry and domain status rise in, "new replies" dot set down once. No new loops; `pages/test_motion.py` guards the rules. 1126 tests green.
  Next: "GO 5" (support email + bug sweep).

- 2026-11-14: Polish-3 stage 5. Support email cause found (no EMAIL_* / SUPPORT_INBOX_EMAIL in .env, silent skip, console backend in dev); `send_test_email`, prod system check, admin inbox banner, logged skip, Gmail steps in DEPLOY_NOTES, mock-SMTP tests. Bug sweep: route matrix for 7 roles, link/alt/label/leak crawl, translations, dead code; parallel test runs fixed. 1140 tests green (--parallel 4).
  Next: put the Gmail app password in .env and run `python manage.py send_test_email --smtp`; then "GO 6" (code comments).

- 2026-11-14: Polish-3 stage 6 (code comments). A short Ukrainian line on every module, class, non-trivial function, template, JS and CSS file; tests one line per class; one commit per app. `scripts/check_comment_only.py` proves the change is comments only (326 files vs bf784af). 1140 tests green.
  Next: polish-3 is complete; review the branch, then the final manual checklist (real phone, keyboard, reduced motion) before merging.

- 2026-11-14: Polish-3 follow-ups. polib wheel untracked, CLAUDE.md comment rule, unused moderation helpers removed, tabs fix (every tab had lost its left padding; own test), a request no longer leaves its language active in the thread (flaky parallel tests; own test). 1142 tests green twice.
  Next: review the branch; real-browser check of tabs and motion; Gmail app password + `send_test_email --smtp`; then merge.


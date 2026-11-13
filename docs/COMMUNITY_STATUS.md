# Community status (branch `community-1`)

Brief: community master brief (kept by the developer in `docs/promts/`, not in git). Plan: `docs/COMMUNITY_PLAN.md`.

## Stages

| # | Stage | Status |
|---|---|---|
| 0 | Plan | done 2026-11-12, answers received |
| 1 | Backend: data, permissions and abuse limits, flag, moderation integration, admin, abuse-case tests, minimal UI | done 2026-11-13 |
| 2a | Backend for the UI: reply notifications (in-app), sticker files + manifest test, permissions and abuse tests for them | done 2026-11-13 |
| 2b | UI: C (picker), D (composer, grids, lightbox, `blob:` preview), E (pages, 3 columns, Load more) | done 2026-11-13 |
| 3 | Polish: design and motion, legal (Terms, Privacy, rules, `TERMS_VERSION` bump), docs, full tests, `check --deploy` | not started |

## Decisions proposed in the plan (change if the developer disagrees)
- New app `community/`, always installed; `COMMUNITY_ENABLED` is checked by one decorator on every view (404 when off).
  Data export and account deletion handle community rows even when the flag is off.
- Author delete wipes the text for real (`deleted_at`); moderator removal keeps the text for appeals and restore.
- `Reply.root` (top-level ancestor) so a page of the tree loads in one query; a reply to depth 3 becomes a depth-3 sibling.
- Images are sent with the form (no separate upload endpoint, no orphan files); the existing `clean_image` and
  `make_thumbnail` are reused unchanged.
- Hot ranking in whole numbers with step decay, like `social/ranking.py`; pinned threads sit in their own row.
- Duplicate check and rate limits are cache-based (`config/ratelimit.py`), no extra columns.
- Sticker manifest is a Python module (`community/stickers.py`) so labels go through gettext; 32 stickers planned.
- `Vote` is not registered in the admin: nobody sees who voted for what.
- Titles can be edited only in the first 15 minutes.

## Answers from the developer (2026-11-13)
1. Moderators may pin threads of protected accounts; remove and lock are not allowed on them.
2. No votes on your own post. 3. Moderator remove deletes the image files at once; restore brings back text only.
4. Account deletion: replies keep their text, author shown as "[deleted]" (no picture, no link); threads without
   other people's replies are deleted. 5. Accounts younger than 24 hours cannot upload images.
Also: in-app reply notifications (no email); stage 2 split into 2a/2b; `blob:` in CSP only for the form preview;
raise `TERMS_VERSION` when Community ships; `COMMUNITY_ENABLED` stays off in production.

## Stage 1 (done)
- App `community/`: Board (5 defaults by migration 0002, names translated through gettext), Thread, Reply (`root` for
  one-query branches, depth 1-3 checked in the DB), CommunityImage (display 1600 + thumb 640, `projects.images`),
  Vote (one per person and target, DB constraints). `Report.thread` / `Report.reply` + "at most one target" over all
  five fields, new Notice kinds. Migrations tested forward/back/forward on a DB copy (with a report row).
- Flag `COMMUNITY_ENABLED` (env; dev on, prod off) via `community_view` on every route, also `/report/thread|reply/`
  and `/mod/act/thread|reply/`; header link only when on; report details about threads/replies 404 when off.
- Rules (`community/limits.py`, `permissions.py`): 10-minute and 24-hour account age (moderators exempt), 1 link and no
  images under 24 h, 5 threads / 30 replies / 120 votes / 10 images / 30 edits per hour, duplicates (thread 24 h,
  reply 10 min; short replies only under the same parent), silent edit 15 min, title only in that window,
  delete own (text wiped; with replies shown as "[deleted]"), locked = moderators only.
- Moderation: remove thread/reply, lock/unlock, pin/unpin with a reason, Notice to the author, AuditLog, reports
  resolved; protected accounts: pin only; restore (superuser, text only). Queue filter Thread/Reply, report detail
  shows the post. "Moderate" menu tag accepts `thread=` / `reply=`.
- Hot / New / Top in SQL (`community/ranking.py`), search by title, pinned row, reply tree Best / New with pages,
  constant query counts (tested). `community_daily` (was `community_recount`) repairs counters, drops votes of hidden accounts, prunes old notifications.
- Account deletion and export cover the community (even with the flag off). Admin: boards editable, posts read-only
  with restore; votes not registered.
- Minimal UI only (plain templates, no community CSS yet): lists, thread, forms, delete confirmation.
- 64 tests in `community/tests.py`; translation test now also renders the community pages in 6 languages.

## Stage 2a (done)
- Reply notifications (in-app, no email): `ReplyNotification` (recipient, reply, kind thread/reply, created, read; one per
  recipient and reply). The answered person is told, also when the depth limit attaches the reply one level up; nobody
  about their own reply; nothing for deleted or inactive accounts. `/community/notifications/` lists only your own
  (no per-item URL, so nothing to guess), 30 per page, constant queries; opening it marks all read.
  Removed, deleted, banned-author replies drop out by themselves (query filter, nothing to clean up).
- Header mark: `User.community_notified_at` (accounts migration 0007), so the dot on the avatar and the "Replies to you
  · new" menu item cost no query on any page (the site has many exact query-count tests). Hidden when the flag is off.
- `community_daily` (renamed from `community_recount`): counters + deletes notifications older than 90 days.
- Export: `community.notifications` (kind, address, dates; not the other person's text or name).
- Stickers: 32 original SVGs in `static/stickers/` (96×96, paper plate with ink ring, apricot "glove" tone, brand
  terracotta/green), shown as `<img>` with the translated label as alt; a retired key renders nothing. Sheet on
  `/styleguide/#stickers`. Tests: manifest = files, safe-SVG allowlist (no script/links/style/external), labels in
  every language, one sticker per reply even if two are posted, unknown key refused by the service too.
- Not done here (2b): picker UI, composer, image grids and lightbox, `blob:` preview, community CSS.
- To do in stage 3: DATA_INVENTORY / Privacy for notifications and `community_notified_at`.

## Stage 2b (done)
Started from a draft that an earlier session wrote without a GO (kept in `stash@{0}`, not dropped); reviewed, adopted,
fixed and tested. Commits: pages and layout, composer and picker, lightbox, UI tests.
- Pages: three columns on the feed layout (boards / content / rules panel; the boards fold above the content on phones),
  `static/css/pages/community.css` (tokens only, light and dark), thread cards with a thumbnail, nested replies with
  collapse (button shown by JS only), sort tabs, search, Previous/Next links + "Load more" (JSON `{html, next_url}`),
  `/community/rules/` from `content/<lang>/community-rules.md` (English only for now).
- Votes: plain POST form; `community.js` makes it optimistic and rolls back on any error. "Reply" moves the composer
  under the reply (`?reply_to=<id>` works without JS).
- Composer (`composer.js`): drag and drop, paste, previews (`blob:`), remove per file, hints for type/size/count (the server
  still checks everything). Sticker picker: popover, bottom sheet on phones, search by label (and key), recent in
  localStorage, arrow keys, Escape. Without JS: file input and a `<select>` with the same stickers.
- Grids `.media-grid--1..4`: `aspect-ratio` + `object-fit: cover`, `width`/`height` from the stored file, `srcset`, lazy;
  single wide / tall / tiny images get their own classes. Lightbox (`lightbox.js`, native `<dialog>`): Escape, arrows,
  swipe, backdrop click, focus returns to the tile; tiles are plain links without JS.
- CSP: `blob:` is added to `img-src` only on responses of the composer pages for signed-in users
  (`views.allow_blob_previews`); every other page keeps the site policy (tested).
- Motion (transform and opacity only, `prefers-reduced-motion: no-preference` only): staggered entrances, vote tick,
  sticker pop, collapse open, composer focus, sheet slide.
- Tests: 50 new in `community/test_ui.py` (shell, boards, search escaping, Load more JSON, grids with 1-4 images and odd
  sizes, lightbox markup, picker and sticker validation, CSP, who sees which control, translations render).
- Fix on the way: first-page links no longer carry `page=1`.
- Still open for stage 3: seed_community, post_welcome, rules in 6 more languages (`content/<lang>/community-rules.md`),
  Terms/Privacy/DATA_INVENTORY, DEPLOY_NOTES, `check --deploy`, TERMS_VERSION. Not yet checked by eye at 360-1440 px in
  both themes (needs a browser).

## Open questions
- Reports about threads/replies stay listed in /mod/ while the flag is off (their detail page is a 404). OK?
- `community_daily` needs a cron line (daily) when Community ships; added to DEPLOY_NOTES in stage 3.

## Not touched in this round
- Footer and the badge component (another task owns them); `feed.css`; Explore; proof rules.

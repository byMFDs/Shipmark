# Features status (branch `features-1`)

Brief: `docs/promts/features_master.md`. Plan: `docs/FEATURES_PLAN.md`.

## Stages
Order confirmed by the developer (2026-11-12): 2, 3, 4, 5, 6. Stage 2 is not postponed.

| # | Stage | Status |
|---|---|---|
| 0 | Plan | done 2026-11-12 |
| 1 | Foundations: I (screenshots bug, first), A, B models/admin, Sanction model/admin | done 2026-11-12 |
| 2 | Moderation: C | done 2026-11-12 |
| 3 | Profiles: D | done 2026-11-12, waiting for "GO 4" |
| 4 | Feed and news pages: E, public B | not started |
| 5 | Design pass, buttons, effect, motion, copy: F, G | not started |
| 6 | Leftovers, docs, legal, final tests: H | not started |

## Decisions (proposed in the plan, change if the developer disagrees)
- Roles from one module `accounts/roles.py`; `can_moderate` = moderator badge or superuser, never `is_staff`.
- News lives in a new app `news`; public byline is always the system account "shipmark".
- Sanction expiry is computed per request; the active sanction is cached on the request.
- Profile tabs use `?tab=` (a path like `/u/<user>/log/` would collide with project slugs).
- "For you" score: likes, capped owner followers, hallmark count, Case/When recency buckets (portable SQL);
  SQL hallmark count has a parity test against `compute_hallmarks`.
- Explore stays; feed and explore share one filter parser. Not merged without approval.

## Stage 1 (done)
- I: cause = separate "Upload screenshot" form; Save/Publish never sent the file (dev DB had 0 screenshot rows,
  no `media/screenshots/`). Media serving, templates, pipeline and publish were fine. Fix: files in the main form,
  Publish button belongs to it (`form="project-form"`), thumbnails with Move/Remove via `form=` buttons, per-file errors.
- A: `UserBadge` (official/moderator), `accounts/roles.py` (can_moderate = moderator badge or superuser),
  `accounts/badges.py` (grant/revoke + AuditLog), admin inline + "Badges" list (superuser writes, staff reads),
  `grant_badge` command, reserved usernames, official-looking display names blocked (NFKC, case, punctuation),
  system account `shipmark` (migration, inactive, unusable password, official badge), marks next to names
  (profile, project page, feed, explore, landing, account menu), badges prefetched on lists.
- B: `news` app, `NewsPost` + admin (Django model permissions: superuser or staff with news.* perms), AuditLog.
- Sanction model + admin (superuser issues/changes/revokes, never deleted; staff read-only), `moderation/sanctions.py`.
- Extra (security): non-superuser staff can no longer edit is_staff/is_superuser/groups/permissions in the user admin
  (otherwise they could make themselves superuser and reach badges).

## Stage 2 (done)
- Report: statuses open / in review / resolved / dismissed, resolution note, `log_entry` target, `target_owner`,
  `source` (user / moderator). Reports on projects, profiles and build-log entries (`/report/log/...`).
- `/mod/` (moderator badge or superuser, 404 otherwise): queue with counts and filters, report detail with the
  object and the owner's history, one action form (reason required, shown to the person). Open count in the account menu.
- Decisions (`moderation/decisions.py`): dismiss, remove project (status `removed`, owner sees the reason),
  clear profile fields, mute, ban; restore and purge are superuser-only admin actions. All in AuditLog.
- Limits in settings: `MODERATION_MAX_MUTE` 7 days, `MODERATION_MAX_BAN` 14 days, `MODERATION_ACTIONS_PER_HOUR` 30.
  Permanent only for superusers. Moderators never act on superusers, official accounts, moderators, themselves.
- Enforcement: `accounts.roles.can_write` everywhere a user writes (mute blocks; settings, export, delete,
  unpublish and deleting own projects stay open). `BanMiddleware` ends the session and shows the ban page;
  GitHub sign-in of a banned account or a banned GitHub id is refused with the same page. Expiry per request.
- Ban evasion: `BannedIdentity` = HMAC-SHA256 of the GitHub id keyed from SECRET_KEY (+ fallbacks), kept only
  until the ban ends or is revoked; `prune_bans` daily. Documented in privacy, terms (7 languages), DATA_INVENTORY.
- In-app `Notice` for decisions (never names the reporter); mute banner; export includes sanctions and notices.
- "Moderate" menu on project pages, profiles, feed and list rows, log entries; acting links the newest open report
  or creates one in the moderator's name.

## Stage 3 (done)
- `User`: `headline`, `about` (≤1000 markdown), `location`, `status`, `skills` (M2M `Tag`, ≤10), `avatar`, `avatar_source`,
  `cover`; `ProfileLink` (≤6), `PinnedProject` (≤3). Migration 0006 copies `bio` to `about` and `website` to a website link;
  the old columns stay (deprecated, `editable=False`) until a cleanup migration. Tested on a DB copy (forward, back, forward).
- Pictures: one pipeline (`projects.images.clean_image`: checked, centre-cropped to 512×512 / 1500×500, WebP, no metadata,
  random names). "Use my GitHub picture" downloads once through `safe_fetch` from `avatars.githubusercontent.com` only.
  Files are deleted on replace, remove, moderation clear and account deletion (`accounts/avatars.py`, `accounts/signals.py`).
- Links: http(s) only, no passwords; GitHub / X / LinkedIn / Telegram must point to their own sites (`accounts/links.py`).
- Profile page: cover, avatar, marks, headline, status, location, links, stats, pinned, tabs Projects / Build log / About
  (built-with summary labelled self-declared), inviting empty states, picture as the social preview image.
- Settings: one form with grouped sections and a live preview card; data export has the new fields; moderators' "clear
  profile fields" now means picture and cover / headline and About / links.
- Muted users can edit profile text but not upload pictures (uploads are on the mute list). Rate limits: 20 picture
  uploads and 5 GitHub downloads per hour per user.

## Decisions taken without answers (plan section 6, change if needed)
- `is_suspended` kept as it is (admin-level; suspended owners also cannot delete or unpublish projects).
- Publicly, a ban hides the person like a suspension: profile and projects 404, left out of every list and badge.
- A ban signs the person out; export or deletion during a ban go through the contact email (shown on the ban page).
- Skills reuse the shared `Tag` words (plan question 3). Explore: decided in stage 4.
- "About" on a profile has its own translation context ("Про себе"), separate from the site's About page.
- System account is excluded from the dashboard user counts.

## Open questions
- Plan section 6, questions 1-10: still open.
- Plan question 8 changed: banned users cannot export or delete in the app (they are signed out); OK?
- Public privacy/terms/cookies texts for the new personal data (avatar, location, links, status) are written in stage 6
  (DATA_INVENTORY is already updated).
- Muted users may still edit profile text (headline, About, links). Should a mute also freeze those? (Brief says "use own
  settings", so I left it; moderators can clear the fields.)
- Reports on build-log entries can lead to removing the whole project, mute or ban; there is no "remove one entry"
  action yet (not in the brief).

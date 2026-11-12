# Features status (branch `features-1`)

Brief: `docs/promts/features_master.md`. Plan: `docs/FEATURES_PLAN.md`.

## Stages
Order confirmed by the developer (2026-11-12): 2, 3, 4, 5, 6. Stage 2 is not postponed.

| # | Stage | Status |
|---|---|---|
| 0 | Plan | done 2026-11-12 |
| 1 | Foundations: I (screenshots bug, first), A, B models/admin, Sanction model/admin | done 2026-11-12 |
| 2 | Moderation: C | done 2026-11-12, waiting for "GO 3" |
| 3 | Profiles: D | not started |
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

## Decisions taken without answers (plan section 6, change if needed)
- `is_suspended` kept as it is (admin-level; suspended owners also cannot delete or unpublish projects).
- Publicly, a ban hides the person like a suspension: profile and projects 404, left out of every list and badge.
- A ban signs the person out; export or deletion during a ban go through the contact email (shown on the ban page).
- bio/about, skills, Explore: decided in their stages, defaults from the plan.
- System account is excluded from the dashboard user counts.

## Open questions
- Plan section 6, questions 1-10: still open.
- Plan question 8 changed: banned users cannot export or delete in the app (they are signed out); OK?
- Reports on build-log entries can lead to removing the whole project, mute or ban; there is no "remove one entry"
  action yet (not in the brief).

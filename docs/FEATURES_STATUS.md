# Features status (branch `features-1`)

Brief: `docs/promts/features_master.md`. Plan: `docs/FEATURES_PLAN.md`.

## Stages
| # | Stage | Status |
|---|---|---|
| 0 | Plan | done 2026-11-12 |
| 1 | Foundations: I (screenshots bug, first), A, B models/admin, Sanction model/admin | done 2026-11-12, waiting for "GO 2" |
| 2 | Moderation: C | not started |
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

## Decisions taken without answers (plan section 6, change if needed)
- `is_suspended` kept as it is; bio/about, skills, limits, Explore: decided in their stages, defaults from the plan.
- System account is excluded from the dashboard user counts.

## Open questions
- Plan section 6, questions 1-10: still open.
- New: a banned user can delete the account and sign up again with the same GitHub account (sanctions cascade
  with the user). Proposal for stage 2: on deletion with an active ban keep only a hash of the GitHub id until it ends.

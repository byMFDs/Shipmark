# Features status (branch `features-1`)

Brief: `docs/promts/features_master.md`. Plan: `docs/FEATURES_PLAN.md`.

## Stages
| # | Stage | Status |
|---|---|---|
| 0 | Plan | done 2026-11-12, waiting for "GO 1" |
| 1 | Foundations: I (screenshots bug, first), A, B models/admin, Sanction model/admin | not started |
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

## Open questions
See `docs/FEATURES_PLAN.md` section 6 (10 questions).

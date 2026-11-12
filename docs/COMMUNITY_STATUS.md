# Community status (branch `community-1`)

Brief: community master brief (kept by the developer in `docs/promts/`, not in git). Plan: `docs/COMMUNITY_PLAN.md`.

## Stages

| # | Stage | Status |
|---|---|---|
| 0 | Plan | done 2026-11-12, waiting for answers to the open questions |
| 1 | Backend: data, permissions and abuse limits, flag, moderation integration, admin, abuse-case tests, minimal UI | not started |
| 2 | UI: stickers, images, pages | not started |
| 3 | Polish: design and motion, legal, docs, full tests, `check --deploy` | not started |

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

## Open questions
- Plan section 13, questions 1-10: all open. Questions 2, 3, 4, 5 and 9 affect stage 1.

## Not touched in this round
- Footer and the badge component (another task owns them); `feed.css`; Explore; proof rules.

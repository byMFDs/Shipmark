# Polish-3 status

Branch `polish-3` (from `polish-2`). Brief: one stage per "GO <n>". Order: 0, 1, 7, 2, 3a, 3b, 4, 5, 6.

| Stage | State | Commit |
|---|---|---|
| 0. Community template leak | done 2026-11-13 | Fix community template leak |
| 1. Names and copy | waiting for "GO 1" | |
| 7. People search | after stage 1 | |
| 2. Button glow | | |
| 3a/3b. Design pass | | |
| 4. Motion | | |
| 5. Support email + bug sweep | | |
| 6. Code comments (only on "GO 6") | | |

## Stage 0 notes

- Cause: community views passed a context variable named `block` (the reason a member may not post).
  Inside `{% block %}` Django puts its own `block` (the current BlockNode, for `block.super`) on top of the
  context, so `{% if block %}` was always true and `{{ block }}` printed the node tree. Affected: new thread,
  edit thread, edit reply, and the thread page for anyone who could not reply (locked thread, muted member).
  Muted members never saw their real reason. Renamed to `post_block_reason`.
- The multi-line `{# #}` comments in the five community partials were already fixed in `3ea37f4`.
- Safeguards: `pages/test_leaks.py` (marker check on main pages and error pages; source checks: no template
  reads a bare `block`, no multi-line `{# #}` anywhere), `community/test_templates.py::CommunityLeakTests`
  (every community page for anonymous, member, author, muted, moderator, superuser; empty states).

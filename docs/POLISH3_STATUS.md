# Polish-3 status

Branch `polish-3` (from `polish-2`). Brief: one stage per "GO <n>". Order: 0, 1, 7, 2, 3a, 3b, 4, 5, 6.

| Stage | State | Commit |
|---|---|---|
| 0. Community template leak | done 2026-11-13 | Fix community template leak |
| 1. Names and copy | done 2026-11-14 | Header: fit long languages · Names: For You, Discover · Copy: plain words in every language · Forms: translate field labels · Legal: easier to read |
| 7. People search | done 2026-11-14 | People search |
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

## Stage 1 notes

- 1a: "Feed" → "For You" (nav, footer) / "For You Page" (title); inner tab "For you" → "Recommended";
  "Explore" → "Discover" (uk «Пошук»). URLs unchanged. Glossary in EDITING.md, before/after in POLISH3_COPY.md.
- Found while checking 1a: the open header bar overflowed at 768 and 1024 px in de/fr (pre-existing). Fixed in
  its own commit: menu below 80em, the tagline hides itself when it does not fit. Checked in headless Firefox.
- 1b: all 1146 strings read; ~25 English strings plainer, 9 admin "(s)" messages → ngettext, delete-account
  page matched to the code, uk/de glossary and form-of-address fixes. Real bug in its own commit with a test:
  project and settings forms showed English field labels in every language.
- 1c: Privacy (5 passages) and Terms (3) as lists and shorter sentences, same facts, all 7 languages; Cookies and
  Community rules unchanged. TERMS_VERSION not bumped. Every change in POLISH3_LEGAL_CHANGES.md.
- Not done: native-speaker review of all non-English text; lawyer review of the legal drafts.

## Stage 7 notes

- Discover has tabs Projects / People (`/explore/?tab=people`); the project search is unchanged. Header: a search
  icon from 80em, a search field at the top of the menu below that.
- Rules and numbers in `accounts/people.py`: username only, prefix first, min 2 chars, 20 per page, characters a
  username cannot have match nobody, hidden accounts excluded, rate limit 60 / 10 min per account and 30 / 10 min per
  salted IP hash for anonymous visitors. Constant queries (tested). Privacy + DATA_INVENTORY say what is stored.
- Not tested on PostgreSQL (no local server running); lookups are Django's istartswith/icontains, which escape
  % and _ on both engines.

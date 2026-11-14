# Polish-3 status

Branch `polish-3` (from `polish-2`). Brief: one stage per "GO <n>". Order: 0, 1, 7, 2, 3a, 3b, 4, 5, 6.

| Stage | State | Commit |
|---|---|---|
| 0. Community template leak | done 2026-11-13 | Fix community template leak |
| 1. Names and copy | done 2026-11-14 | Header: fit long languages · Names: For You, Discover · Copy: plain words in every language · Forms: translate field labels · Legal: easier to read |
| 7. People search | done 2026-11-14 | People search |
| 2. Button glow | done 2026-11-14 | Halo: visible on the light theme |
| 3a/3b. Design pass | done 2026-11-14 | Design audit (3a) · Layout fixes from the design audit · One spacing and icon scale · Dark theme: three levels, visible hairlines · Design: add and remove |
| 4. Motion | done 2026-11-14 | Motion: tab marks, theme fade, reading progress |
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

## Stage 2 notes

- Cause: on hover the secondary ring turned ink (`--btn-edge: var(--text)`), so the ink light ran over an ink ring;
  the primary ring ran paper white on the paper page. Now the ring keeps its resting colour and the light is
  `--text` + one accent spark in both themes. Measured >= 3:1 (table in DESIGN.md); `pages/test_halo.py` reads
  tokens.css and fails if a token change makes the ring too faint.
- Kept: hover/focus/loading only, idle turn on the hero only, static ring with reduced motion, forced-colours border.
- Buttons: heights, radius and icon gaps already consistent; the file input's "Browse" button got the button radius.
- Not changed (listed for 3a): `.composer__preview .btn` (32px remove button on image previews) and
  `.reply__collapse` (36px, and a duplicate `padding`) are below the 44px tap target.

## Stage 3b notes

- Done as planned in POLISH3_DESIGN.md, sections 1-4. One correction to the audit: `.reply__collapse` already had a 44px
  target on touch screens and no duplicate padding (my grep had joined two rules); unchanged.
- Dark theme: new values and `--raised`; `pages/test_tokens.py` checks AA for every pair, the two dark blocks, the
  styleguide table. Logo SVGs and stickers keep their own colours (identity, separate files).
- Not checked: real Safari/Chrome, 390px separately (same breakpoints as 360).

## Stage 4 plan: motion

Rules kept: transform and opacity only, at most 3 loops visible, loops pause offscreen and in hidden tabs, no layout
shift, no scroll-jacking, reduced motion = the finished static state (`base.css`), nothing blocks a click.
New animations (no new loop; JS only where the change itself comes from JS):

| # | Where | What | Cost |
|---|---|---|---|
| 1 | Header nav, tabs on Discover, For You, profile, /mod/ | Page to page: the current-tab mark slides to the new tab (cross-document view transition, named group per tab row, 240 ms) while the page cross-fades. Chrome/Edge 126+, Safari 18.2+; elsewhere a normal navigation | ~1 KB CSS, one `<span aria-hidden>` in the current link |
| 2 | Theme switch (footer) | The page cross-fades to the new theme (same-document view transition, 180 ms) instead of snapping | ~0.3 KB JS |
| 3 | Legal and content pages, news posts | A 2px reading hairline at the top grows with the scroll (scroll-driven animation, CSS only); hidden where unsupported and with reduced motion | ~0.4 KB CSS |
| 4 | Disclosures: hallmark explanation, DNS/meta help, feed filters, community boards on phones | The opened content fades in and rises 4px (160 ms) | ~0.2 KB CSS |
| 5 | Build log | A just-posted entry rises into the list (320 ms) | ~0.2 KB CSS + 1 line JS |
| 6 | Domain verification ("Verify now") | The new status block rises in place (260 ms) | ~0.1 KB CSS + 2 lines JS |
| 7 | Header "new replies" dot | Set down once on load (scale, 320 ms) | ~0.1 KB CSS |

Existing motion is unchanged (list in DESIGN.md, Motion). Loop budget per page: landing 3 (shimmer, pulse, tick; the
closing cursor is never on screen with them), project page 1 (uptime tick), everywhere else 0; a hovered/focused halo
and a busy spinner are answers to the person. Styleguide (DEBUG only) shows the loops side by side on purpose; its
dead "drift" sample (no CSS since the drift was removed) goes.
Guard: `pages/test_motion.py` reads every CSS file: keyframes may only animate transform/opacity, `@view-transition`
only inside `prefers-reduced-motion: no-preference`, infinite animations only on the known loops.

## Stage 4 notes

- All 7 done as planned. Cost: CSS +3.8 KB raw / +1.2 KB gzip (half of it comments), JS +0.6 KB raw / +0.3 KB gzip;
  no new file, no new request. Core CSS now 85 KB raw / 21 KB gzip.
- Tab underlines are now an element (`.tab-mark`) instead of a box-shadow / border / ::after; same place and look.
- A view transition blocks clicks for its 180-240 ms (browser behaviour), the same as the existing page cross-fade.
- Not checked in a real browser (no dev server in this session): the slide of the marks (Chrome/Edge 126+, Safari
  18.2+), the reading hairline (Chrome 115+, Safari 26; Firefox shows nothing), the theme fade.
- Seen: `manage.py test --parallel` crashes with "cannot pickle 'traceback' object"; the serial run is green. Left for stage 5.

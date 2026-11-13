# Design system (values live in `static/css/tokens.css`)

A public record of shipped work: each project is a framed record, and proof is a flat mark on it.
Warm paper, hairline frames, square corners (buttons excepted), one action color. Rules:
- Depth comes from surface color (paper < surface) and hairlines. No bevels, gradients, glow or tinted
  sections; the only shadow is `--shadow-pop`, on floating menus and toasts. One gradient on purpose: the halo ring on a few
  buttons (Components). Records, panels, fields and marks are square; buttons have 10px corners (they are pressed, records
  are not); people (avatars) are round.
- Terracotta (`--accent`) is the one action color: the primary button, nothing else.
  Green (`--proof`) means proof only: earned marks, the uptime strip, "public" status.
  Danger red is for errors and destructive actions only.
- Mono uppercase labels (12px, tracked) name things: record headers, meta lines, eyebrows.
  Headlines are Manrope, body is Inter. Text is left-aligned.
- Motion answers an action, or marks a fact appearing (see Motion). No hover lifts.

## Color (light / dark)
Dark theme is used by the toggle, by the OS setting, and always inside `.band`. Both blocks in
`tokens.css` must stay in sync (three places: light, `[data-theme="dark"]` + `.band`, and the `prefers-color-scheme` block).
There are no legacy token aliases any more; use the names in the table below.

### Measured contrast (WCAG 2.x; AA = 4.5:1 text, 3:1 large text and UI). Token pairs rechecked 2026-11-14 (Polish-3 3b, new dark theme); `pages/test_tokens.py` recomputes them from `tokens.css` on every test run.
Recheck after any token change; every pair below must stay at or above its minimum. Two checks: the token pairs below
(computed from `tokens.css`), and every text node on 13 signed-in/public pages x 360/390/768/1440 px x light/dark in
Firefox (computed color over the real background chain): 0 failures. Disabled controls are exempt (WCAG 1.4.3).

| Pair (text / background) | Light | Dark | Min | Where |
|---|---|---|---|---|
| `--text` / `--paper` | 14.04 | 14.93 | 4.5 | body text |
| `--text` / `--surface` | 15.46 | 13.04 | 4.5 | cards, panels |
| `--text` / `--raised` | 15.46 | 11.63 | 4.5 | fields, menus, toasts |
| `--text` / `--tint` over paper | 12.81 | 12.78 | 4.5 | quiet button hover |
| `--muted` / `--paper` | 5.57 | 7.99 | 4.5 | secondary text |
| `--muted` / `--surface` | 6.14 | 6.98 | 4.5 | secondary text on cards |
| `--muted` / `--raised` | 6.14 | 6.23 | 4.5 | placeholders, menu notes |
| `--muted` / `--tint` over paper | 5.08 | 6.84 | 4.5 | disabled-field text, quiet hover |
| `--muted` / `--proof-bg` | 5.06 | 5.44 | 4.5 | muted text on a proof note |
| `--accent-text` / `--paper` | 5.29 | 7.74 | 4.5 | accent words, labels |
| `--accent-text` / `--surface` | 5.82 | 6.76 | 4.5 | accent words on cards |
| `--on-accent` / `--accent` | 4.96 | 6.41 | 4.5 | primary button |
| `--on-accent` / `--accent-hover` | 6.50 | 8.45 | 4.5 | primary button, hover |
| `--proof` / `--proof-bg` | 6.51 | 7.58 | 4.5 | hallmark chip, proof note |
| `--danger` / `--paper` | 5.98 | 7.88 | 4.5 | error text |
| `--danger` / `--surface` | 6.59 | 6.88 | 4.5 | error text on cards |
| `--danger` / `--raised` | 6.59 | 6.14 | 4.5 | danger item in a menu |
| `--danger` / `--danger-tint` over paper | 5.32 | 6.80 | 4.5 | danger button hover |
| `--on-danger` / `--danger` | 6.59 | 7.88 | 4.5 | solid danger button |
| `--on-danger` / `--danger-hover` | 8.49 | 8.93 | 4.5 | solid danger button, hover |
| `--paper` / `--text` | 14.04 | 14.93 | 4.5 | inverted: chosen theme option, skip link |
| `--line-strong` / `--paper` | 3.17 | 4.45 | 3 | UI: input and control borders |
| `--line-strong` / `--surface` | 3.49 | 3.89 | 3 | UI: borders on cards |
| `--line-strong` / `--raised` | 3.49 | 3.47 | 3 | UI: field borders, checkbox edges |
| `--accent` / `--paper` | 4.50 | 6.41 | 3 | UI: primary button edge |
| `--accent` / `--surface` | 4.96 | 5.60 | 3 | UI: primary button edge on cards |
| `--focus` / `--paper` | 14.04 | 14.93 | 3 | UI: focus ring |
| `--focus` / `--raised` | 15.46 | 11.63 | 3 | UI: focus ring on fields |
| `--proof` / `--surface` | 7.89 | 9.72 | 3 | UI: tick strip cells |
| `--surface` / `--paper` | 1.10 | 1.14 | none | depth: cards off the page |
| `--raised` / `--surface` | 1.00 | 1.12 | none | depth: fields and menus off a card |
| `--line` / `--paper` | 1.29 | 1.69 | none | dividers (decorative, never a control edge) |
| `--line` / `--surface` | 1.42 | 1.48 | none | dividers on cards |

Decorative exception: the landing specimen's tick strip is `aria-hidden` and illustrative; its cells are 55% proof green
(2.67:1 light on the record surface). The real uptime strip on project pages uses full `--proof` (7.89 / 9.72).

`.band` (dark strip; dark tokens on `--band-bg` #212721 in the light page / #0D1310 in the dark page):
text 12.65 / 15.59 · muted 6.77 / 8.34 · accent-text 6.56 / 8.08 · accent edge 5.43 / 6.69 ·
line-strong 3.77 / 4.64 · focus 12.65 / 15.59. The primary button inside a band is the dark one.

**Dark primary button.** `#EE7A3B` (Polish-3: a little deeper than `#F5803F`, so large fills glare less) with dark
text `#121815` (6.41:1), hover `#FA9A63` (8.45:1). White text on any light orange fails (about 2.6:1), so in dark the
label is always dark. In light it stays white on `#BD4B27`.

**Dark theme, Polish-3 3b.** Three levels without shadows: page `--paper` #121815 → cards and panels `--surface`
#1C2521 (1.14:1 on the page, was 1.10) → fields, menus, popovers and toasts `--raised` #242E29 (1.12:1 on a card;
in the light theme `--raised` = `--surface`, hairlines give the depth there). Hairlines `--line` #35413B (1.48:1 on a
card, was 1.27), control edges `--line-strong` #76817A. The tone stays green-black; text #ECEAE1 is a touch softer
(less glare). Before/after is on /styleguide/ ("Dark theme: before / after").

## Type
- Manrope (variable 200-800; headlines, weight 500, tracking -0.03em) · Inter (variable; body and UI) ·
  IBM Plex Mono 400 (labels, code, numbers in records). Self-hosted woff2 (Latin, Latin-ext, Cyrillic by
  `unicode-range`), licences in `static/fonts/OFL.txt`. Fallbacks: local Arial / Liberation Sans scaled to
  each font's metrics (`size-adjust`), so swapping causes no layout shift.
- Root 100% (16px), 106.25% (17px) from 64em. Sizes in rem. Scale 1.25: fs--2 .75rem (mono labels, the
  smallest text) · fs--1 .8125 · fs-0 1 · fs-1 1.25 · fs-2 1.563 · fs-3 1.953 · fs-4 2.441 · fs-5 3.052 ·
  fs-6 3.815 · `--fs-hero` clamp(2.75rem, 5.6vw + 1.4rem, 5.5rem) (landing only).
- Body line-height 1.55, max line 68ch. h1-h2 line-height 1.05; `.lede` 1.25rem muted, max 52ch.
- Headlines hyphenate (`hyphens: auto`) so German and Polish never widen a 360px phone; reading text
  (`.doc`) does not in en and uk.

## Space, radii, depth
- Space (4px base): s-1 .25rem ... s-9 6rem. Radius 0 (`--radius`), buttons 10px (`--radius-btn`, changed 2026-11-12 in the
  features round). Focus: 2px `--focus` outline, offset 2px (3px on buttons; the outline follows the rounded corners).
- Frames: 1px `--line` hairline; control edges use `--line-strong` (3:1). Press: buttons scale .98.
- **One spacing scale** (Polish-3 3b): margins, paddings and gaps use `--s-1`...`--s-9` only. Rhythm: between page
  sections `--s-7`, between panels `--s-5`, inside a panel `--s-4`, label to field `--s-2`. Named exceptions as tokens:
  `--btn-pad` 1.25rem / `--btn-pad-lg`, `--chip-pad` .625rem, the 9px field padding that centres text in a 44px control,
  hairline geometry in px (uptime cells, 1px overlaps), and em spacing inside running text.
- **One icon scale:** `--icon-s` 16px (meta lines, small controls, chevrons), `--icon-m` 20px (buttons, menus; the
  default `.icon`), `--icon-l` 24px (empty states). Inside a mono chip an icon follows the chip text (1.1em). The text
  arrow after a link label (`.arrow`) is 14px on purpose: it belongs to the words, not to the control.
- **Alignment rules:** text left-aligned; icon + label = `inline-flex`, centred, gap `--s-2`; numbers `tabular-nums`;
  in a row with 1-2 lines of text the avatar and the action are centred, with 3+ lines they sit at the top; a card's
  actions sit at its bottom; a name and its badges never break apart; tab labels never break inside a word.

## Layout
- Content max 1200px; side padding max(1rem, safe-area inset) -> 1.5rem at 48em -> 2rem at 64em (`.container`).
- Page shell (`base.css`), used by every page except the landing: `<div class="container shell">`. Widths: default 1200px (feed,
  explore, profile, project, sheets, /mod/), `.shell--narrow` 46rem (legal and content pages, news, delete confirmation, ban page,
  errors), `.shell--card` 32rem (sign in/out, sign-up, accept terms, report form). Narrow widths are centred, so nothing hangs
  against the left edge; text inside stays left-aligned. The shell owns the space above (s-6, s-7 from 64em) and below (s-8 / s-9);
  page CSS does not add its own bottom padding.
- Header block: `.page-head` = optional mono eyebrow, h1, one lede, optional `.page-head__actions` (right of the text from 48em),
  closed by a hairline. Sheet pages use `.sheet__intro` in the left column instead.
- There is no global grid class. Pages that need columns declare them in their own CSS: 12 columns from 64em
  (project page, landing, `.sheet`), one column on phones.
- Project page: head across the top, then main (8: cover, about, build log) and proof column (4: marks,
  uptime, built with, tags, embed). On phones the order is head, cover, marks, about, log, facts, embed.
- Form pages (`.sheet`): title left (4), framed `.panel` sections right (8) from 64em, both reaching the container edges (the old
  46rem cap on the panels left an empty strip on the right); one column below.
- Owner bar on phones: one column, every button full width.
- Targets >= 44px (`--control-h`); on `pointer: fine` only chips, tag links and the theme switch may be smaller
  (theme switch is 44px on `pointer: coarse`). Inline links inside sentences are exempt (WCAG 2.5.8).

## Hallmark
- Flat chip: check glyph + mono label ("Repo owner", "Domain verified", "Steady"); names stay English in every language
  except Ukrainian (docs/EDITING.md). "Domain verified" was "Live" until 2026-11-12; the internal id is still `live`.
  Earned: `--proof-bg` fill, `--proof` text. Not earned: dashed `--line-strong` outline, muted, "Not yet".
- Sizes: S (lists, label may hide state) · M · L (project page: chip + one fact line, opens a panel).
- The first mark proves repository ownership (or 10+ commits), never who wrote the code. Internal id stays
  `authored`; only display text says "Repo owner".

## Components (`components.css`)
- Buttons (44px, `.btn--lg` 52px, `.btn--icon` 44px square; Inter 500; 10px corners): primary = accent fill (label dark in dark
  theme) · secondary = surface + `--line-strong` · quiet = text only · danger = danger outline, filled only on the final
  confirmation. Each variant sets `--btn-bg`, `--btn-fg`, `--btn-edge`; states change only those: hover (darker fill or ink edge),
  press (scale .98 + hover colour, also on touch), focus (2px ring, offset 3px), disabled (45% opacity, not-allowed), loading
  (`aria-busy` blocks clicks; `busy.js` adds `data-busy-ring` to the button that submitted a normal form: label transparent, a
  turning ring in its place, same size; cleared when the page comes back from the Back-button cache; data-export forms opt out
  with `data-no-busy`).
- Halo (`.btn--halo`): every "Sign in with GitHub" / "Continue with GitHub" button (header, login page, feed navigation, landing
  hero and closing action) plus "New project" (header) and "Publish project". An oversized conic gradient (`::before`, 200% of the
  width) turns behind the button with `transform: rotate` only, clipped by the rounded button; the fill (`::after`) sits 2px
  inside, so a 2px ring shows. The ring keeps its resting colour (`--halo-base`: `--line-strong`, or `--accent` on a primary
  button) also on hover; hover (mouse only), keyboard focus and loading run a light over it every 2.4 s. The light is `--text`
  (dark ink on the light theme, near-white on the dark one) with one spark (`--accent`; `--accent-hover` on a primary button).
  Polish-3 stage 2: before, hover turned the whole ring ink on the light theme (ink light on an ink ring, invisible) and the
  primary ring ran paper white on the paper page. `.btn--halo-idle` (the landing hero button only): a faint ring that turns once
  every 12 s while on screen. Reduced motion: the same ring, standing still, still lit on hover and focus. Forced colours: a plain
  1px border.

  Measured (every colour on the ring, blends between stops at 10% steps, against page and surface):

  | Theme / button | vs paper (min) | vs surface (min) | light vs resting ring |
  |---|---|---|---|
  | light, secondary (`#868A80` ring, `#20251F` light, `#BD4B27` spark) | 3.17:1 | 3.49:1 | 4.43:1 |
  | light, primary (`#BD4B27` ring, `#20251F` light, `#A13D1C` spark) | 4.50:1 | 4.96:1 | 3.12:1 |
  | dark, secondary (`#76817A` ring, `#ECEAE1` light, `#EE7A3B` spark) | 4.45:1 | 3.89:1 | 3.36:1 |
  | dark, primary (`#EE7A3B` ring, `#ECEAE1` light, `#FA9A63` spark) | 6.41:1 | 5.60:1 | 2.33:1 (plus a hue change) |

- Button shapes (checked in stage 2): every `.btn` is 44px (`.btn--lg` 52px, `.btn--icon` a 44px square), radius
  `--radius-btn`, icons 20px with an 8px gap, centred on the label. The file input's "Browse" button now has the same radius.
  The halo ring is 2px where other edges are 1px: on purpose, it marks the main action.
- Fields: surface, `--line-strong` border, >= 16px text, error = danger border + message with icon,
  `aria-invalid` + `aria-describedby`. Checkbox and radio: 20px control inside a 44px row. `.code-value` +
  `.btn--copy`: a literal value to paste.
- `.record` (frame + mono header row) is the base of the proof column, build log, embed panel, filters and
  the landing specimen. `.panel` is a framed form section (`--danger` = destructive). `.page-head`: h1 + lede.
- Lists: `.plate-row` (cover, name in Manrope, by-line, tagline, marks) · `.card` (landing) · `.chip` (tags).
- Header: not sticky, hairline under, mobile menu is `<details>`. "<n> people joined" (`.site-count`, `pages/stats.py`): a quiet
  fact (mono number, muted words, `title` "Registered accounts"), in the bar from 48em and next to the tagline from 64em, inside
  the phone menu below 48em. Registered accounts, not people online: no live dot, no pulse.
- Footer (`site_footer.html`): one 12-column grid. Brand block (logo, `SITE_DOMAIN`, tagline) and three link columns (Product,
  Company, Legal; mono headings) take 3 each from 64em; brand across + three columns of 4 from 48em; brand + two columns on phones.
  Bottom bar: copyright in sentence case from `LEGAL_OWNER_NAME` (left), language and theme (right, full width on phones). All three
  controls share `--footer-control-h` (44px, 52px on touch), `--radius-btn` and a `--line-strong` edge. The language select sends the
  form on change (`language.js`); without JS its "Change" button stays, joined to the select.
- Toast: surface + border, `role=status`, bottom. Empty state: dashed frame, three unstruck marks, one action.
- Error pages (`404.html`, `403.html` inside the site; `500.html`, `400.html`, `403_csrf.html` standalone, no DB or
  context processors; views in `config/errors.py`): big mono status code, headline, one sentence, one mark that fails to
  stamp, primary action (front page, or feed when signed in) + "Go back", "Reference: <request id>" on 500/403/CSRF.
  Previews at `/_dev/errors/<code>/` (DEBUG only). A quiet "Report a problem" opens `/support/?category=bug&ref=<request id>`.
- Support (`support/form.html`, `support/sent.html`, `pages/support.css`): a `.sheet` (intro + "What happens next" record on
  the left; "What to write" panel and the form on the right). The sent page is a small record that gets a "Received" stamp in
  ink (never green: it is not proof).
- Tabs: plain links with `aria-current`; active = text color + 2px bar.
- Profile (`accounts/profile.html`, `profile.css`): one framed card (`.profile-card`): optional 3:1 cover, 128px round avatar
  (overlaps the cover), name + marks, mono handle, headline, a flat `.status-chip` (neutral outline, never proof green or the
  action colour: it is the person's own statement), location and join date, links with own inline icons (`globe`, `github`, `x`,
  `linkedin`, `telegram`, `link`), actions. Then stats, pinned projects, tabs (`?tab=projects|log|about`, plain links with
  `aria-current`). Avatars are always local files (`{% user_avatar user size %}`), initials when there is none.
- Settings (`settings.html`): one multipart form in grouped `.panel` sections (picture and cover, about you, links, pinned
  projects, language); the left column holds a live preview card (`profile-preview.js`, copies text only; a chosen image is read
  in the browser as a data: URL, so the CSP is unchanged).
- Feed (`social/feed.html`, `feed.css`): a 12-line grid is not used; the page declares its columns: 1 on phones (tabs `position:
  sticky`, filters folded in a `<details>`), `1fr 17rem` from 48em, `1fr 37.5rem 1fr` from 72em (navigation, 640px feed, panel;
  equal sides: navigation and panel are both 16rem and sit on the outer edges). `.feed-card`: frame + hairline, no shadow; cover 16:10 from the thumbnail, head (avatar, name + marks, handle,
  time, follow), name in Manrope, tagline, marks, the latest update with a 2px rule (3 lines max), actions. `.empty--plain` is an
  empty state without the dashed frame. News cards (`.news-card`) share the same frame.
- Badges after a name (`{% user_marks person [size] %}`, `.user-mark`, one component for every kind): a glyph button about the
  name's x-height (`s` 0.8em in dense lists, `m` 0.85em, `l` 0.7em next to a big heading; min 14px; the hit area grows invisibly).
  Official = filled ink diamond with the logo's slash cut; moderator = muted ink shield with a bar. No colour of their own (not
  proof, not an action). Hover/focus: a mono tooltip with the label. Click/tap: one shared panel per page (`badge_popover.html`,
  `badges.js`): title, one sentence, "Affiliated with <SITE_NAME>" with the logo mark (official), "<Kind> since <date>" from the
  real `UserBadge.granted_at`, "How badges work" (`/how-proof-works/#badges`). A popover under the badge from 48em, a bottom sheet
  below. Escape, the close button and an outside click close it; focus returns to the badge. Lists prefetch `owner__badges`.

### Find people (stage 7)
Header from 80em: a search icon (`.site-search`, a `<details>`) opens a small form; below 80em the menu panel starts
with a plain search field. Both go to Discover → People (`/explore/?tab=people`). Result rows (`.person-row`): avatar 48,
name + badges, mono `@username`, headline, counts, then the action (Follow / "You" / "Sign in to follow"); on phones the
action sits under the text.

## Motion (`motion.css`, `motion.js`)
- Animations use transform and opacity only. Exception, on purpose: hover/focus colour and border-colour fades
  (120-200 ms, paint only, no layout). Nothing animates width, height, margin, top/left or font size.
- Loops run only while their block is on screen (`.is-inview`, IntersectionObserver) and stop in a hidden tab
  (`html.is-paused`, which also reaches `::before/::after`). At most 3 loops visible at once. These pause rules
  apply only when JS runs (`.js` is set in `<head>`); without JS nothing loops, nothing is hidden, and the strike
  shows its final state.
- Reduced motion: `base.css` turns off every animation and transition, so each element shows its final state;
  no reveal, no page transition, the tick head is hidden.
- Landing: strike (once), live pulse + uptime tick in the specimen and the idle shimmer on the hero sign-in button (3 loops,
  the maximum; the old specimen drift was removed to make room), closing cursor (far below the hero, never visible together
  with it), section reveal (once). A hovered or focused halo is an answer to the person, not an ambient loop.
- Inner pages (every `.shell`), once, CSS only, `animation-fill-mode: backwards` (nothing keeps a transform afterwards, clicks work
  during it): the shell's children rise 10px into place (60 ms apart); list items (`.feed-list`, `.plate-list`, `.news__list`,
  `.mod-list`) follow one after another (first 8, 50 ms apart; later ones and "Load more" together); the three dashed marks of an
  empty state are set down and the first is pressed once and does not take. Cards (`.feed-card`, `.news-card`, `.card`): the frame
  firms up to `--line-strong` and the cover scales 1.03 inside its frame on hover; a press on the card's own link pushes it to
  .995. Profile stats count up once when in view (`[data-count]`, motion.js; skipped with reduced motion; the HTML has the real
  number).
- Error pages: one mark comes down, does not take and lifts away (once, 1.3 s); the dashed "Not yet" mark stays.
- Chrome: the footer's blocks rise in one after another when it comes into view (`data-reveal`), a hairline grows under a
  hovered footer link, the theme fill slides to the chosen option; the badge panel opens with a 160 ms fade-and-rise (sheet:
  slides up); the header count counts up once on load (800 ms, over a hidden copy of the final text, so no layout shift);
  the support "Received" stamp is pressed once. All transform/opacity, all off with reduced motion.
- Project page: marks strike in order on load (300 / 650 / 1000 ms), one tick highlight over the 30 uptime
  cells (1 loop). Everywhere: hover, press and focus answers, like/follow pop, menu and toast fades, page
  cross-fade.
- Page cross-fade is `@view-transition` (180 ms) inside `prefers-reduced-motion: no-preference`. Browsers
  without view transitions ignore the rule and navigate normally; `view-transition-name: site-header` is
  harmless there.

## Performance
- Self-hosted woff2 only (Latin set per page ~88 KB: Inter 48, Manrope 25, Plex Mono 15; Cyrillic and Latin-ext
  load only when the text needs them, by `unicode-range`). Inter + Manrope Latin (and Cyrillic for `uk`) are
  preloaded. Fallback fonts are size-adjusted, so the swap does not move the layout.
- Core CSS per page (tokens, base, components, motion): 69 KB raw, 16 KB gzip (2026-11-12); one page file on top. Core JS
  (6 small ES modules, deferred by `type="module"`): 8.7 KB raw, 3.1 KB gzip. Only `theme-init.js` is blocking
  (it sets the theme and `.js` before first paint).
- Images carry width/height and `loading="lazy"` (the first project screenshot is not lazy). Production
  `collectstatic` hashes every file (`CompressedManifestStaticFilesStorage`).
- Dead CSS check: a class that no template, JS or Python file mentions is removed (dynamic names such as
  `avatar--{size}` and `is-{status}` are the exceptions; search before deleting).

## Accessibility
- Skip link first in the tab order (44px, shown on focus), one `<main id="main">`, one `h1` per page, headings
  in order (an empty state under the page title is an `h2`).
- Focus: 2px `--focus` outline, offset 2px, on every control. No positive `tabindex`.
- Menus are native `<details>` (work without JS; `menu.js` adds Escape and outside click). Tabs are plain links
  with `aria-current`. The theme switch is a group of buttons with `aria-pressed`. The language switch is a
  labelled `<select>` in a POST form; with JS it sends on change, without JS a "Change" button sends it. Badges are buttons
  (`aria-haspopup="dialog"`, `aria-expanded`, label = kind); the header count has a hidden sentence with the exact number. Toasts live in an `aria-live="polite"` region; errors use `role="alert"`.
- Form fields have visible labels, `aria-invalid` and `aria-describedby` for errors; a failed form shows an
  error summary that takes focus.
- Checked 2026-11-11 in Firefox at 360/390/768/1024/1440 px, light and dark, `uk` (and `de` at 360 for long
  words): no horizontal scroll. Not checked: real iOS/Android, screen readers.

## Badge (`projects/badges.py`)
Drawn in Python with fixed colors from the light tokens (plate, graphite, steel, line) and green for stamps and
the count. Square corners. Pairs measured 2026-11-11: plate/graphite 15.46, steel/plate 6.14, plate/proof 7.89,
white/proof 7.96, line/plate 3.49 (border).

## Logo
- Mark C, "struck slash": a square with a slash and a full stop cut out. Path
  `M0 0H32V32H0ZM4 26H12L22 6H14ZM20 18H28V26H20Z` (even-odd). Files: `logo.svg`, `logo-mark.svg`, `favicon.svg`,
  PNGs for the touch icon and OG image; `logo-dark.svg` and `logo-mark-dark.svg` are light copies for the dark
  admin. `favicon.ico` (16/32/48, opaque: dark square, paper slash and stop, readable on light and dark tab bars) and
  `apple-touch-icon.png` are drawn from `logo-mark.svg` by `manage.py make_icons`; `favicon.svg` switches to the light
  mark under `prefers-color-scheme: dark`. Icon links use `{% static_v %}` (content hash), so a new logo is a new URL. Options A and B live in `static/brand/options/` (styleguide only).
- Wordmark: lowercase "shipmark" in Manrope 700 as outlines. Header and footer inline the SVG so it follows the theme.
  `SITE_NAME` stays "Shipmark" (capitalised in running text and page titles); only the logo files and the OG image spell
  it lowercase. `SITE_DOMAIN = "shipmark.me"` is shown in the footer, badges and embed snippets. The OG image
  (`og-default.png`) has the headline and the three marks baked in, with "Repo owner" as the first mark.

## Admin
django-unfold, colors from the same palette (`UNFOLD["COLORS"]`: primary = terracotta, base = warm green-black),
radius 0, light/dark logo from `branding.py`. Nothing else is overridden.

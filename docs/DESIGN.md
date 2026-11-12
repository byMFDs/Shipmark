# Design system (values live in `static/css/tokens.css`)

A public record of shipped work: each project is a framed record, and proof is a flat mark on it.
Warm paper, hairline frames, square corners, one action color. Rules:
- Depth comes from surface color (paper < surface) and hairlines. No bevels, gradients, glow or tinted
  sections; the only shadow is `--shadow-pop`, on floating menus and toasts. Square corners everywhere; only people (avatars) are round.
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

### Measured contrast (WCAG 2.x; AA = 4.5:1 text, 3:1 large text and UI). Checked 2026-11-11 (phase 4b).
Recheck after any token change; every pair below must stay at or above its minimum. Two checks: the token pairs below
(computed from `tokens.css`), and every text node on 13 signed-in/public pages x 360/390/768/1440 px x light/dark in
Firefox (computed color over the real background chain): 0 failures. Disabled controls are exempt (WCAG 1.4.3).

| Pair (text / background) | Light | Dark | Min | Where |
|---|---|---|---|---|
| `--text` / `--paper` | 14.04 | 15.05 | 4.5 | body text |
| `--text` / `--surface` | 15.46 | 13.70 | 4.5 | cards, inputs |
| `--text` / `--tint` over paper | 12.81 | 12.80 | 4.5 | quiet button hover |
| `--muted` / `--paper` | 5.57 | 7.40 | 4.5 | secondary text |
| `--muted` / `--surface` | 6.14 | 6.73 | 4.5 | secondary text on cards, placeholders |
| `--muted` / `--tint` over paper | 5.08 | 6.31 | 4.5 | disabled-field text, quiet hover |
| `--muted` / `--proof-bg` | 5.06 | 5.40 | 4.5 | muted text on a proof note |
| `--accent-text` / `--paper` | 5.29 | 7.26 | 4.5 | accent words, labels |
| `--accent-text` / `--surface` | 5.82 | 6.61 | 4.5 | accent words on cards |
| `--on-accent` / `--accent` | 4.96 | **6.76** | 4.5 | primary button |
| `--on-accent` / `--accent-hover` | 6.50 | **8.29** | 4.5 | primary button, hover |
| `--proof` / `--proof-bg` | 6.51 | 7.65 | 4.5 | hallmark chip, proof note |
| `--proof` / `--paper`, `--surface` | 7.17 / 7.89 | 10.48 / 9.54 | 4.5 | proof-colored text outside a chip |
| `--danger` / `--paper` | 5.98 | 7.27 | 4.5 | error text |
| `--danger` / `--surface` | 6.59 | 6.62 | 4.5 | error text on cards |
| `--danger` / `--danger-tint` over paper | 5.32 | 6.24 | 4.5 | danger button hover |
| `--on-danger` / `--danger` | 6.59 | 7.27 | 4.5 | solid danger button |
| `--on-danger` / `--danger-hover` | 8.49 | 8.76 | 4.5 | solid danger button, hover |
| `--paper` / `--text` | 14.04 | 15.05 | 4.5 | inverted: chosen theme option, skip link |
| `--line-strong` / `--paper` | 3.17 | 3.80 | 3 | UI: input and control borders |
| `--line-strong` / `--surface` | 3.49 | 3.46 | 3 | UI: borders on cards |
| `--accent` / `--paper` | 4.50 | 6.76 | 3 | UI: primary button edge |
| `--accent` / `--surface` | 4.96 | 6.15 | 3 | UI: primary button edge on cards |
| `--focus` / `--paper` | 14.04 | 15.05 | 3 | UI: focus ring |
| `--focus` / `--surface` | 15.46 | 13.70 | 3 | UI: focus ring on cards and inputs |
| `--proof` / `--surface` | 7.89 | 9.54 | 3 | UI: tick strip cells |
| `--line` / `--paper` | 1.29 | 1.39 | none | dividers only (decorative, never a control edge) |

Decorative exception: the landing specimen's tick strip is `aria-hidden` and illustrative; its cells are 55% proof green
(2.67:1 light / 3.88:1 dark on the record surface). The real uptime strip on project pages uses full `--proof` (7.89 / 9.54).

`.band` (dark strip; dark tokens on `--band-bg` #212721 in the light page / #0D1310 in the dark page):
text 13.00 / 16.02 · muted 6.39 / 7.87 · accent-text 6.27 / 7.73 · accent edge 5.84 / 7.19 ·
line-strong 3.29 / 4.05 · focus 13.00 / 16.02. The primary button inside a band is the dark one.

**Dark primary button.** Was `#E5835C`, a pale orange that looked weak; it is now `#F5803F`
(more saturated) with dark text `#141A17` (6.76:1), hover `#FA9A63` (8.29:1). White text on any light
orange fails (≈2.6:1), so in dark the label is always dark. In light it stays white on `#BD4B27`.

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
- Space (4px base): s-1 .25rem ... s-9 6rem. Radius 0 (`--radius`). Focus: 2px `--focus` outline, offset 2px.
- Frames: 1px `--line` hairline; control edges use `--line-strong` (3:1). Press: buttons scale .98.

## Layout
- Content max 1200px; side padding max(1rem, safe-area inset) -> 1.5rem at 48em -> 2rem at 64em (`.container`).
- There is no global grid class. Pages that need columns declare them in their own CSS: 12 columns from 64em
  (project page, landing, `.sheet`), one column on phones.
- Project page: head across the top, then main (8: cover, about, build log) and proof column (4: marks,
  uptime, built with, tags, embed). On phones the order is head, cover, marks, about, log, facts, embed.
- Form pages (`.sheet`): title left (4), framed `.panel` sections right (8) from 64em; one column below.
- Owner bar on phones: one column, every button full width.
- Targets >= 44px (`--control-h`); on `pointer: fine` only chips, tag links and the theme switch may be smaller
  (theme switch is 44px on `pointer: coarse`). Inline links inside sentences are exempt (WCAG 2.5.8).

## Hallmark
- Flat chip: check glyph + mono label ("Repo owner", "Live", "Steady"); names stay English in every language.
  Earned: `--proof-bg` fill, `--proof` text. Not earned: dashed `--line-strong` outline, muted, "Not yet".
- Sizes: S (lists, label may hide state) · M · L (project page: chip + one fact line, opens a panel).
- The first mark proves repository ownership (or 10+ commits), never who wrote the code. Internal id stays
  `authored`; only display text says "Repo owner".

## Components (`components.css`)
- Buttons (44px, Inter 500): primary = accent fill (label dark in dark theme) · secondary = surface +
  `--line-strong` · quiet = text only · danger = danger outline, filled only on the final confirmation.
- Fields: surface, `--line-strong` border, >= 16px text, error = danger border + message with icon,
  `aria-invalid` + `aria-describedby`. Checkbox and radio: 20px control inside a 44px row. `.code-value` +
  `.btn--copy`: a literal value to paste.
- `.record` (frame + mono header row) is the base of the proof column, build log, embed panel, filters and
  the landing specimen. `.panel` is a framed form section (`--danger` = destructive). `.page-head`: h1 + lede.
- Lists: `.plate-row` (cover, name in Manrope, by-line, tagline, marks) · `.card` (landing) · `.chip` (tags).
- Header: not sticky, hairline under, mobile menu is `<details>`. Footer: links, language form (POST), theme.
- Toast: surface + border, `role=status`, bottom. Empty state: dashed frame, three unstruck marks, one action.
- Error pages (`404.html`, `403.html` inside the site; `500.html`, `400.html`, `403_csrf.html` standalone, no DB or
  context processors; views in `config/errors.py`): big mono status code, headline, one sentence, one mark that fails to
  stamp, primary action (front page, or feed when signed in) + "Go back", "Reference: <request id>" on 500/403/CSRF.
  Previews at `/_dev/errors/<code>/` (DEBUG only).
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
  equal sides). `.feed-card`: frame + hairline, no shadow; cover 16:10 from the thumbnail, head (avatar, name + marks, handle,
  time, follow), name in Manrope, tagline, marks, the latest update with a 2px rule (3 lines max), actions. `.empty--plain` is an
  empty state without the dashed frame. News cards (`.news-card`) share the same frame.
- Marks after a name (`{% user_marks person %}`, `.user-mark`): official = filled ink diamond with a cut check,
  `title` + hidden text "Official Shipmark account" (no colour: it is neither proof nor an action); moderator = quiet
  mono "MODERATOR" label with a `--line-strong` outline. Lists prefetch `owner__badges`.

## Motion (`motion.css`, `motion.js`)
- Animations use transform and opacity only. Exception, on purpose: hover/focus colour and border-colour fades
  (120-200 ms, paint only, no layout). Nothing animates width, height, margin, top/left or font size.
- Loops run only while their block is on screen (`.is-inview`, IntersectionObserver) and stop in a hidden tab
  (`html.is-paused`, which also reaches `::before/::after`). At most 3 loops visible at once. These pause rules
  apply only when JS runs (`.js` is set in `<head>`); without JS nothing loops, nothing is hidden, and the strike
  shows its final state.
- Reduced motion: `base.css` turns off every animation and transition, so each element shows its final state;
  no reveal, no page transition, the tick head is hidden.
- Landing: strike (once), live pulse + uptime tick + drift in the hero (3 loops, the maximum), closing cursor
  (far below the hero, never visible together with it), section reveal (once). Drift is desktop + hover only.
- Error pages: one mark comes down, does not take and lifts away (once, 1.3 s); the dashed "Not yet" mark stays.
- Project page: marks strike in order on load (300 / 650 / 1000 ms), one tick highlight over the 30 uptime
  cells (1 loop). Elsewhere: hover, press and focus answers, like/follow pop, menu and toast fades, page
  cross-fade.
- Page cross-fade is `@view-transition` (180 ms) inside `prefers-reduced-motion: no-preference`. Browsers
  without view transitions ignore the rule and navigate normally; `view-transition-name: site-header` is
  harmless there.

## Performance
- Self-hosted woff2 only (Latin set per page ~88 KB: Inter 48, Manrope 25, Plex Mono 15; Cyrillic and Latin-ext
  load only when the text needs them, by `unicode-range`). Inter + Manrope Latin (and Cyrillic for `uk`) are
  preloaded. Fallback fonts are size-adjusted, so the swap does not move the layout.
- Core CSS per page (tokens, base, components, motion): 55 KB raw, 14 KB gzip; one page file on top. Core JS
  (5 small ES modules, deferred by `type="module"`): 5.9 KB raw, 2.7 KB gzip. Only `theme-init.js` is blocking
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
  labelled `<select>` in a POST form. Toasts live in an `aria-live="polite"` region; errors use `role="alert"`.
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

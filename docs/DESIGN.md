# Design system (values live in `static/css/tokens.css`)

A public record of shipped work: each project is a framed record, and proof is a flat mark on it.
Warm paper, hairline frames, square corners, one action color. Rules:
- Depth comes from surface color (paper < surface) and hairlines. No bevels, shadows, gradients,
  glow or tinted sections. Square corners everywhere; only people (avatars) are round.
- Terracotta (`--accent`) is the one action color: the primary button, nothing else.
  Green (`--proof`) means proof only: earned marks, the uptime strip, "public" status.
  Danger red is for errors and destructive actions only.
- Mono uppercase labels (12px, tracked) name things: record headers, meta lines, eyebrows.
  Headlines are Manrope, body is Inter. Text is left-aligned.
- Motion answers an action, or marks a fact appearing (see Motion). No hover lifts.

## Color (light / dark)
Dark theme is used by the toggle, by the OS setting, and always inside `.band`. Both blocks in
`tokens.css` must stay in sync. Old token names (`--steel`, `--ink`, `--plate`) are only aliases now.

### Measured contrast (WCAG 2.x; AA = 4.5:1 text, 3:1 large text and UI). Checked 2026-11-11.
Recheck after any token change; every pair below must stay at or above its minimum.

| Pair (text / background) | Light | Dark | Min | Where |
|---|---|---|---|---|
| `--text` / `--paper` | 14.04 | 15.05 | 4.5 | body text |
| `--text` / `--surface` | 15.46 | 13.70 | 4.5 | cards, inputs |
| `--text` / `--tint` over paper | 12.81 | 12.80 | 4.5 | quiet button hover |
| `--muted` / `--paper` | 5.57 | 7.40 | 4.5 | secondary text |
| `--muted` / `--surface` | 6.14 | 6.73 | 4.5 | secondary text on cards |
| `--accent-text` / `--paper` | 5.29 | 7.26 | 4.5 | accent words, labels |
| `--accent-text` / `--surface` | 5.82 | 6.61 | 4.5 | accent words on cards |
| `--on-accent` / `--accent` | 4.96 | **6.76** | 4.5 | primary button |
| `--on-accent` / `--accent-hover` | 6.50 | **8.29** | 4.5 | primary button, hover |
| `--proof` / `--proof-bg` | 6.51 | 7.65 | 4.5 | hallmark chip, proof note |
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
| `--proof` / `--surface` | 7.89 | 9.54 | 3 | UI: tick strip cells |
| `--line` / `--paper` | 1.29 | 1.39 | none | dividers only (decorative, never a control edge) |

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
- Content max 1200px; side padding max(1rem, safe-area inset) -> 1.5rem at 48em -> 2rem at 64em.
- Grid 1 -> 6 (48em) -> 12 columns (64em), gap 1.5rem / 2rem.
- Project page: head across the top, then main (8: cover, about, build log) and proof column (4: marks,
  uptime, built with, tags, embed). On phones the order is head, cover, marks, about, log, facts, embed.
- Form pages (`.sheet`): title left (4), framed `.panel` sections right (8) from 64em; one column below.
- Targets >= 44px on `pointer: coarse`; chips and small controls may be 32px on `pointer: fine`.

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
- Error pages (`404.html`, `403.html` inside the site; `500.html`, `400.html`, `403_csrf.html` standalone):
  code label, headline, one sentence, three unstruck marks, two links.
- Tabs: plain links with `aria-current`; active = text color + 2px bar.

## Motion (`motion.css`, `motion.js`)
- Transform and opacity only. Loops run only while their block is on screen (`.is-inview`) and stop in a
  hidden tab (`html.is-paused`). At most 3 loops visible at once. Reduced motion: final state, no loops,
  no reveal, no page transition. Without JS nothing is hidden.
- Landing: strike (once), live pulse, uptime tick, drift, closing cursor, section reveal.
- Project page: marks strike in order on load (300 / 650 / 1000 ms), one tick highlight over the 30 uptime
  cells (loop 1). Elsewhere: hover, press and focus answers, like/follow pop, page cross-fade
  (`@view-transition`, 180ms).

## Badge (`projects/badges.py`)
Drawn in Python with fixed colors from the light tokens (plate, graphite, steel, line) and green for stamps and
the count. Square corners. Pairs measured 2026-11-11: plate/graphite 15.46, steel/plate 6.14, plate/proof 7.89,
white/proof 7.96, line/plate 3.49 (border).

## Logo
- Mark C, "struck slash": a square with a slash and a full stop cut out. Path
  `M0 0H32V32H0ZM4 26H12L22 6H14ZM20 18H28V26H20Z` (even-odd). Files: `logo.svg`, `logo-mark.svg`, `favicon.svg`,
  PNGs for the touch icon and OG image; `logo-dark.svg` and `logo-mark-dark.svg` are light copies for the dark
  admin. Options A and B live in `static/brand/options/` (styleguide only).
- Wordmark: lowercase "shipmark" in Manrope 700 as outlines. Header and footer inline the SVG so it follows the theme.

## Admin
django-unfold, colors from the same palette (`UNFOLD["COLORS"]`: primary = terracotta, base = warm green-black),
radius 0, light/dark logo from `branding.py`. Nothing else is overridden.

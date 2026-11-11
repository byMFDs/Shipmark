# Design system (values live in `static/css/tokens.css`)

An assay office for software: projects are plates, proof is struck into them. Rules:
- Raised = you can press it (buttons, plates). Recessed = it receives (inputs, earned marks).
- Ink only on proof marks, links, focus and the one primary action per view. Never a wash,
  glow, gradient or tinted section. People are round (avatars); objects are cut (plates, marks).
- Text left-aligned. Motion only answers an action, except the hero strike. No hover lifts.

## Color (light / dark)
Values: `static/css/tokens.css` (the redesign tokens; old names like `--ink`, `--steel` are aliases
until phase 3). Dark theme is used by the toggle, by the OS setting, and always inside `.band`.

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
- Plex Sans 400, 400 italic, 600 (body, UI, h3-h4) · Plex Sans Condensed 600 (h1-h2 only) ·
  Plex Mono 400 (code). Latin + Cyrillic woff2 by `unicode-range`. Condensed has no Cyrillic, so
  that file is variable Plex Sans at wdth 75 / wght 600 (same widths as Condensed), see OFL.txt.
- Fallbacks: local Arial / Liberation Sans scaled to Plex metrics (`size-adjust` + overrides).
- Root 100% (16px), 106.25% (17px) from 64em. Sizes in rem, so browser font settings still work.
- Scale 1.25: fs--1 .8rem (meta; the minimum) · fs-0 1 · fs-1 1.25 · fs-2 1.563 · fs-3 1.953 ·
  fs-4 2.441 · fs-5 3.052 · fs-6 3.815. Hero h1: clamp(fs-4 … fs-6).
- Body 1.55 line-height, max 68ch · h1-h2 1.05, tracking -0.02em · h3-h4 1.25 · numbers tabular.

## Space, radii, depth
- Space (4px base): s-1 .25rem · s-2 .5 · s-3 .75 · s-4 1 · s-5 1.5 · s-6 2 · s-7 3 · s-8 4 · s-9 6.
- Radii by size: plate 10px · control 8px · chip, checkbox 4px · mark 2px · avatar 50%.
- Bevel (plates, secondary buttons): inner top highlight + 1px contact line + one short shadow.
  Light `inset 0 1px 0 #fff/.85, 0 1px 0 text/.06, 0 2px 3px -1px text/.12`; dark `inset 0 1px 0
  #fff/.05, 0 1px 0 #000/.45, 0 2px 3px -1px #000/.5`. Blur never above 4px.
  Featured plate: last layer `0 3px 4px -2px`. Compact rows: no shadow, hairline separators.
- Press (inputs; buttons on `:active`): `inset 0 1px 2px text/.10`, button moves 1px down.
- Focus: 2px ink `outline`, offset 2px, on every focusable (survives forced-colors mode).

## Hallmark
- SVG cartouche: rectangle with cut corners (cut = 1/5 of height), 5:4, joints softened 2px.
- Only a glyph inside, as on real hallmarks; the word sits beside it, so marks keep one width in
  every language. Authored: commit node (ring on a line) · Live: dot inside a ring ·
  Steady: three equal bars. Glyph stroke 1.5px like the icon set, 2px at L.
- Earned: solid ink, glyph cut out in plate color; deboss = dark line on the inner top edge, light
  line under the outer bottom edge, drawn in the SVG (box-shadow would show square corners).
- Not earned: outline and glyph in `--line-strong` (3:1), no fill, label "Not yet".
- S 20×16: lists, earned marks only, label visually hidden · M 30×24 + label ·
  L 50×40 + label + one fact ("Owner of org/repo · checked 2 days ago").

## Hero: the specimen plate
- Headline (Condensed, fs-6), one plain sentence, "Sign in with GitHub". Under it, not beside it:
  one large example plate over 8 columns, captioned "Example project".
- Three L marks on the plate's bottom strip. Desktop: hairline leader lines to short notes on the
  right saying what was checked. Mobile: the notes are a list under the plate.
- Strikes at 250 / 600 / 950 ms, 150ms each: ink fills at once, mark 1.06 → 1, deboss deep →
  normal, plate dips 1px. Done by ~1.15s. CSS only, once. Reduced motion: final state.

## Layout
- Content max 1200px; side padding max(1rem, safe-area inset) → 1.5rem at 48em → 2rem at 64em.
- Grid 1 → 6 (48em) → 12 columns (64em), gap 1.5rem. Project page, feed, explore: 8 + aside 4.
- Targets ≥44px on `pointer: coarse`; chips and small controls may be 32px on `pointer: fine`.

## Components
- Buttons (44px, radius 8, Sans 600): primary = ink fill · secondary = plate, line-strong, bevel ·
  quiet = text only, shade on hover · danger = danger text + border, filled only on final confirm.
- Fields: plate, line-strong border, press shadow, ≥16px text. Error: danger border, message under,
  `aria-invalid` + `aria-describedby`. Checkbox: 20px box inside a 44px label row.
- Plate: featured (large, bevel, screenshot) · compact (row, S marks right). Chip: radius 4, hairline.
- Header: solid paper, hairline under, not sticky; mobile menu is `<details>` (works without JS).
- Footer: links, language form (POST + button), theme System / Light / Dark, © owner.
- Toast: plate + bevel, `role=status`, bottom above safe-area; JS hides it after 6s.
- Empty state: an empty plate outline with three unstruck marks, one sentence, one action.
- Tabs: plain links with `aria-current`; active = text color + 2px ink bar.

## Logo
- Mark C, "struck slash": a square with a slash and a full stop cut out of it. Both cuts use one
  8-unit punch on the 32-unit grid. The slash leans 2:1 (about 63°), lower and heavier than a typed
  "/" (~70°), so it reads as a struck mark, not a path separator or a terminal prompt. The stop is an
  8×8 square on even units: exactly 4×4 px at 16px, so it stays visible in a browser tab.
- Path: `M0 0H32V32H0ZM4 26H12L22 6H14ZM20 18H28V26H20Z` (even-odd). Used in `logo.svg`,
  `logo-mark.svg`, `favicon.svg`; the PNGs (`apple-touch-icon.png`, `og-default.png`) draw the same shape.
- Options A (notch check) and B (corner stamp) are kept in `static/brand/options/` and shown only on
  `/styleguide/`.
- Wordmark: lowercase "shipmark" in Manrope 700, outlined to paths. Header and footer inline the SVG
  so it follows the theme; favicon.svg switches color with its own `prefers-color-scheme` query.

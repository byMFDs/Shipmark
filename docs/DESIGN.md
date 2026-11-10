# Design system (values live in `static/css/tokens.css`)

An assay office for software: projects are plates, proof is struck into them. Rules:
- Raised = you can press it (buttons, plates). Recessed = it receives (inputs, earned marks).
- Ink only on proof marks, links, focus and the one primary action per view. Never a wash,
  glow, gradient or tinted section. People are round (avatars); objects are cut (plates, marks).
- Text left-aligned. Motion only answers an action, except the hero strike. No hover lifts.

## Color (light / dark; contrast on paper)
- `--paper` #F1F2EF / #15171A page · `--plate` #FAFAF8 / #1F2226 raised surfaces and inputs.
- `--text` #1E2126 / #E6E7E9 (14.4 / 14.5) · `--steel` **#666C74** / #9AA0A8 (4.7 / 6.8) secondary.
  Spec value #6E747C is 4.2:1 on paper (fails AA); #666C74 is the closest one that passes.
- `--line` #D5D8DB / #2E3237 dividers only · `--line-strong` #868C93 / #6B7179 (3.2 / 3.6) borders
  of inputs, checkboxes, secondary buttons (WCAG 1.4.11 needs 3:1; `--line` is 1.3:1).
- `--ink` #2A3FCF / #8EA8F1 (6.9 / 7.7; dark keeps the light hue, less chroma) · `--on-ink` #FAFAF8 / #15171A.
- `--danger` #A8322D / #F08A80 (5.9 / 7.4). No green "success": results are said in words.
- Light on `:root`; dark via `prefers-color-scheme` unless `[data-theme=light]`, or on any
  `[data-theme=dark]` element (styleguide shows both). Inline `<head>` script: no flash.

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
- Mark: square cartouche (cut 2/16; a bigger cut reads as a stop sign), ink, cut-out ⊥. Not a letter,
  not a check mark: survives a rename, does not read as a checkbox at 16px.
- Wordmark: name in Plex Sans Condensed 600, outlined to paths. Header inlines the SVG file so it
  follows the theme; favicon.svg swaps ink for dark browser tabs with its own media query.

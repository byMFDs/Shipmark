# Redesign plan (phase 0, waiting for approval)

Source: `docs/new_design/{white,dark}_version/` (landing only, 1440px). Everything else is inferred.

## 1. What I take from the images
- Warm paper page, near-white record surfaces, green-black text, a dark band for statements.
- Square corners, 1px hairline frames, no shadows or bevels. Depth comes from surface color only.
- Terracotta as the one action color; green only for proof (chips, check, notes).
- Big geometric two-sentence headlines; mono uppercase eyebrows and meta lines; `↗` in buttons.
- Hallmarks as flat mono chips "✓ Authored", pale green when earned.
- Landing order: header · hero (text + project record) · statement band · 01 The standard ·
  02 Out in the world · 03 The work behind the mark · closing band · footer.

## 2. What I change and why
- **Accent text** `#C4502E` is 4.1:1 on paper (fails AA for small eyebrows). Fill stays; text and
  eyebrows use a darker `--accent-text`. All pairs are computed in phase 1, not eyeballed.
- **Mono labels** are ~10px in the images. Minimum becomes 12px (0.75rem), tracking .06em.
- **Illustrative data**: `relay.so` is a real domain → `relay.example`. "99.98%" → a value the
  rules can produce, shown with a 30-day strip. "Built with Cursor" gets "(self-declared)".
- **"01 The standard" copy**: punchy subheads from the images, but the rule text comes from
  `proof.RULES` (already in the context), so the page cannot drift from the code.
- **"02 Out in the world"**: real `recent` projects when there are any; the three illustrative
  cards (labelled "Illustrative projects") only when the list is empty. Never mixed.
- **"Copy badge"** on the landing would copy a fake badge → static badge preview + link to
  `/how-proof-works/`. The real copy button stays on the owner's project page.
- **Theme switch** keeps System / Light / Dark (images show two). **Header tagline** is
  `brand.TAGLINE`, from 1024px only. **"№ 0042"** stays on the illustration (no pk on real pages).

## 3. Tokens (light / dark; final hex after contrast check)
| Token | Light | Dark | Use |
|---|---|---|---|
| `--paper` | #F4F3EE | #151C19 | page |
| `--surface` | #FFFEFA | #1C2420 | records, cards, inputs |
| `--band` / `--on-band` | #212721 / #F1EFE6 | #0E1411 / #F1EFE6 | statement + closing bands |
| `--text` | #20251F | #F1EFE6 | text |
| `--muted` | #5F665E | #A3ABA2 | secondary text (≥4.5:1) |
| `--line` | #D9D8D0 | #2C3632 | hairlines, frames |
| `--line-strong` | #85897F | #6A746E | control borders (≥3:1) |
| `--accent` / `--on-accent` | #C4502E / #FFFEFA | #E5835C / #151C19 | primary action fill |
| `--accent-text` | #B0431F | #EC8E68 | eyebrows, numbers, links on hover |
| `--proof-bg` / `--proof` | #E4EBDC / #2B5A3F | #24382C / #A9D1B4 | earned marks, proof notes |
| `--danger` | #A8322D | #F08A80 | errors, destructive only |
- Radii 0 (avatars stay round). Focus: 2px `--text` outline, offset 2px. Scale 1.25, space scale,
  12-col grid and 1200px container kept; hero h1 `clamp(2.75rem … 5.5rem)`, tracking -0.03em.

## 4. Fonts (self-hosted woff2, OFL, Latin + Latin-ext + Cyrillic, variable `wght`)
- Display: **Geologica** 500 (geometric, close to the image, native Cyrillic).
- Body/UI: **Inter** 400/500/600. Mono: **IBM Plex Mono** 400 (already in the repo).
- Removed: IBM Plex Sans and Sans Condensed. Fallbacks get new `size-adjust` metrics. Files come
  once from the Fontsource CDN and are committed; licences added to `OFL.txt`.

## 5. Components
Buttons (primary terracotta, secondary framed, quiet, danger; `↗` as inline SVG) · fields ·
eyebrow · section head · record (framed surface, mono header row) · project card · compact row ·
hallmark chip (S/M/L, earned / "Not yet") · proof note · uptime strip · band · tabs · tags ·
header + mobile `<details>` menu · footer (language select, theme segments) · toast · empty
state · avatar · error summary · pagination · build-log timeline.
`{% hallmark %}` keeps its signature; only its markup changes (check SVG + label).

## 6. Logo options (all one-color, square, no letters; shown on /styleguide/)
- **A. Notch check** (recommended): solid square, a cut-out check whose long arm runs out through
  the top-right corner. Same glyph as the earned chips; the notch keeps it from reading as a checkbox.
- **B. Corner stamp**: a square with a smaller square set into its bottom-right corner, split by a
  gap: a mark struck on a project. Most abstract, strongest at 16px.
- **C. Struck slash**: the "s/" of the images reduced to a square with one cut-out slash and a dot.
Wordmark: lowercase "shipmark" in Geologica 500, outlined to paths (fontTools in a temporary
venv outside the project, not a dependency). PNGs rendered with Pillow / headless Firefox.
`branding.py` gets `SITE_DOMAIN = "shipmark.me"`; the domain is shown from `brand.SITE_DOMAIN`.

## 7. Motion plan (transform/opacity only)
| # | Where | What | Cost |
|---|---|---|---|
| 1 | Hero record | chips struck at 300/650/1000ms (scale 1.12→1 + fade), once | CSS, 3 elements |
| 2 | Hero "Live" chip | dot pulse, 2.4s loop | CSS, loop 1 |
| 3 | Hero uptime strip | one highlight stepping over 30 cells, 6s loop | CSS, 1 element, loop 2 |
| 4 | Hero record | drift ±4px, 10s loop, desktop only | CSS, 1 layer, loop 3 |
| 5 | Closing band eyebrow | blinking mono cursor, 1.1s steps | CSS, the only loop in that view |
| 6 | 01 / 02 / 03 sections | reveal: fade + 12px rise, head hairline draws in, once | IntersectionObserver |
| 7 | Buttons, cards, links | arrow nudge 2px, press scale .98, underline scaleX | CSS |
| 8 | Like, follow, verify | check pops once when the state changes | CSS class from existing JS |
| 9 | Page to page | `@view-transition { navigation: auto }`, 180ms cross-fade | CSS, no JS |
- `static/js/motion.js` (~40 lines): loops run only under `.is-inview`, all pause on
  `visibilitychange`. Without JS everything is visible and static except the CSS-only strike.
- Max 3 loops per viewport (hero: 2, 3, 4). Reduced motion: final state, no reveal, no transition.

## 8. Phases and files
1. `tokens.css`, `base.css`, `components.css`, fonts, `static/brand/*`, `branding.py`, `ui.py`
   (hallmark markup), header/footer includes, `/styleguide/` (motion, 3 logos), `motion.js`.
2. `landing.html`, `pages/landing.css`, en + uk strings.
3. feed, explore, profile, project page + forms, settings, auth, report, legal/content,
   delete/confirm pages, error pages (404/403/500), menus, `pages/*.css`.
4. Motion polish, 360/390/768/1024/1440 × light/dark pass, a11y, CLAUDE.md §9 + `DESIGN.md`.

## 9. Open points (default applies unless you say otherwise)
1. **SVG badges** are drawn in `projects/badges.py` (Python). Default: restyle colors and the
   mark there (phase 3), nothing else: same URLs, cache, text and sizes logic.
2. **Admin (unfold)** colors live in settings. Default: update the palette values and logo only.
3. **Logo**: default A. 4. **Fonts**: default Geologica + Inter + Plex Mono.
5. **CTA** "Submit your project" starts the existing one-click GitHub sign-in, with the note
   "GitHub account required" under it. Default: keep as in the images.

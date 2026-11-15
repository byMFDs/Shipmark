# Palette and motion implementation

Only the five supplied bases are used. Fonts, content, template structure, URLs and application behavior are unchanged. Theme meta colour values and styleguide colour data follow the tokens. No browser or development server was started.

## Roles

| Token | Light | Dark |
|---|---|---|
| `paper` | `#F3F6F7` | `#071C1E` |
| `surface` | `#F3F6F7` | `#15292B` |
| `raised` | `#F3F6F7` | `#233638` |
| `text` | `#071C1E` | `#F3F6F7` |
| `muted` | `#20383A` | `#B1B9BA` |
| `line` | `#20383A` | `#4E6264` |
| `line-strong` | `#6A7A7C` | `#7F8E8F` |
| `accent` | `#C7F36B` | `#C7F36B` |
| `accent-hover` | `#79D9D2` | `#79D9D2` |
| `on-accent` | `#071C1E` | `#071C1E` |
| `accent-text` | `#20383A` | `#79D9D2` |
| `proof-bg` | `#C7F36B` | `#C7F36B` |
| `proof` | `#071C1E` | `#071C1E` |
| `danger` | `#20383A` | `#79D9D2` |
| `danger-hover` | `#071C1E` | `#C7F36B` |
| `on-danger` | `#F3F6F7` | `#071C1E` |
| `focus` | `#C7F36B` | `#C7F36B` |
| `signal` | `#79D9D2` | `#79D9D2` |
| `focus-edge` | `#071C1E` | `#071C1E` |
| `halo-tint` | `#527049` | `#79D9D2` |
| `halo-track` | `#071C1E` | `#071C1E` |

## Derivations

All mixes use rounded sRGB channels: `round(a × (1 − t) + b × t)`. No independent hue is introduced.

- `#6A7A7C`: rule → paper, 35%; light control edges.
- `#15292B`: ink → paper, 6%; dark records.
- `#233638`: ink → paper, 12%; dark fields/menus.
- `#B1B9BA`: ink → paper, 72%; dark secondary text.
- `#4E6264`: rule → paper, 22%; dark hairlines.
- `#7F8E8F`: rule → paper, 45%; dark control edges.
- `#527049`: rule → proof, 30%; visible proof-tinted perimeter light on light pages.
- Alpha colours use only ink (4%, 5%, 25%) or paper (6%); shadows and surface tints. `danger-tint` aliases the surface tint.

Lime fills primary actions, earned hallmark chips, proof notes and focus rings; all text on lime is ink. Signal fills uptime/live shapes and hover underlines. On light pages, standalone proof/status text uses rule. On dark pages it uses signal. Error and destructive-action text uses rule in light and signal in dark; existing labels and shapes distinguish its meaning. Focus lime is backed by an ink shadow; the halo uses an ink track.

## Verification log

Existing colour assertions are updated only for the new token roles: lime primary/focus are measured against their ink backing, and the perimeter light against both its track and surrounding surface. AA thresholds remain unchanged.

## Motion

- Marks: 8px drop with 2px / −1px overshoot, 420ms each, 120ms stagger, once on load.
- Uptime: 180ms fill per cell, 30ms stagger, starts at 660ms after all three marks; once. Existing uptime head and live/cursor ambient loops are now static.
- Primary idle shimmer: narrow paper-alpha sweep, 3.6s loop, one primary action per page; pauses offscreen and in hidden tabs. One decorative `aria-hidden` span is inserted by motion-only JS; templates are unchanged. Without IntersectionObserver it stays static. Paper at 50% alpha is the only additional derived colour (composited over proof/signal).
- GitHub perimeter light: one 900ms turn on hover/focus, including GitHub forms; static lit border for reduced motion. Existing busy spinner now turns once, 700ms. Only shimmer loops, so at most one loop is visible.
- Every content section, including nested sections: 18px rise/fade over 520ms, 70ms child stagger, once on scroll entry. Legacy reveal hooks inside a section share its entrance. No JS/observer or reduced motion: final content remains visible.
- People count: integer count from 0 on load, 700ms. Existing profile counters use the same duration on entry. Changing the motion preference mid-count resolves immediately to the server's final text.
- Page/section navigation: a 1px rule draws left-to-right, or right-to-left when choosing an earlier navigation item; content resolves after the rule, total 300ms. No link interception or requests; an ephemeral sessionStorage direction flag is the only state. Unsupported View Transitions still use the same CSS entrance; direct loads and reduced motion remain static. Native geometry morphs are disabled.
- Changelog timeline: the existing filled launch nodes are treated as live nodes; signal fill, one 600ms pulse on scroll entry, including inline-posted entries. No new nodes or content were added to the landing example. Reduced motion keeps the final node state.

## Measured text/background matrix

WCAG relative sRGB luminance: `(Lmax + 0.05) / (Lmin + 0.05)`. These are final, static states; transition fade frames are excluded. All text, including small labels and disabled controls, is checked at **4.5:1** (also exceeds the 3:1 large-text requirement). Rows deliberately cover every shared text role over every surface/tint, including placeholders, inverse controls/tooltips, form feedback, mock screens, proof notes, the fixed book/badge halves and image viewer. Admin surfaces/text use these same roles. User-uploaded images and existing sticker artwork retain their artwork colours. No browser-based computed-style audit was run.

| Theme | Foreground role | Hex | Background role | Hex | Contrast |
|---|---|---|---|---|---:|
| light | text | #071C1E | paper | #F3F6F7 | 16.20:1 |
| light | text | #071C1E | surface | #F3F6F7 | 16.20:1 |
| light | text | #071C1E | raised | #F3F6F7 | 16.20:1 |
| light | text | #071C1E | tint/paper | #E7EBEC | 14.65:1 |
| light | text | #071C1E | tint/surface | #E7EBEC | 14.65:1 |
| light | text | #071C1E | tint/raised | #E7EBEC | 14.65:1 |
| light | muted | #20383A | paper | #F3F6F7 | 11.45:1 |
| light | muted | #20383A | surface | #F3F6F7 | 11.45:1 |
| light | muted | #20383A | raised | #F3F6F7 | 11.45:1 |
| light | muted | #20383A | tint/paper | #E7EBEC | 10.36:1 |
| light | muted | #20383A | tint/surface | #E7EBEC | 10.36:1 |
| light | muted | #20383A | tint/raised | #E7EBEC | 10.36:1 |
| light | accent-text | #20383A | paper | #F3F6F7 | 11.45:1 |
| light | accent-text | #20383A | surface | #F3F6F7 | 11.45:1 |
| light | accent-text | #20383A | raised | #F3F6F7 | 11.45:1 |
| light | accent-text | #20383A | tint/paper | #E7EBEC | 10.36:1 |
| light | accent-text | #20383A | tint/surface | #E7EBEC | 10.36:1 |
| light | accent-text | #20383A | tint/raised | #E7EBEC | 10.36:1 |
| light | danger | #20383A | paper | #F3F6F7 | 11.45:1 |
| light | danger | #20383A | surface | #F3F6F7 | 11.45:1 |
| light | danger | #20383A | raised | #F3F6F7 | 11.45:1 |
| light | danger | #20383A | tint/paper | #E7EBEC | 10.36:1 |
| light | danger | #20383A | tint/surface | #E7EBEC | 10.36:1 |
| light | danger | #20383A | tint/raised | #E7EBEC | 10.36:1 |
| light | proof | #071C1E | proof-bg | #C7F36B | 13.79:1 |
| light | on-accent | #071C1E | accent | #C7F36B | 13.79:1 |
| light | on-accent | #071C1E | accent-hover | #79D9D2 | 10.61:1 |
| light | on-danger | #F3F6F7 | danger | #20383A | 11.45:1 |
| light | on-danger | #F3F6F7 | danger-hover | #071C1E | 16.20:1 |
| light | paper | #F3F6F7 | text | #071C1E | 16.20:1 |
| light | fixed | #F3F6F7 | fixed | #20383A | 11.45:1 |
| light | fixed | #F3F6F7 | fixed | #071C1E | 16.20:1 |
| light | fixed | #071C1E | fixed | #F3F6F7 | 16.20:1 |
| light | fixed | #071C1E | fixed | #C7F36B | 13.79:1 |
| light | fixed | #071C1E | fixed | #79D9D2 | 10.61:1 |
| light | fixed | #79D9D2 | fixed | #071C1E | 10.61:1 |
| light | fixed | #B1B9BA | fixed | #071C1E | 8.81:1 |
| light | fixed | #F3F6F7 | fixed | #15292B | 13.97:1 |
| light | drag hint 94% | #15292B | surface | #F3F6F7 | 13.97:1 |
| light | shimmer label | #071C1E | shimmer/accent | #D2F48E | 14.30:1 |
| light | shimmer label | #071C1E | shimmer/accent-hover | #98E0DB | 11.74:1 |
| dark | text | #F3F6F7 | paper | #071C1E | 16.20:1 |
| dark | text | #F3F6F7 | surface | #15292B | 13.97:1 |
| dark | text | #F3F6F7 | raised | #233638 | 11.67:1 |
| dark | text | #F3F6F7 | tint/paper | #15292B | 13.97:1 |
| dark | text | #F3F6F7 | tint/surface | #223537 | 11.85:1 |
| dark | text | #F3F6F7 | tint/raised | #2F4243 | 9.76:1 |
| dark | muted | #B1B9BA | paper | #071C1E | 8.81:1 |
| dark | muted | #B1B9BA | surface | #15292B | 7.60:1 |
| dark | muted | #B1B9BA | raised | #233638 | 6.35:1 |
| dark | muted | #B1B9BA | tint/paper | #15292B | 7.60:1 |
| dark | muted | #B1B9BA | tint/surface | #223537 | 6.44:1 |
| dark | muted | #B1B9BA | tint/raised | #2F4243 | 5.31:1 |
| dark | accent-text | #79D9D2 | paper | #071C1E | 10.61:1 |
| dark | accent-text | #79D9D2 | surface | #15292B | 9.15:1 |
| dark | accent-text | #79D9D2 | raised | #233638 | 7.65:1 |
| dark | accent-text | #79D9D2 | tint/paper | #15292B | 9.15:1 |
| dark | accent-text | #79D9D2 | tint/surface | #223537 | 7.76:1 |
| dark | accent-text | #79D9D2 | tint/raised | #2F4243 | 6.39:1 |
| dark | danger | #79D9D2 | paper | #071C1E | 10.61:1 |
| dark | danger | #79D9D2 | surface | #15292B | 9.15:1 |
| dark | danger | #79D9D2 | raised | #233638 | 7.65:1 |
| dark | danger | #79D9D2 | tint/paper | #15292B | 9.15:1 |
| dark | danger | #79D9D2 | tint/surface | #223537 | 7.76:1 |
| dark | danger | #79D9D2 | tint/raised | #2F4243 | 6.39:1 |
| dark | proof | #071C1E | proof-bg | #C7F36B | 13.79:1 |
| dark | on-accent | #071C1E | accent | #C7F36B | 13.79:1 |
| dark | on-accent | #071C1E | accent-hover | #79D9D2 | 10.61:1 |
| dark | on-danger | #071C1E | danger | #79D9D2 | 10.61:1 |
| dark | on-danger | #071C1E | danger-hover | #C7F36B | 13.79:1 |
| dark | paper | #071C1E | text | #F3F6F7 | 16.20:1 |
| dark | fixed | #F3F6F7 | fixed | #20383A | 11.45:1 |
| dark | fixed | #F3F6F7 | fixed | #071C1E | 16.20:1 |
| dark | fixed | #071C1E | fixed | #F3F6F7 | 16.20:1 |
| dark | fixed | #071C1E | fixed | #C7F36B | 13.79:1 |
| dark | fixed | #071C1E | fixed | #79D9D2 | 10.61:1 |
| dark | fixed | #79D9D2 | fixed | #071C1E | 10.61:1 |
| dark | fixed | #B1B9BA | fixed | #071C1E | 8.81:1 |
| dark | fixed | #F3F6F7 | fixed | #15292B | 13.97:1 |
| dark | drag hint 94% | #E6EAEB | surface | #15292B | 12.52:1 |
| dark | shimmer label | #071C1E | shimmer/accent | #D2F48E | 14.30:1 |
| dark | shimmer label | #071C1E | shimmer/accent-hover | #98E0DB | 11.74:1 |

**82 measured pairs; minimum 5.31:1; all pass AA.**

### Non-text visibility

| Theme | Light / ring | Surrounding page | Surrounding surface | Ink track |
|---|---|---:|---:|---:|
| light | #527049 | 5.13:1 | 5.13:1 | 3.16:1 |
| dark | #79D9D2 | 10.61:1 | 9.15:1 | 10.61:1 |

Lime focus against its ink backing: 13.79:1. The light border is a sweep over a track: the table measures the visible crest, not the unlit track. Gradient intermediates are linear sRGB mixtures of the documented endpoints. Light control edge #6A7A7C on paper: 4.12:1; dark edge #7F8E8F on raised: 3.72:1.

### Composited derivations

For rgba and gradients, every intermediate shade is derived by `base × alpha + background × (1 − alpha)`; alpha is not a new base colour. Rounded composites used by text are explicit below.

| Role | Background | Derived hex |
|---|---|---|
| light tint (5% ink / 6% paper) | #F3F6F7 | #E7EBEC |
| ink 4% (shadow/backdrop) | #F3F6F7 | #EAEDEE |
| ink 25% (shadow/backdrop) | #F3F6F7 | #B8C0C1 |
| ink 92% (shadow/backdrop) | #F3F6F7 | #1A2D2F |
| light tint (5% ink / 6% paper) | #F3F6F7 | #E7EBEC |
| ink 4% (shadow/backdrop) | #F3F6F7 | #EAEDEE |
| ink 25% (shadow/backdrop) | #F3F6F7 | #B8C0C1 |
| ink 92% (shadow/backdrop) | #F3F6F7 | #1A2D2F |
| light tint (5% ink / 6% paper) | #F3F6F7 | #E7EBEC |
| ink 4% (shadow/backdrop) | #F3F6F7 | #EAEDEE |
| ink 25% (shadow/backdrop) | #F3F6F7 | #B8C0C1 |
| ink 92% (shadow/backdrop) | #F3F6F7 | #1A2D2F |
| paper 50% shimmer (stop / effective peak) | #C7F36B | #DDF4B1 |
| paper 25% shimmer (stop / effective peak) | #C7F36B | #D2F48E |
| paper 50% shimmer (stop / effective peak) | #79D9D2 | #B6E8E4 |
| paper 25% shimmer (stop / effective peak) | #79D9D2 | #98E0DB |
| dark tint (5% ink / 6% paper) | #071C1E | #15292B |
| ink 4% (shadow/backdrop) | #071C1E | #071C1E |
| ink 25% (shadow/backdrop) | #071C1E | #071C1E |
| ink 92% (shadow/backdrop) | #071C1E | #071C1E |
| dark tint (5% ink / 6% paper) | #15292B | #223537 |
| ink 4% (shadow/backdrop) | #15292B | #14282A |
| ink 25% (shadow/backdrop) | #15292B | #122628 |
| ink 92% (shadow/backdrop) | #15292B | #081D1F |
| dark tint (5% ink / 6% paper) | #233638 | #2F4243 |
| ink 4% (shadow/backdrop) | #233638 | #223537 |
| ink 25% (shadow/backdrop) | #233638 | #1C3032 |
| ink 92% (shadow/backdrop) | #233638 | #091E20 |
| paper 50% shimmer (stop / effective peak) | #C7F36B | #DDF4B1 |
| paper 25% shimmer (stop / effective peak) | #C7F36B | #D2F48E |
| paper 50% shimmer (stop / effective peak) | #79D9D2 | #B6E8E4 |
| paper 25% shimmer (stop / effective peak) | #79D9D2 | #98E0DB |

## Retained motion inventory

Existing restrained motion remains once or on user action: presses/checks 120ms; arrows/disclosures/menu icons 200ms; cover zoom 500–600ms on hover; tooltip 120ms; popovers 160ms / sheets 220ms; menus/toast entrance 200ms and toast exit 160ms; state pop 260ms; page shell 420ms; list entry 380ms; empty marks 360ms plus failed-stamp 520ms; new log entry 320ms; domain-result entrance 260ms; notification dot 320ms; support stamp 700ms; error stamp 1300ms; community vote 320ms, reply branch 240ms, composer preview 260ms, sticker 360ms, picker/lightbox 220ms, empty-state sticker 520ms. Reading progress responds to scroll (no wall-clock duration). All authored keyframes and transitions animate transform/opacity only. Vendor admin animations are static; its transitions are limited to transform/opacity.

## Validation and manual review

Checks before commits: tokens — pages (125); marks/example — pages/projects (275); buttons — pages/accounts (310) plus motion/halo (11); sections/counter — pages/accounts (310); transitions — pages (125); timeline — pages/projects (275). Final all-app run: `python manage.py test --parallel 4 --noinput` — **1147 tests passed**; `python manage.py check` passed. The final focused motion/palette run passed 22 tests. A first parallel attempt hit the unchanged moderation test’s broad `u3` assertion in a randomly generated CSRF token; that test passed alone and the complete retry passed. No test dependency was added. JS syntax checks and a Node VM harness exercise loop visibility/tab pause, one-shot reveal/timeline entry, the counter at 0/350/700ms and reduced motion.

Manual checklist (not run: requested no browser/dev server): open landing, Discover/projects/people, feed, profile/tabs, project/detail/new/edit/delete/domain/embed/build log, auth/settings/deletion, support/sent, news/list/detail, content/legal, enabled Community views, moderator views, admin/login/list/edit and error pages. Check manual light/dark and OS dark, keyboard GitHub focus and one full turn, shimmer offscreen/hidden-tab pause, one-shot stamp/uptime/reveal/count/timeline, directional navigation, no JS, reduced motion before load and while counting, and 360px width. Styleguide historical comparison now uses the current dark palette; copy is unchanged.

The final colour pass includes the admin palette overlay (same-origin static CSS only), always-dark image viewer, current-palette styleguide samples, SVG/icon colours and the embedded badges. Badge geometry, visibility decisions and hallmark computation remain unchanged; badges now use paper/ink halves with lime marks and ink count labels. Four new tests cover every animation selector’s reduced-motion reset, explicit final-state overrides for new classes, allowed keyframe/transition properties, and the 82 measured contrast rows. Existing tests changed only in colour-role assertions; thresholds remain 4.5:1 text / 3:1 control and light visibility.

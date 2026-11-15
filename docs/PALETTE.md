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

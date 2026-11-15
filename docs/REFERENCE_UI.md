# Reference UI implementation

All five files in `docs/new/` were inspected before changes. Reference PNGs remain user-owned, untracked inputs.

## Account marks

`img.png` uses #0096FF (dominant non-white pixel colour), retained in both site themes. The moderator reference was absent from the supplied five files; it uses the same shared twelve-point rosette and white rounded check with #E0245E, as requested. Both reuse one inline SVG symbol and the existing size variants. These colours are exceptions for account marks, not changes to the site palette. No badge grants, permission rules, or hallmark computation are changed.

Measured contrast: white check / blue 3.09:1; white check / red 4.58:1. Red / light paper 4.22:1 and red / dark ink 3.84:1. Reference blue / light paper is 2.84:1 (kept exact as requested); blue / dark ink 5.70:1. Mark commit checks: `manage.py check`; accounts/pages: 315 tests passed. No new translation string was introduced by the mark-only change.

## Badge panel

The existing shared panel now opens immediately on pointer hover and keyboard focus, without moving keyboard focus during hover. Tap/activation opens and focuses it. A 100ms dismissal grace lets the pointer cross the existing gap into the panel; Escape closes and restores badge focus without reopening it. Existing animation durations and palette/type/radius tokens are unchanged. The first fact carries the matching rosette. Official heading/aria label is “Verified account”; its short fact says it is verified and operated by the Shipmark team. Moderator fact says moderators can review reports. Both render “Verified since” with the existing localized badge-record date. New strings and compiled catalogs ship together for all six translated locales plus English source.

Panel commit checks: `manage.py check`; accounts/pages: 315 tests passed; JS syntax and a Node VM harness passed hover, focus, real-date propagation, touch activation, and Escape/focus restoration.

## Sticker sheets

All 96 source cells are copied: 48 faces from `img_2.png`, then 48 gestures/objects from `img_3.png`, left-to-right and top-to-bottom. The sheets have no printed labels; the manifest uses the matching conventional emoji names, retaining existing short labels where the drawing matches. Each SVG has source-sheet/cell/hash provenance. `scripts/trace_sticker_sheets.py` reproduces the files with existing Pillow only.

The original vector curves and transparent edge pixels cannot be recovered exactly from these low-resolution, flattened PNGs, for **all 96 stickers**. The closest faithful vectors are source-pixel paths: no drawing is substituted, smoothed, simplified or colour-quantized; all retained RGB values are exact. Only the blue-grey sheet matte, its isolated dark compression specks, and the outer two-pixel cell gutter are removed. Antialiasing near that removed matte can retain a faint dark edge on light surfaces. No raster image is embedded in an SVG. This limitation applies to every item in the table below.

The 32 previous assets were removed with `git rm`; matching keys are recreated with reference artwork, and absent keys are retired using the existing rendering fallback. Empty states and seed/test fixtures now reference available sheet stickers. Database fields, one-sticker-per-reply validation, upload restrictions and key validation are unchanged. Every label is present in English and all six translated/compiled catalogs in this commit.

| Sheet | Row | Column | Key | English label |
|---|---:|---:|---|---|
| faces | 1 | 1 | `smile` | Smile |
| faces | 1 | 2 | `big-eyes` | Grinning face with big eyes |
| faces | 1 | 3 | `smiling-eyes` | Grinning face with smiling eyes |
| faces | 1 | 4 | `beaming` | Beaming face with smiling eyes |
| faces | 1 | 5 | `laugh` | Laugh |
| faces | 1 | 6 | `holding-back-tears` | Face holding back tears |
| faces | 1 | 7 | `sweat-smile` | Grinning face with sweat |
| faces | 1 | 8 | `joy` | Face with tears of joy |
| faces | 2 | 1 | `rofl` | Rolling on the floor laughing |
| faces | 2 | 2 | `smiling-tear` | Smiling face with tear |
| faces | 2 | 3 | `smiling-face` | Smiling face |
| faces | 2 | 4 | `blushing-smile` | Smiling face with smiling eyes |
| faces | 2 | 5 | `halo` | Smiling face with halo |
| faces | 2 | 6 | `slight-smile` | Slightly smiling face |
| faces | 2 | 7 | `upside-down` | Upside-down face |
| faces | 2 | 8 | `wink` | Wink |
| faces | 3 | 1 | `relieved` | Relieved face |
| faces | 3 | 2 | `love` | Love |
| faces | 3 | 3 | `smiling-hearts` | Smiling face with hearts |
| faces | 3 | 4 | `blowing-kiss` | Face blowing a kiss |
| faces | 3 | 5 | `kissing` | Kissing face |
| faces | 3 | 6 | `kissing-smiling-eyes` | Kissing face with smiling eyes |
| faces | 3 | 7 | `kissing-closed-eyes` | Kissing face with closed eyes |
| faces | 3 | 8 | `savoring-food` | Face savoring food |
| faces | 4 | 1 | `tongue` | Face with tongue |
| faces | 4 | 2 | `squinting-tongue` | Squinting face with tongue |
| faces | 4 | 3 | `winking-tongue` | Winking face with tongue |
| faces | 4 | 4 | `zany` | Zany face |
| faces | 4 | 5 | `raised-eyebrow` | Face with raised eyebrow |
| faces | 4 | 6 | `monocle` | Face with monocle |
| faces | 4 | 7 | `nerd` | Nerd face |
| faces | 4 | 8 | `cool` | Cool |
| faces | 5 | 1 | `disguised` | Disguised face |
| faces | 5 | 2 | `star-struck` | Star-struck face |
| faces | 5 | 3 | `party` | Party |
| faces | 5 | 4 | `melting` | Melting face |
| faces | 5 | 5 | `smirk` | Smirking face |
| faces | 5 | 6 | `unamused` | Unamused face |
| faces | 5 | 7 | `exhaling` | Face exhaling |
| faces | 5 | 8 | `sad` | Pensive face |
| faces | 6 | 1 | `disappointed` | Disappointed face |
| faces | 6 | 2 | `worried` | Worried face |
| faces | 6 | 3 | `confused` | Confused face |
| faces | 6 | 4 | `slightly-frowning` | Slightly frowning face |
| faces | 6 | 5 | `frowning` | Frowning face |
| faces | 6 | 6 | `persevering` | Persevering face |
| faces | 6 | 7 | `confounded` | Confounded face |
| faces | 6 | 8 | `tired` | Tired face |
| gestures/objects | 1 | 1 | `pouting-cat` | Pouting cat |
| gestures/objects | 1 | 2 | `heart-hands` | Heart hands |
| gestures/objects | 1 | 3 | `palms-together` | Palms up together |
| gestures/objects | 1 | 4 | `open-hands` | Open hands |
| gestures/objects | 1 | 5 | `raised-hands` | Raising hands |
| gestures/objects | 1 | 6 | `clap` | Clap |
| gestures/objects | 1 | 7 | `handshake` | Handshake |
| gestures/objects | 1 | 8 | `thumbs-up` | Thumbs up |
| gestures/objects | 2 | 1 | `thumbs-down` | Thumbs down |
| gestures/objects | 2 | 2 | `oncoming-fist` | Oncoming fist |
| gestures/objects | 2 | 3 | `raised-fist` | Raised fist |
| gestures/objects | 2 | 4 | `left-fist` | Left-facing fist |
| gestures/objects | 2 | 5 | `right-fist` | Right-facing fist |
| gestures/objects | 2 | 6 | `push-left` | Leftwards pushing hand |
| gestures/objects | 2 | 7 | `push-right` | Rightwards pushing hand |
| gestures/objects | 2 | 8 | `fingers-crossed` | Fingers crossed |
| gestures/objects | 3 | 1 | `victory` | Victory hand |
| gestures/objects | 3 | 2 | `finger-heart` | Hand with index finger and thumb crossed |
| gestures/objects | 3 | 3 | `love-you-hand` | Love-you gesture |
| gestures/objects | 3 | 4 | `horns` | Sign of the horns |
| gestures/objects | 3 | 5 | `ok` | OK hand |
| gestures/objects | 3 | 6 | `pinched-fingers` | Pinched fingers |
| gestures/objects | 3 | 7 | `pinching-hand` | Pinching hand |
| gestures/objects | 3 | 8 | `palm-down` | Palm down hand |
| gestures/objects | 4 | 1 | `palm-up` | Palm up hand |
| gestures/objects | 4 | 2 | `point-left` | Backhand index pointing left |
| gestures/objects | 4 | 3 | `point-right` | Backhand index pointing right |
| gestures/objects | 4 | 4 | `point-up` | Backhand index pointing up |
| gestures/objects | 4 | 5 | `point-down` | Backhand index pointing down |
| gestures/objects | 4 | 6 | `index-up` | Index pointing up |
| gestures/objects | 4 | 7 | `raised-hand` | Raised hand |
| gestures/objects | 4 | 8 | `back-of-hand` | Raised back of hand |
| gestures/objects | 5 | 1 | `splayed-hand` | Hand with fingers splayed |
| gestures/objects | 5 | 2 | `vulcan` | Vulcan salute |
| gestures/objects | 5 | 3 | `wave` | Wave |
| gestures/objects | 5 | 4 | `call-me` | Call me hand |
| gestures/objects | 5 | 5 | `hand-right` | Rightwards hand |
| gestures/objects | 5 | 6 | `hand-left` | Leftwards hand |
| gestures/objects | 5 | 7 | `flex` | Flexed arm |
| gestures/objects | 5 | 8 | `mechanical-arm` | Mechanical arm |
| gestures/objects | 6 | 1 | `middle-finger` | Middle finger |
| gestures/objects | 6 | 2 | `writing-hand` | Writing hand |
| gestures/objects | 6 | 3 | `pray` | Folded hands |
| gestures/objects | 6 | 4 | `point-at-viewer` | Index pointing at the viewer |
| gestures/objects | 6 | 5 | `foot` | Foot |
| gestures/objects | 6 | 6 | `leg` | Leg |
| gestures/objects | 6 | 7 | `mechanical-leg` | Mechanical leg |
| gestures/objects | 6 | 8 | `lipstick` | Lipstick |

Sticker trace verification reconstructed every SVG path: all 108,579 retained source pixels have the same coordinates and exact RGB values. The 96 assets occupy about 4.2 MB combined and each remains below 64 KiB. The safe-SVG checks still prohibit scripts, embedded raster images, references, URLs and external content; only the old 8 KB artwork budget and 32-item count were updated for the detailed reference set.

Sticker commit checks: `manage.py check`; Community/pages: 282 tests passed. Safe SVG/file-manifest agreement, 48+48 sheet order, explicit catalog entries in all seven supported languages, translated alt text, forged-key refusal and one-sticker-per-reply tests are green.

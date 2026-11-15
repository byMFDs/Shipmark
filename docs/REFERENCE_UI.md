# Reference UI implementation

All five files in `docs/new/` were inspected before changes. Reference PNGs remain user-owned, untracked inputs.

## Account marks

`img.png` uses #0096FF (dominant non-white pixel colour), retained in both site themes. The moderator reference was absent from the supplied five files; it uses the same shared twelve-point rosette and white rounded check with #E0245E, as requested. Both reuse one inline SVG symbol and the existing size variants. These colours are exceptions for account marks, not changes to the site palette. No badge grants, permission rules, or hallmark computation are changed.

Measured contrast: white check / blue 3.09:1; white check / red 4.58:1. Red / light paper 4.22:1 and red / dark ink 3.84:1. Reference blue / light paper is 2.84:1 (kept exact as requested); blue / dark ink 5.70:1. Mark commit checks: `manage.py check`; accounts/pages: 315 tests passed. No new translation string was introduced by the mark-only change.

## Badge panel

The existing shared panel now opens immediately on pointer hover and keyboard focus, without moving keyboard focus during hover. Tap/activation opens and focuses it. A 100ms dismissal grace lets the pointer cross the existing gap into the panel; Escape closes and restores badge focus without reopening it. Existing animation durations and palette/type/radius tokens are unchanged. The first fact carries the matching rosette. Official heading/aria label is “Verified account”; its short fact says it is verified and operated by the Shipmark team. Moderator fact says moderators can review reports. Both render “Verified since” with the existing localized badge-record date. New strings and compiled catalogs ship together for all six translated locales plus English source.

Panel commit checks: `manage.py check`; accounts/pages: 315 tests passed; JS syntax and a Node VM harness passed hover, focus, real-date propagation, touch activation, and Escape/focus restoration.

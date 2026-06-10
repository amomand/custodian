# Cabin View (cockpit framing)

Status: implemented (presentation layer). The operating desk now renders inside a
dark retro flight deck: a window onto the Dark out front, a cabin frame and
console sill around the viewport, screen-styled panels, an arka presence light,
and a head-turn that lets you look between stations instead of seeing one flat
grid.

It is a re-skin, not a new engine. The cabin is a thin presentation layer over the
same `ui` snapshot the operating desk already renders (see
`../architecture/web-session-api.md` and `operating-desk.md`). No simulation truth,
hidden value, or data contract changed, so the snapshot/contract tests are
untouched. Everything in the cabin except the desk panels is `aria-hidden`
atmosphere driven only by already-shown deterministic fields.

The producer call still holds: this is an operating-surface game, not a flight sim.
The cabin gives embodiment, place, and dread without becoming a free-look 3D
cockpit. The player's body is still their attention; the window is one more surface
arka's calm can colonise, used to make the Dark felt rather than explained.

## Layers

From back to front, all inside `.cabin`:

- **Window** (`#spaceView` canvas) — the space view straight ahead. A starfield
  painted client-side, carrying no text. Its travel and mood come only from
  deterministic snapshot fields (range to fix, jumps executed, the qualitative
  exposure band). The Dark shows as a quiet thinning and edge-darkening of the
  stars — never a meter, percentage, or label.
- **Glass / sill** (`.cabin-glass`, `.cabin::before`, `.cabin::after`) — canopy
  glare, vignette, and a low console shadow that seats the view in a hull.
- **Frame** (`.cabin-frame`) — dark chrome struts around the viewport. Decorative.
- **arka presence** (`#arkaPresence`) — a fixed pilot light near the canopy you can
  turn toward. Its calm is the same deniable drift atmosphere as the arka panel
  (`arka_panel_intensity`, a data hook only — never printed). arka's words still
  live in its panel.
- **Desk** — the operating desk panels, now styled as translucent lit screens so
  the window glows behind the cluster. A new **Forward View** panel frames the
  window and shows only fields already surfaced elsewhere (heading/current fix,
  range, jumps run, exposure band).

## Head-turn between stations

In cabin mode the player arrives looking forward through the window, with the
command channel available by pressing `/` rather than auto-focused. The desk is a
flight deck you look around. The panels are gathered into four stations, left to
right:

| Station   | Panels                         |
| --------- | ------------------------------ |
| `ahead`   | the window / Forward View      |
| `port`    | ship schematic + objective     |
| `console` | active system + raw telemetry  |
| `arka`    | arka advisory + transcript/log |

The looked-at station is bright and square-on; the others sit dim and slightly
angled in peripheral vision, and the whole desk parallaxes against the fixed
starfield. Looking `ahead` recedes the console so the view fills the canopy. Raw
telemetry and manual controls are always one head-turn away — the hiding is the
player's own choice of where to look, never corruption hiding information.

Turn the head with:

- the **station rail** buttons (the accessible primary control),
- the **left/right arrow keys** (when focus is outside the system tablist),
- **edge-hover** — dwelling briefly at the far left/right edge of the cabin.

The `1`–`4` keys still switch the active system tab within the console station.

## Boundaries (so beauty never leaks truth)

- The window and cabin render **only** normal snapshot fields. No trust, drift
  stage, manual familiarity, or exact Dark exposure ever appears. Exposure is shown
  only as the qualitative band already used in navigation; there is no Dark meter.
- Drift atmosphere (the arka presence light, panel intensity) stays a `data-*` hook
  applied to styling only, never printed as text — the same rule the operating desk
  already enforces, guarded by the snapshot leak test.
- All cabin motion — the starfield, the head-turn parallax, the focus cross-fade —
  is gated behind `prefers-reduced-motion` and the reduced-motion toggle.

## Degradation

Cabin mode (`html[data-cabin="on"]`) only runs on a wide viewport **with motion
allowed**. Under reduced motion or below 1100px it turns off: the station rail
hides, the head-turn transforms drop, the starfield falls back to a single static
frame, and the desk returns to the existing full stacked/grid layout where every
panel is visible at once. The cabin is purely additive — turning it off is the
current operating desk.

## Focus / take-the-watch

Focus mode (`zen-mode.md`) reads as the cabin dimming toward arka: the window
settles into a calm dark and the arka presence light is the thing you are looking
at, while the desk quiets to arka plus the strategic glance. It is still the
whole-ship form of standing delegation, with the same honest cost, and `Esc` (or
"take back the watch") restores the full cabin.

## Files

- `src/custodian/web_static/index.html` — cabin structure, window canvas, frame,
  presence, station rail, Forward View panel.
- `src/custodian/web_static/styles.css` — cabin layers, screen reskin, head-turn
  look states, reduced-motion / narrow fallbacks.
- `src/custodian/web_static/app.js` — Forward View render, station rail + look
  control, cabin-mode detection, the starfield space view.

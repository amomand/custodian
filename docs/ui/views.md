# Views: desk / map / dark

Status: implemented. The web client has three full-screen places, switched
deliberately: the **desk** (home — the synoptic operating desk), the **map**
(the star map and deck plan), and the **dark** (the forward window). Moving
between them is an act of attention — there is no head-turn, no cockpit, no
partial dimming; you are either at the board, at the chart table, or at the
glass. This supersedes the cockpit cabin experiment (PR #33); the reasoning is
in `../production/desk-map-dark-plan.md`.

Everything below is presentation over the same `ui` snapshot
(`../architecture/web-session-api.md`, `operating-desk.md`). The active view is
UI-local state like the active tab: never persisted, never sent to the engine.

## Switching

- **View rail** next to the mission strip: "Star map" and "Outside". Static
  buttons, never re-rendered, so keyboard focus is never lost to a snapshot.
- **Keys**: `m` toggles the map, `o` toggles the window, `Esc` walks back to
  the desk. `/` returns to the desk first if needed, then focuses the command
  channel.
- Each full-screen view carries a visible "Back to the desk" button. `Esc`
  order stays: cancel pending confirmation → take the watch back → return to
  the desk → blur the command input.
- The beat a run finishes, the client returns to the desk so the outcome and
  debrief are never hidden behind another view.

## The desk

Unchanged in layout and behaviour (`operating-desk.md`) — fully synoptic, so
cross-checking arka against raw telemetry stays a glance, never a navigation
act. It wears the screen re-skin salvaged from the cabin experiment: panels as
mounted lit displays (translucent over the hull shell, inset bevel, static
scanlines), which costs no legibility and is reduced-motion-safe (the
scanlines do not animate).

## The map (star map + deck plan)

The full-screen chart of record. Beauty is spent here deliberately, because
this is where decisions happen:

- **Star map**: the current fix and staged route chain sit in fixed chart
  positions. The open leg is bright, future legs are locked, and taken depth
  variants stay visible as committed path history. Each depth variant draws as
  its own path. The Dark is drawn as *territory* in the lower corner of the
  chart and each path bends toward it by its qualitative exposure band;
  instability bands render as increasingly broken dashes; the plotted route is
  highlighted. The SVG is `aria-hidden` decoration -- every fact on it (open
  leg, locked/taken state, band words, distances, depth, route names) is also
  text in the route cards beside it.
- **Route cards**: the same staged display as the desk's Navigation tab -- band
  rows, detail line, open / locked / taken labels, and plot / execute-jump
  buttons from the same `ui.actions` specs through the same dispatch, including
  the inline confirmation strip (rendered at the top of the map when triggered
  there). Delegate / standing / inspect groups for navigation ride along.
- **Deck plan**: the desk's sector diagram at map scale (same renderer, same
  corruption visuals and textual states). Selecting a sector shows its facts
  and its containment action specs beside the plan instead of jumping tabs.

No new commands, no new truth: the chart renders only fields the desk already
shows. Exposure appears only as the existing band words; "THE DARK" as a chart
label names territory, not a measurement.

## The dark (the forward window)

A full-screen starfield canvas. Looking outside is a chosen dread beat, not
wallpaper behind the panels:

- The field is painted from deterministic, already-shown fields only. Rising
  exposure thins the stars and tightens the edge vignette — the Dark closing
  in, never a meter, never a label on the glass.
- A minimal corner readout repeats heading / range / jumps / exposure band
  (all shown elsewhere), plus the way back.
- **Jumps are a moment**: when the already-shown jump counter increments, the
  window comes forward for ~2 seconds of warp streak, then returns to
  wherever the player was. Skipped entirely under reduced motion.
- **arka's presence light** sits in the upper glass: dim ember while merely
  looking outside, fully lit during focus. Its calm breathing carries the same
  deniable `arka_panel_intensity` drift atmosphere as the arka panel — slower
  and softer as the account rots, never noisier, applied as a `data-*` hook
  and never printed.

## Focus renders as the Dark

"Let arka take the watch" (`zen-mode.md`) no longer collapses the desk into a
text panel — the desk drops away entirely and focus renders on the window:
the void, arka's light, arka's advisory lines, the strategic glance
(route / ship), the command channel (the one form moves out with the player),
and "Take back the watch". Staring into the Dark while a calm voice holds the
board *is* the surrender. `Esc` or the button restores the full desk; urgent
incidents still eject (engine-side) and land on the desk.

## Boundaries and degradation

- Hidden values stay hidden everywhere: no trust, drift stage, familiarity, or
  exact Dark exposure on any view. The snapshot leak test still guards the
  `data-*`-only rule for drift atmosphere.
- All motion — starfield, warp, view cross-fade, presence breathing, fix
  pulse — is gated behind `prefers-reduced-motion` and the reduced-motion
  toggle. Under reduced motion the window is a static frame and the warp
  moment does not fire; every view remains fully usable, since views are
  chosen surfaces rather than motion effects.
- Narrow viewports: the desk keeps its existing stacked fallback; the map
  stacks its two panes and scrolls; the window is unaffected. Hidden views are
  `display: none`, so they leave the accessibility tree and tab order.

## Files

- `src/custodian/web_static/index.html` — the three view containers, view
  rail, dark-view overlays, map panes.
- `src/custodian/web_static/app.js` — view state and switching, starfield and
  warp, focus-on-the-dark rendering, map chart/cards/deck-plan renderers.
- `src/custodian/web_static/styles.css` — view visibility, screen re-skin,
  dark and map styling, reduced-motion and narrow fallbacks.

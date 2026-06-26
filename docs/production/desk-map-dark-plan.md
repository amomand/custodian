# Desk / Map / Dark: view architecture plan

Status: implementation plan, written 2026-06-10. Supersedes the cockpit cabin
experiment in PR #33. The one-line `story.py` parse fix from that branch is
extracted to PR #34 and is not part of this work.

## Why not the cockpit

PR #33 wrapped the operating desk in a first-person cockpit: a starfield window
behind the panels, a head-turn between four stations, an arka presence light on
the canopy. Reviewed running, none of it landed:

- The starfield was effectively invisible (~0.04% of canvas pixels lit, ~58px of
  unobstructed sky; panels at 93–95% opacity let nothing through).
- The arka presence light rendered entirely behind the mission strip.
- The head-turn reduced to opacity-dimming of "unlooked-at" panels — friction
  that taxes the desk's core skill (synoptically cross-checking arka against
  raw telemetry) while adding no embodiment.

The diagnosis: a cockpit casts the player as a *pilot*, but the custodian is a
*watch officer*. The dread is epistemic — the voice describing the ship may be
wrong — and that dread lives in instruments and accounts, not in a windscreen.
Every cockpit feature had to be compromised into invisibility because the game
kept correctly insisting on being a desk.

What did work and is kept: the screen re-skin (panels as lit displays:
scanlines, bevels, translucency), the jump-as-a-moment instinct, the
degradation discipline, and the no-truth-leak boundaries.

## The shape: three places, moved between by acts of attention

Embodiment comes from *deliberately going somewhere*, not from a painted-on
cabin. The client gets three full-screen views. The principle for where beauty
lives: **beauty lands hardest on the surface where decisions happen.**

1. **Desk** (home) — the existing synoptic operating desk, unchanged in layout,
   wearing the #33 screen re-skin. Everything visible at a glance; catching
   arka's drift by eye stays possible. No head-turn, no station rail, no
   edge-hover, no starfield behind it.
2. **Map** (star map) — full-screen chart: the current fix, staged route legs,
   and depth variants drawn as paths through the Dark (exposure band rendered as
   territory -- how deep each path cuts into the dark field), plus the ship deck
   plan grown up, with containment per sector. This is where route and
   containment *decisions* happen, so it is where the visual investment goes.
   Drawn only from snapshot fields the desk already shows.
3. **The Dark** (outside) — the full-screen window. A starfield that is
   actually visible, thinned and edge-darkened by the qualitative exposure band
   (never a meter), with a minimal corner readout (heading / range / jumps /
   exposure band — fields already shown elsewhere). Looking outside is a chosen
   dread beat, not wallpaper.

**Focus mode renders as the Dark.** "Let arka take the watch" drops the desk
away entirely: the void, arka's presence light (its calm the same deniable
`arka_panel_intensity` data hook — styling only, never printed), arka's recent
lines, the strategic glance, the command bar, and "Take back the watch". The
moment of surrender is staring into the Dark while a calm voice holds the
board. `Esc` takes the watch back, as today.

**Jumps are a moment.** Executing a jump (detected from the already-shown
`jumps_executed` counter) briefly brings the Dark forward as a warp overlay,
then returns to wherever the player was. Gated behind reduced motion.

## Contracts that do not move

- Views are pure presentation over the existing `ui` snapshot. No snapshot
  field, simulation truth, or data contract changes. View choice is UI-local
  state (like the active tab) and is never persisted or sent to the engine.
- Every button still dispatches an existing `ui.actions` action spec through
  the same `GameEngine.handle()` path (no-AI interpreter round-trip contract
  holds). The map renders the same navigation / containment specs the desk
  renders; it invents no commands.
- Hidden values stay hidden: no trust, drift stage, familiarity, exact Dark
  exposure. Exposure appears only as the existing qualitative band. The map's
  "Dark territory" is drawn from band words alone.
- Corruption visuals keep their existing meaning: `visual_state` hooks
  (`label_instability`, sector noise states, `arka_panel_intensity`) apply as
  `data-*` styling hooks only and are never printed. The snapshot leak test
  still guards this.
- Corruption and views never hide essential information: every map element
  keeps its textual state (labels, `aria-label`s); band words render as text,
  not colour alone.
- Reduced motion: starfield falls to a static frame, warp overlay does not
  fire, view cross-fades drop. All views remain fully usable — they are
  player-chosen surfaces, not motion effects.
- Narrow viewports: the desk keeps its existing stacked fallback; map and dark
  remain reachable (they are full-screen scrolling surfaces, not transforms).

## Client structure (`src/custodian/web_static/`)

- `index.html` — three view containers: `#deskView` (existing desk markup),
  `#mapView`, `#darkView` (canvas + overlay). A compact view rail (Desk / Map /
  Outside) in the mission strip area; `html[data-view="desk|map|dark"]` drives
  visibility. Focus forces the dark view with the focus overlay variant.
- `app.js` — `ui.view` local state; `setView()`; keyboard: `m` map, `o`
  outside, `Esc` returns to desk (after its existing duties); starfield module
  (runs rAF only while the dark view or warp overlay is visible); map renderer
  (route plot SVG + enlarged deck plan, reusing the existing schematic
  renderer and `actionButton` dispatch); focus rendering moved onto the dark
  view; jump warp overlay.
- `styles.css` — keep #33's screen re-skin (scanlines, bevels, translucent
  panels, dark shell); add view visibility rules, map layout, dark overlay
  layout; delete nothing from the desk's existing responsive/reduced-motion
  behaviour.

## Work plan

1. **Land `story.py` fix** — PR #34, independent. (Done.)
2. **Re-skin only** — port the #33 panel/screen cosmetics with no starfield
   behind the desk. (Done.)
3. **View system** — view rail, `data-view` switching, keyboard, Esc ordering.
   (Done.)
4. **The Dark view** — visible starfield (bigger/brighter stars, density tuned
   on a real screen), exposure thinning/vignette, corner readout, jump warp
   overlay, reduced-motion static frame. (Done.)
5. **Focus-on-the-Dark** — focus layout becomes the dark view variant: arka
   light + lines + glance + command bar + take-back. Urgent ejects (engine
   already does this) land back on the desk view. (Done.)
6. **Map view** — route plot SVG (fix → candidate paths through Dark
   territory, band words as text, plot/execute buttons per route with the
   existing confirmation strip), deck plan pane (reuse schematic renderer at
   map scale, sector select → containment actions). (Done.)
7. **Docs** — `docs/ui/views.md` (cabin-view.md never landed on main; nothing
   to retire); update `operating-desk.md`, `zen-mode.md`,
   `project-reference.md`. (Done.)
8. **Verify & critique loop** — run the suite; drive the app in a browser:
   all three views, focus enter/exit, a jump from desk and from outside,
   narrow viewport, reduced motion; iterate on density/contrast/feel until
   the vibe holds without costing legibility. (Done — see PR notes. Found and
   fixed along the way: a pre-existing `null`-stringifying append in the
   system/nav/containment renderers; clipped chart labels; warp hold now
   yields to explicit view changes.)

## Out of scope (deliberately)

- The map as *arka's account* (drift colonising the chart) — strong later
  idea; needs its own design pass against the deniability rule.
- Sound. Worth a separate pass; nothing here should preclude it.
- Any engine/snapshot change at all.

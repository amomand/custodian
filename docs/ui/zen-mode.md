# arka Focus Mode ("take the watch" / zen mode)

Status: implemented. Clicking arka (or the `focus` command) hands it the whole
ship and quiets the desk to arka plus a route/current-fix glance and a high-level
ship overview. Raw telemetry, dense controls, and command-output clutter are
intentionally absent while arka has the watch; the full desk is one click or
`Esc` away. Mechanically it is the whole-ship form of standing delegation, so it
carries the same honest cost (drift pressure, no manual familiarity) and never
makes an irreversible move. The focus dwell is recorded in the behaviour ledger
(`focus_beats`). It is the UI expression of standing delegation. It already has
teeth through delegation-driven drift; the story/incident layer adds
contradiction-aware reliance signals (entered/stayed during a contradiction,
urgent-incident eject). Internal name: focus / zen mode. Player-facing, it is
arka offering to take the watch.

## Concept

Click arka and the operating desk quiets. The dense noise — raw telemetry,
per-metric panels, manual controls — fades away, leaving arka's voice and a few
slow, strategic readouts (route and ship overview). arka has the board. The
player can leave at any time and the full desk returns.

It is the same idea as the operating desk's arka panel taken to its limit: arka
is already the easiest thing to read, the path of least resistance. Focus mode
lets the player make the entire ship's complexity disappear by trusting it.
Choosing the quiet *is* the act of delegation.

## What shows, what hides

Shown in focus mode:

- arka's advisory and channel,
- a route / current-fix glance,
- a ship overview (high-level sector state),
- the command channel.

Hidden by player choice:

- raw telemetry panels and per-metric numbers,
- manual control surfaces,
- the busy schematic and action density,
- command-output clutter that would pull the hard faff back into the quiet.

The cut is deliberate: focus mode keeps the slow, strategic things and removes
the fast micro-telemetry that arka abstracts away.

## Why it fits the thesis

This is delegation rendered as an interface. The desk is the manual/raw path;
focus mode is the delegated path made literal. The horror is structural: in the
quiet, the raw telemetry that could contradict arka is gone — by the player's own
choice. Late in a run the calm persists while the now-hidden raw says the forward
banks are failing. To catch it the player has to choose to leave the quiet, and a
player who has grown comfortable will not. That already bites mechanically
through delegation-driven drift; later incidents make the contradiction sharper.

## Guardrails (so it does not break the design)

- **Not a win button.** Its payoff is calm and reduced cognitive load, paid for in
  lost vigilance and decaying manual familiarity. It must never make outcomes
  strictly better on its own.
- **Raw stays one step away.** This is *consensual* hiding — the player chose it
  and can leave instantly. The point of focus is that the hard, confusing desk is
  not leaking back into view while arka holds the watch. That is categorically
  different from corruption hiding information, so it does not violate "raw
  telemetry is always the audit path".
- **Irreversible moves eject.** Per the standing-delegation rule, arka cannot seal
  a cryobay, abandon a sector, or commit the final jump from inside focus mode
  without surfacing it and pulling the player out to authorise. Otherwise the
  ending becomes arka's fault instead of the player's history.
- **Earn it, do not default to it.** Focus mode should become available/tempting
  once arka has earned trust (Act 1+), not be the default from minute one — so the
  player first learns the real desk and the "manual control is real" pillar holds.
- **Diegesis.** "Zen mode" is an internal name only. The player-facing surface is
  arka taking the watch, e.g. clicking arka → "I've got it. Rest your eyes." and
  the desk quiets.

## Behaviour ledger signals (§6)

Focus mode is a strong reliance signal. Record at least:

- time spent in focus mode,
- whether focus mode was entered (or stayed in) during an arka/raw contradiction,
- which irreversible decisions ejected the player back to the full desk.

These feed difficulty, late-game friction, and the debrief — never a visible
trust meter.

## Accessibility

- The enter/leave transition is a cross-fade gated behind `prefers-reduced-motion`
  and the reduced-motion toggle; reduced motion swaps instantly.
- Focus mode never traps focus and always exposes a clear, keyboard-reachable way
  back to the full desk.

## Dependencies

- Behaviour ledger and standing delegation (done): mechanical home; focus mode is
  the whole-ship form of standing delegation.
- The story / manifest-anchor / incident layer (GitHub issue #21): supplies the
  drift and incidents that make the calm dangerous and let urgent incidents eject
  the player.
- Builds on the operating desk and the `ui` snapshot (both done).

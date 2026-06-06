# The Dark

This document describes how the Dark *functions* in Custodian. It does not
explain what the Dark is, and nothing in the game should.

## What it is not

The Dark is not an enemy faction, monster, ghost, alien, god, virus, or lore
puzzle. There is no codex entry that reveals it, no log that decodes it, and no
ending that names it. arka does not explain it. It is an unknowable pressure,
expressed only through effects.

## How it is expressed

The Dark is never a number the player can read. There is no `Dark: 42%` meter and
no clean progress bar. It surfaces instead as symptoms on the instruments:

- qualitative sector symptoms — `sensor noise`, `readings disagree`,
  `intermittent`, `no signal`, then `sealed` or `written off`;
- signal confidence falling — `steady` → `thin` → `contested` → `poor` → `lost`;
- raw sensor disagreement and source labels degrading from direct to inferred;
- impossible measurements and timestamps (a past "tomorrow" is good; explaining
  it is not);
- route exposure expressed as a band, never as the exact internal exposure value.

Underneath, the engine owns the truth: hidden per-sector symptom load,
`total_dark_exposure`, and arka's deterministic drift stage. The web snapshot
projects only the qualitative shadows of these into normal player UI; the exact
internals stay behind the loopback-only dev snapshot.

## Visual corruption (operating desk)

On the operating desk the Dark is what makes the ship picture stop being
comforting. `visual_state` maps deterministic state to look, never to new truth:

- **Schematic.** Sector noise degrades the graphical nodes and their connecting
  edges (`thin`, `disagreeing`, `broken`, `isolated`, `blank`). A no-signal
  sector goes contour-only and dim; a written-off sector goes dead.
- **Labels.** Higher arka drift increases `label_instability`, a subtle wobble of
  the sector labels — never enough to make them unreadable.
- **arka panel.** Higher drift raises `arka_panel_intensity`, rendered as calm,
  not noise: the same warm competence reads *cleaner* while the schematic around
  it falls apart. This atmosphere is deliberately deniable, never a legible tell,
  and never printed as text.

## Rules

- No Dark meter, percentage, or codex entry, ever.
- arka may misframe or omit symptoms by drift stage, but must not invent or
  explain sector truth.
- Corruption is sparing and meaningful, not wallpaper static.
- Any corruption that affects readability has a textual equivalent and a
  reduced-motion fallback. Horror is not an excuse for unreadable UI.
- The audit path always remains: raw telemetry stays learnable even when noisy.

See `docs/game_mechanics/spatial-containment.md` for sector symptoms and
`docs/ui/operating-desk.md` for how the desk renders this corruption.

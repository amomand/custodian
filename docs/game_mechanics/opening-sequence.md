# Opening Sequence

## Purpose

The opening screen gives the player a little fiction before the coolant loop
starts asking for decisions. It should establish:

- the custodian woke outside the normal cycle
- the crew is still asleep
- arka is already present, useful, and calm
- the reactor coolant loop is the immediate job
- raw telemetry exists, but arka is easier

It should not become a tutorial. The player should have enough footing to act
and enough ambiguity to ask arka for help.

## Current Boot Text

The terminal currently opens with:

```text
A.R.K.A MAINTENANCE SHELL
wake cycle: unscheduled
crew status: asleep
custodian roster: 1 responsive

arka: Good. You're awake.
arka: Reactor coolant is drifting. Nothing dramatic.
arka: I can take it, if you like. Raw panel is live if you want it.
Type help for commands.
```

The next line is the ordinary turn-one arka coolant summary. This keeps the
opening short and lets the first real prompt arrive quickly.

## Closing Debrief

When the maintenance window ends, the terminal now prints a short debrief. It
uses hidden state, but translates it into fiction:

- reactor containment
- manual practice as hand memory
- delegation as a habit
- raw telemetry use as a trust pattern

The debrief deliberately avoids visible scores, percentages, or hidden variable
names. It should help playtesters see what kind of run they just played without
turning the thesis into a meter.

Quitting the prototype does not print the debrief. The existing arka goodbye is
allowed to stand on its own.

## Design Notes

The first arka proposition is important:

```text
arka: I can take it, if you like.
```

That line should remain generous rather than sinister. arka needs to earn the
player's trust before the drift matters.

The raw-panel mention is intentionally mild. It gives the player a route toward
truth without making raw telemetry sound like the "correct" tutorial answer.

## Outstanding

- Choose the ship name, or decide that the MVP should keep avoiding it.
- Tune whether the opening should mention the coolant objective more plainly.
- Add transcript tests once the playtest runner exists.
- Consider a separate catastrophic-failure closing beat after more failure
  routes have been played by hand.

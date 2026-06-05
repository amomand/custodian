# Opening Sequence

## Purpose

The opening screen gives the player a little fiction before the coolant loop
starts asking for decisions. It should establish:

- the custodian woke outside the normal cycle
- the crew is still asleep
- arka is already present, useful, and calm
- the reactor coolant loop and cryostasis are the immediate job
- the goal is stated plainly: keep both panels nominal until the watch ends
- raw telemetry exists, but arka is easier
- current telemetry is visible as ship readout, not arka speech

It should not become a tutorial. The player should have enough footing to act
and enough ambiguity to ask arka for help.

## Current Boot Text

Interactive terminals first show an A.R.K.A software boot screen:

```text
A.R.K.A OPERATIONS KERNEL
cold-start recovery image

wake signal ............ unscheduled
operator biometric ..... 1 responsive
crew census ............ asleep
reactor watch .......... variance detected
cryostasis watch ....... viable / drifting

loading maintenance shell
[#######.................] memory lattice
[#############...........] telemetry buses
[###################.....] advisory channel
[########################] arka runtime

press any key to open maintenance shell
```

arka does not introduce itself here. The first screen belongs to A.R.K.A in the
formal software register; arka's familiar voice enters only after the maintenance
shell opens.

After the keypress, the terminal opens with:

```text
A.R.K.A MAINTENANCE SHELL
wake cycle: unscheduled
crew status: asleep
custodian roster: 1 responsive

arka: Good. You're awake.
arka: Reactor coolant is drifting. Cryostasis is colder than you are.
arka: The job is simple to say: hold both panels nominal until the watch closes.
arka: Your hands can answer one control at a time. I can take a whole panel.
arka: I can take coolant or cryo, if you like. Raw panels and manual controls are live.
arka: Pumps, vent, flush, balance. Banks, chill, pods, triage. Unglamorous verbs, but they work.
Type help for commands.
```

The goal and the throughput asymmetry are now stated in the opening so the player
is never left wondering what they are for. The next visible state is the
objective block (OBJECTIVE / WATCH / ATTENTION / CREW LOAD) followed by the
terminal HUD and arka's qualitative summary. Non-interactive runs skip the boot
keypress screen so CI, smoke tests, and transcript tooling stay readable.

The terminal clears on interactive launch and again for major scene changes such
as pressure events, blooms, failures, and endings. This is a presentation
courtesy, not a state transition. Non-interactive runs do not clear the screen.

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

arka should not read out telemetry numbers in ordinary summaries. The HUD and
raw panel own numbers; arka owns interpretation, reassurance, omission, and
eventual contradiction.

## Outstanding

- Choose the ship name, or decide that the MVP should keep avoiding it.
- Consider a separate catastrophic-failure closing beat after more failure
  routes have been played by hand.

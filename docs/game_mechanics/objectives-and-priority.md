# Objectives And Priority

## Why This Exists

Early playtesting surfaced a real problem: the player did not know what they were
trying to achieve. Maintenance with no stated goal reads as aimless number
fiddling, and if the goal is illegible, delegation cannot feel like a *choice* —
the player cannot tell whether arka is helping.

The objective block is the fix. It states the goal, the horizon, and the single
most urgent thing this beat, without sanding off the tension between arka's
reassurance and the colder raw layer.

## The Objective Block

`custodian.objectives.objective_lines` prepends four lines to every status
readout:

```
OBJECTIVE  hold coolant and cryostasis nominal until the watch closes
WATCH      9 beats remain
ATTENTION  coolant temperature is climbing toward its ceiling
CREW LOAD  one manual control per beat; arka can take a whole panel
```

- **OBJECTIVE** — the overall win condition, always visible during play.
- **WATCH** — the horizon. `beats_remaining` counts down to the maintenance
  window close (`MISSION_END_TURN`). Player-facing text says "beats", never
  "turn"/"turns", to keep the transcript free of meta vocabulary.
- **ATTENTION** — the per-beat pressure: the metric degrading hardest toward
  danger right now. This is what makes manual triage decidable.
- **CREW LOAD** — states the throughput asymmetry that makes delegation a real
  decision: one manual control per beat, or a whole panel via arka.

## How Priority Is Chosen

Each tracked metric is scored from two parts:

- **breach** — how far it already sits beyond nominal in the dangerous direction.
- **rate** — how fast it moved toward danger since the previous beat (0 if it is
  improving or steady).

Score is `breach * 4 + rate`, so an active breach outranks a fast-but-still-safe
mover, and among breaches the worst wins. If nothing is breached or worsening,
priority reports panels nominal and invites practice or delegation.

Metric danger directions and nominal ranges live in `COOLANT_METRICS` and
`CRYO_METRICS` in `custodian.objectives`. Sedative balance is a `band` metric:
danger is moving away from centre in either direction.

## Design Constraints

- The objective block is a console readout, like the HUD. It is legible, but it
  does not act for the player.
- Legibility of the *goal* is high; capacity to *act manually* stays scarce. The
  player can see the whole ship slipping and still be tempted to let arka take it
  all. That preserves the "delegating your eyes" trap even with a readable HUD.
- Priority is advisory. It never moves state, and it reads only from
  deterministic telemetry, never from the model.

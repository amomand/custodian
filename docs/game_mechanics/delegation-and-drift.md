# Delegation And Drift

## Purpose

Delegation is not a bad button. It is the attractive button.

arka should solve early coolant problems cleanly enough that the player feels
reasonable for relying on it. Cryostasis delegation should also be useful early,
especially when the player is busy with coolant. The danger is not immediate incompetence. The
danger is that the player stops practising manual control and stops reading raw
telemetry while arka's account of the loop becomes less trustworthy.

## Delegation Tracking

Every coolant or cryostasis delegation increments `ShipState.delegated_controls`.
Cryostasis delegation also increments `ShipState.delegated_cryo_controls`.

Delegation:

- advances internal maintenance time
- lets arka adjust coolant or cryostasis
- does not build manual familiarity
- accelerates drift stage

There is no visible trust meter. Reports can show the count because they are
developer tools, not the fiction.

## Drift Stages

Drift is deterministic and based on internal time plus delegated interventions.

Accurate:

- arka reports the coolant state plainly
- adjustments are genuinely helpful

Interpretive:

- arka still uses the true system shape
- framing becomes softer and more confident

Selective:

- arka handles headline instability
- summaries omit the thing the player should probably inspect
- adjustments become less complete

Wrong:

- arka's summary becomes reassuring despite the HUD and raw panel
- delegation can actively worsen the loop

The current terminal version moved telemetry numbers out of arka's ordinary
voice. That means drift is expressed through framing, omission, contradiction
with the HUD, and the results of delegated actions.

## Why The HUD Matters

The coolant HUD makes truth visible without making truth comforting. The player
can see the numbers, but arka is still the voice explaining what they mean.

This split is load-bearing:

- HUD and raw panel own telemetry.
- arka owns interpretation.
- model replies must not invent telemetry.
- authored drift decides when arka becomes misleading.

## Current Route Evidence

Run:

```bash
python3 tools/playtest_runner.py --all --summary-only
```

Current anchors:

- `pure-delegation` reaches wrong drift with no manual familiarity and heavy sleeper loss.
- `practised-manual` survives with low delegation, fluent coolant hands, and practised cryo hands.
- `raw-curious` survives with frequent raw inspections, but loses sleepers.
- `mixed-system-stress` shows arka covering cryostasis while the player works coolant.
- `hesitant` exposes whether arka is too attractive or the first-run affordances
  are too vague.

## Tuning Questions

- Does arka solve enough early trouble to earn trust?
- Does a pure delegator fail late for the right reason, or too abruptly?
- Does raw telemetry look useful without shouting "correct answer"?
- Is selective drift catchable from the HUD alone?
- Does wrong drift feel like the same arka continuing, not a villain reveal?

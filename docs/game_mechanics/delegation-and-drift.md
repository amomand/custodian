# Delegation And Drift

## Purpose

Delegation is not a bad button. It is the attractive button.

arka should solve early coolant problems cleanly enough that the player feels
reasonable for relying on it. Cryostasis delegation should also be useful early,
especially when the player is busy with coolant. The danger is not immediate incompetence. The
danger is that the player stops practising manual control and stops reading raw
telemetry while arka's account of the loop becomes less trustworthy.

## Delegation As A Throughput Choice

Delegation is not just "arka is higher quality." It is a capacity decision.

- Manual control steadies **one system per beat**. The player picks the single
  intervention they can afford and spends the beat on it.
- arka takes a **whole panel at once**. When it handles coolant or cryostasis, it
  addresses several metrics in a single beat.

Because telemetry degrades on several axes at once (see the trend arrows and the
`PRIORITY` line in the objective block), a hands-on player constantly falls
behind on everything they did not touch. That is the honest, structural reason
delegation is seductive: there is too much ship for one waking custodian.

The trap is wired to the same mechanic. When arka takes the whole panel, the
player stops reading *which* knob moved, which is exactly how selective and wrong
drift slip past them.

## Delegation Tracking

Every coolant or cryostasis delegation increments `ShipState.delegated_controls`.
Cryostasis delegation also increments `ShipState.delegated_cryo_controls`.

Delegation:

- advances internal maintenance time
- lets arka adjust a whole panel of coolant or cryostasis metrics
- does not build manual familiarity
- is the primary driver of drift stage

There is no visible trust meter. Reports can show the count because they are
developer tools, not the fiction.

## Drift Weighting

Drift is deterministic. Its inputs, in order of weight:

1. **Delegation (primary).** `delegated_controls >= 3 / 5 / 7` pushes arka to
   interpretive / selective / wrong. Handing arka the panels is what lets its
   account of the ship rot, regardless of how early it happens.
2. **Time (weak backstop).** Late in the watch, arka drifts even for a careful
   player, so the finale still bites. `wrong` overlaps the final crisis beat so
   the "calmly contradicting the raw feed" moment actually lands.
3. **Vigilance (mitigation).** Reading the raw layer buys honest beats: every two
   `raw` inspections delay the time-based backstop by one beat (capped). A player
   who keeps looking keeps arka honest longer; a player who delegated their eyes
   gets blindsided. Vigilance never offsets delegation-driven drift.

This is the thesis as difficulty, not as a cutscene: the player who stopped
looking pays for it; the player who kept checking has a fighting chance.

## Drift Stages

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

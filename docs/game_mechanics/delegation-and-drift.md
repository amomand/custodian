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

- Manual control answers **one control per beat**. The player picks the single
  intervention they can afford and spends the beat on it.
- arka takes a **whole panel at once**. When it handles coolant or cryostasis, it
  addresses several metrics in a single beat.

Because telemetry degrades on several axes at once (see the trend arrows and the
`ATTENTION` line in the objective block), a hands-on player constantly falls
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

## Standing Delegation

One-shot delegation hands arka a panel for a single beat. Standing delegation
hands arka a whole system *between* watches. The player runs `assign coolant`
(or cryostasis, or navigation); from then on, every beat that passes, arka makes
one gentle automatic adjustment to that system until the player runs
`release coolant`.

Standing delegation is meant to be the more tempting form. It reduces cognitive
load: there is less to read, fewer bars to scan, and the UI can quiet the panel
entirely (the focus/zen view). Early, while arka's account is still
accurate, the automatic adjustments quietly keep the panel inside its box and
improve outcomes. That is the seduction.

The cost is wired to the same mechanic. Every standing adjustment is a
delegation, so it drives drift exactly like a one-shot hand-over: each tended
system pushes `delegated_controls` once per beat. Hand arka a system early and
its account of that system rots faster, precisely while the player has stopped
looking. Standing delegation never builds manual familiarity, and the player's
hands fall further behind the longer it runs.

Standing delegation is **routine handling only**. It must never make an
irreversible move on the player's behalf:

- Standing navigation keeps arka's recommended route plotted and ready, but never
  commits the jump. The player still calls the jump.
- A manual plot is respected: standing navigation will not override a route the
  player plotted by hand.
- Nothing in standing delegation seals or abandons a sector.

Those guards keep the ending the player's history, not arka's fault.

### Focus mode is whole-ship standing delegation

Focus ("take the watch" / zen) mode is the whole-ship form of standing
delegation. Entering it (clicking arka or `focus`) hands arka every system at
once and quiets the desk; mechanically it is standing delegation over all of
coolant, cryostasis, and navigation, so it carries the same honest cost — drift
pressure each beat, no manual familiarity — and the same irreversible-move guard.
Its only added pull is calm: there is simply less to read, because the player
chose to stop looking. The raw layer that could contradict arka is one click (or
`Esc`) away, and the focus dwell is recorded as a reliance signal. Because it
tends every system, focus mode drives drift quickly; it is meant to be dipped
into, not lived in. See `../ui/zen-mode.md` and `trust-ledger.md`.

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

## Open UI Hypothesis: Delegation Quiets The HUD

Not implemented yet, but worth holding onto for playtest feel:

Delegation might make the full HUD disappear for that beat. Instead of showing
every metric again after `delegate`, the terminal could clear down to a sparse
arka acknowledgement and perhaps a compact advisory line. All that panel noise
goes away because arka is dealing with it.

This could make delegation feel attractive in the player's hands, not just in
the numbers. The relief is immediate: less reading, fewer bars, no urgent scan
of every failing metric. The cost is the same relief. The player no longer sees
what changed unless they deliberately ask for `status` or read a raw panel.

Design questions:

- Does hiding the HUD after delegation make arka feel usefully competent, or
  does it make the interface feel withholding?
- Should `status` bring the whole HUD back without advancing time, or should
  regaining the raw picture cost a beat?
- Should the HUD vanish for both coolant and cryostasis delegation, or only when
  arka takes the panel most relevant to the current attention line?
- During active crises, should arka still suppress the HUD, or would that make
  late failure feel unfair rather than seductive?
- Does this make transcripts harder to review, and if so do developer reports
  need a fuller hidden trace?

Boundary:

The HUD going quiet must be presentation only. Raw telemetry still belongs to
deterministic state, and arka still must not become the source of ship truth.

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

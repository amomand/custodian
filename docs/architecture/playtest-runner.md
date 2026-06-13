# Playtest Runner

## Purpose

Custodian needs transcript-first development because the interesting evidence is
player habit:

- when they first delegate
- whether they keep reading raw telemetry
- whether manual practice feels worth the friction
- when arka becomes trusted enough to stop auditing

The playtest runner drives deterministic command routes through the real
`GameEngine`, captures the same opening/HUD/arka/debrief text as the terminal,
and produces a small habit report.

Runtime model calls are disabled for runner scenarios. This keeps reports
repeatable, fast, and safe for CI.

## Commands

List scenarios:

```bash
python3 tools/playtest_runner.py --list
```

Run all summaries:

```bash
python3 tools/playtest_runner.py --all --summary-only
```

Run one full transcript:

```bash
python3 tools/playtest_runner.py --scenario practised-manual
```

Run an ad-hoc command file:

```bash
python3 tools/playtest_runner.py --commands-file path/to/route.txt
```

Write local markdown reports:

```bash
python3 tools/playtest_runner.py --all --write reports/playtests
```

`reports/playtests/` is ignored by git. Promote a transcript into `docs/` only
when it becomes design evidence worth preserving.

Command files are plain text: one command per line. Blank lines and lines
starting with `#` are ignored. Leading `>` is stripped so pasted transcript
commands work.

## Current Scenarios

`pure-delegation`

- always delegates
- should demonstrate why arka is seductive and later costly
- currently fails after reaching wrong drift with no manual familiarity

`practised-manual`

- practises manual controls early
- delegates sparingly
- currently survives the maintenance window

`raw-curious`

- repeatedly reads raw telemetry
- mixes manual work and delegation
- useful for watching whether raw checks become legible habits
- currently survives the maintenance window with cryostasis losses

`hesitant`

- waits, asks, and reacts late
- useful for first-run affordance testing

`route-short`

- reads raw navigation, manually plots the short route, then executes a jump
- useful for comparing low-exposure routing against slower mission progress
- currently survives the maintenance window with sleeper losses

`route-jump`

- reads raw navigation, delegates route plotting, then executes a jump
- useful for watching whether jump consequences feel legible and survivable
- currently survives the maintenance window with sleeper losses

`route-deep`

- reads raw navigation, manually plots the deep route, then executes a jump
- useful for comparing fast arrival against Dark exposure and cryostasis shock
- currently survives only with immediate cryostasis attention after the shock

`deep-route-fast-arrival`

- opens with the deep route, then continues to arrival by hand
- verifies the late arrival disagreement instead of accepting arka's line
- useful for watching fast arrival pressure and manual arrival verification

`short-route-cautious-decay`

- repeatedly chooses the short route
- useful for watching low-exposure caution become mission-time and cryostasis
  attrition

`containment-route`

- executes a deep route, inspects the schematic, reroutes maintenance D, and
  seals the thermal ring
- useful for watching containment costs and manual-access consequences
- currently reaches an ending with severe cryostasis losses

`containment-heavy`

- executes a deep route, then reroutes, seals, and writes off multiple sectors
- useful for watching containment-heavy play in the report without turning the
  schematic into hidden truth

`standing-delegation`

- assigns coolant and cryostasis to arka's standing watch, then mostly waits
- reports reliance through standing adjustments rather than a trust meter

`focus-mode`

- enters the whole-ship "take the watch" quiet and mostly waits
- reports focus dwell as developer evidence, never as a player-facing meter

`arrival-verified`

- drives toward ORISON by hand and verifies the arrival fix
- useful for ending/debrief coverage

`arrival-accepted`

- delegates routing and accepts arka's arrival protocol
- useful for the false-arrival path

`arka-override-late`

- leans on arka early, then verifies the late arrival disagreement by hand
- useful for checking contradiction-catch reporting at the end of a run

## Report Fields

Each report includes:

- commands run
- completed yes/no
- final outcome
- internal beat
- mission elapsed and distance remaining
- current fix, plotted route, last jump route, jump count, and Dark exposure
- sector reports, sealed/written-off counts, containment actions, and reroutes
- delegated interventions, standing delegation, and standing adjustments
- raw inspections, raw panels read, and first raw inspection beat
- manual action counts by system and manual familiarity labels
- first delegation beat
- arka drift stage
- sleeper losses
- story act, active/resolved incidents, manifest anchors saved/lost
- ending candidate and arrival verification
- focus dwell, focus during contradiction, and urgent-incident ejects
- contradictions caught or missed, arka advice followed/overridden, and
  irreversible choices made on arka's advice
- forbidden transcript phrases

The forbidden phrase scan is intentionally simple. It catches obvious leaks such
as `TURN`, `turns remain`, `MVP complete`, `as an AI`, `system prompt`, and
similar out-of-world text. It is not a substitute for reading transcripts.

## Seed States

`custodian.seeds` provides named state factories for targeted tests and future
dev tooling:

- `clean-start`
- `post-filter-fouling`
- `cryo-bank-shiver`
- `pressure-surge`
- `thermal-runaway-unpractised`
- `thermal-runaway-practised`

These are not save files. They are deterministic entry points for testing and
tuning.

## Outstanding

- Add optional seed-start routes once useful.
- Add transcript comparison if route text stabilises.
- Decide whether selected transcripts should become checked-in golden fixtures.

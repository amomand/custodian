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

## Report Fields

Each report includes:

- commands run
- completed yes/no
- final outcome
- internal beat
- mission elapsed and distance remaining
- current fix, plotted route, last jump route, jump count, and Dark exposure
- delegated interventions
- raw inspections
- manual familiarity label
- arka drift stage
- sleeper losses
- forbidden transcript phrases

The forbidden phrase scan is intentionally simple. It catches obvious leaks such
as `TURN`, `turns remain`, `MVP complete`, `as an AI`, `system prompt`, and
similar out-of-world text. It is not a substitute for reading transcripts.

## Seed States

`custodian.seeds` provides named state factories for targeted tests and future
dev tooling:

- `clean-start`
- `post-filter-fouling`
- `pressure-surge`
- `silicate-bloom`
- `thermal-runaway-unpractised`
- `thermal-runaway-practised`

These are not save files. They are deterministic entry points for testing and
tuning.

## Outstanding

- Add optional seed-start routes once useful.
- Add transcript comparison if route text stabilises.
- Decide whether selected transcripts should become checked-in golden fixtures.

# Engine Contracts

## Purpose

This document is the compact contract for future Custodian implementation work.
It points at the current authority boundaries so the graphical operating surface
can grow around the existing game without letting UI, prose, or model calls
become ship truth.

The production direction lives in `docs/production/codex-direction-phase4.md`.
The interpreter-specific AI boundary lives in `docs/architecture/ai-interpreter.md`.

## Canonical Flow

Player input follows one path:

```text
terminal or web input -> GameEngine.handle() -> ArkaInterpreter.interpret()
-> Intent -> deterministic dispatch -> StepResult
```

The terminal CLI prints `StepResult.messages`. A future web server should store
session state and expose snapshots, but it should still route commands through
the same engine path unless there is an explicit, tested reason not to.

## Truth Owners

`src/custodian/models.py` owns serialisable state dataclasses:

- reactor coolant telemetry,
- cryostasis telemetry,
- mission clock,
- navigation options and current fix,
- spatial sectors and containment,
- hidden manual familiarity,
- delegation and raw-inspection counters,
- the behaviour ledger (`BehaviourLedger`): delegated/manual/raw actions by
  system or panel, standing delegations, standing-adjustment count, and first
  delegation/raw timing,
- crisis, outcome, and command history.

`src/custodian/engine.py` owns state transitions:

- advancing time,
- changing telemetry,
- manual control effects,
- delegated control effects,
- route plotting and jump execution,
- spatial drift and containment consequences,
- cryostasis losses,
- crisis timers and crisis resolution,
- terminal outcome checks,
- command history records.

`src/custodian/arka.py` owns deterministic arka-facing summaries and drift-stage
phrasing. It may misframe or omit according to game state. It should not mutate
state.

`src/custodian/telemetry.py` and `src/custodian/objectives.py` render
deterministic state for the player. They should not invent new truth.

`src/custodian/narrative.py` owns opening and closing prose. Debriefs may read
hidden state, but should translate behaviour into fiction rather than showing
hidden scores.

`src/custodian/persistence.py` serialises and deserialises `ShipState`. Save/load
should store game state, not UI component state.

`src/custodian/playtest.py` and `tools/playtest_runner.py` run scripted routes
through the same engine and report behaviour for balancing.

## Model Boundary

The runtime model may help with:

- mapping natural text to a known `Intent`,
- short arka replies for conversational or off-script input,
- synonyms and diegetic soft denials.

The runtime model must not own:

- raw telemetry,
- route risk or current fix,
- jump consequences,
- sector symptoms or containment truth,
- sleeper losses,
- crisis timers or crisis resolution,
- manual familiarity,
- arka drift stage,
- authored arka omissions or contradictions,
- ending conditions.

If the model suggests a state change, the engine should ignore it. The engine
executes known intent actions only.

## Behaviour Contracts

- Manual familiarity improves through manual actions only.
- Delegation should be useful early, should not increase manual familiarity, and
  should be recorded as behaviour.
- Behaviour (delegation, manual, raw, standing delegation, first-reliance timing)
  is recorded in the ledger from the one canonical command path, so UI buttons
  and typed commands land in the same record. The ledger counts stay out of
  normal UI snapshots; there is no visible trust meter.
- Standing delegation is routine handling only. arka may tend an assigned system
  between watches, but it must not make irreversible moves on the player's
  behalf: standing navigation keeps a route ready but never commits the jump, and
  standing delegation never seals or abandons a sector. Irreversible choices stay
  the player's to authorise.
- Focus ("take the watch" / zen) mode is whole-ship standing delegation plus a
  quiet view. It carries the same cost and the same irreversible-move guard,
  records its dwell in the ledger, and deliberately hides raw telemetry, dense
  controls, and command-output clutter while held. The audit path is that the
  full desk returns immediately on the player's command (or Escape): consensual
  hiding, never corruption hiding the way back.
- Reading raw telemetry may delay arka drift pressure, but does not make the
  player more manually fluent.
- arka drift is deterministic. It is not ordinary model unreliability.
- Raw telemetry is the audit path. It should remain learnable, even when noisy.
- Physical sectors can be sealed, abandoned, or rerouted. arka has no physical
  sector and cannot be spatially contained.
- Irreversible choices should remain the player's responsibility unless the
  maintainer explicitly adds and tests an emergency delegation rule.
- The Dark is expressed through effects, symptoms, route risk, and contradiction.
  It should not become a clean public progress meter.

Current implementation note: terminal navigation telemetry still exposes Dark
exposure values as a playtest shorthand. The future web snapshot should avoid
surfacing those exact internals in normal player UI unless that design decision
is made deliberately.

## Web Growth Contracts

The browser layer should wrap the engine, not fork it.

Server/session code should:

- keep one mutable `ShipState` or future run wrapper per session,
- dispatch text commands and structured UI actions through the same engine path
  where practical,
- persist serialisable game state rather than client component state,
- expose transcript/history from engine records,
- keep developer-only data behind explicit dev affordances.

Snapshot code should:

- project renderable state from deterministic state,
- provide raw panels from state, not arka prose,
- provide arka advisory from deterministic arka summaries or constrained arka
  voice,
- expose action specs without teaching the client hidden rules,
- hide trust, manual familiarity numbers, exact hidden exposure internals, and
  future story flags from normal player UI.

Client code should treat snapshots as display data. It should not reconstruct
simulation truth or decide consequences.

## Checks

The core checks remain:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests main.py
```

Tests must pass without an API key. Model-backed behaviour should use fake
clients or deterministic fallback paths.

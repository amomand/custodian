---
name: custodian-simulation-truth-review
description: Use as an optional review lens for Custodian changes that touch model boundaries, telemetry, arka summaries, drift, manual familiarity, crisis logic, or docs/code contracts. It protects the thesis without freezing early design.
---

# Custodian Simulation Truth Review

Use this as a local review lens when a change touches game state, AI
interpretation, arka summaries, telemetry, crisis logic, manual familiarity,
delegation, route/system mechanics, tests, configuration, or architecture docs.

This is not a gate. It exists because Custodian's central risk is subtle: if the
model starts inventing ship truth, the game stops being about delegation and
becomes ordinary chatbot unreliability.

## Current Lens

Look for changes that might accidentally make any of these true:

- The model invents or mutates raw telemetry.
- The model advances turns, resolves crises, changes sleeper losses, changes
  manual familiarity, or updates reactor state.
- arka wrongness becomes unplanned model drift instead of deterministic game
  drift.
- Delegation increases manual familiarity.
- Reading raw telemetry increases manual familiarity.
- Critical crisis outcomes depend on generated prose.
- Docs describe commands, model defaults, env vars, state transitions, or AI
  boundaries differently from implementation.

## Useful Anchors

- `src/custodian/models.py`
- `src/custodian/engine.py`
- `src/custodian/arka.py`
- `src/custodian/arka_interpreter.py`
- `docs/architecture/ai-interpreter.md`
- `design.md`
- `docs/roadmap.md`
- `tests/**`

## Review Procedure

1. Inspect changed files first.
2. Trace input through intent parsing into engine state if needed.
3. Read nearby docs only to confirm a concrete mismatch.
4. Ignore docs that are merely incomplete or exploratory.
5. Prefer "this may be crossing the boundary" over hard failure language unless
   the model truly owns ship truth.

## Output

Use this shape:

```markdown
Simulation Truth Review: PASS | QUESTIONS | CONCERNS

What I checked:
- ...

Questions:
- None.

Concerns:
- None.

Notes:
- ...
```

Use `PASS` when nothing actionable appears. Use `QUESTIONS` for uncertain design
boundary issues. Use `CONCERNS` for concrete model/simulation boundary drift.

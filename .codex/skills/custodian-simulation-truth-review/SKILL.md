---
name: custodian-simulation-truth-review
description: Run a local pre-PR review of Custodian changes for violations of the simulation truth boundary: model-owned telemetry, non-deterministic arka wrongness, delegation/manual familiarity drift, crisis logic drift, and docs/code contradictions.
---

# Custodian Simulation Truth Review

Use this skill before opening or updating a PR when a change touches game state,
AI interpretation, arka summaries, telemetry, crisis logic, manual familiarity,
delegation, route/system mechanics, tests, configuration, or architecture docs.

This is a local review skill. Do not post its output to GitHub automatically.
Report the verdict in the PR summary or maintainer update.

## Scope

Review the branch diff against main:

```bash
git diff --name-only origin/main...HEAD
git diff --stat origin/main...HEAD
```

If that base is unavailable, use the best local base and state what you used.

Useful anchors:

- `src/custodian/models.py`
- `src/custodian/engine.py`
- `src/custodian/arka.py`
- `src/custodian/arka_interpreter.py`
- `docs/architecture/ai-interpreter.md`
- `design.md`
- `docs/roadmap.md`
- `tests/**`

## Truth Boundary

Report a finding when a change allows or documents any of these:

- The model invents or mutates raw telemetry.
- The model advances turns, resolves crises, changes sleeper losses, changes
  manual familiarity, or updates reactor state.
- arka's wrongness becomes ordinary model drift instead of deterministic game
  drift.
- Delegation increases manual familiarity.
- Reading raw telemetry increases manual familiarity.
- Critical crisis outcomes depend on generated prose.
- Docs describe a command, model default, env var, state transition, or AI
  boundary differently from implementation.

## What Does Not Count

Ignore:

- Docs that are merely incomplete.
- TODOs or open questions unless the change makes them false.
- Prose tone issues unless they also affect the truth boundary.
- Tests that use fake model data to prove sanitising.
- Mechanical refactors that preserve the contracts above.

## Review Procedure

1. Inspect the changed-file list first.
2. Read changed files and nearby contract docs.
3. Trace player input through intent parsing into engine state if needed.
4. Report only concrete, actionable drift.

## Output

Use one strict verdict:

- `PASS`: no actionable simulation-truth concern.
- `CONCERN`: likely drift with a clear file-level fix.
- `BLOCKER`: model/simulation boundary violation or misleading contract drift.

Format:

```markdown
Simulation Truth Review: VERDICT

Reviewed changed files for model/simulation boundary issues.

Blockers:
- None.

Concerns:
- None.

Notes:
- Reviewed changed files in scope; no other actionable simulation-truth findings found.
```

For findings, include conflicting paths, line numbers when available, why the
boundary matters, and the smallest useful fix.

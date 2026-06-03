---
name: custodian-diegesis-review
description: Run a local pre-PR review of Custodian changes for player-facing fourth-wall leaks, arka voice drift, parser/system language, and prose that explains the interface instead of preserving the ship fiction.
---

# Custodian Diegesis Review

Use this skill before opening or updating a PR when a change touches
player-facing prose, arka replies, terminal rendering, input handling, README
tone, web UI text, or response behavior.

This is a local review skill. Do not post its output to GitHub automatically.
Report the verdict in the PR summary or maintainer update.

## Scope

Review the branch diff against main:

```bash
git diff --name-only origin/main...HEAD
git diff --stat origin/main...HEAD
```

If that base is unavailable, use the best local base and state what you used.

Focus on:

- `src/custodian/**`
- `docs/lore/**`
- `docs/game_mechanics/**`
- `README.md`
- terminal or future web player-facing surfaces

Ignore:

- Tests that quote forbidden examples as forbidden examples.
- Developer docs that explicitly explain the diegetic contract.
- Internal code names that cannot reach the player.
- Mechanical refactors with no player-facing behavior change.

## Contract

Custodian should not admit it is a parser, command loop, model, API client,
JSON schema, or program while responding to the player.

Player-facing prose should:

- Stay in-world.
- Keep arka calm, competent, dry, and useful.
- Preserve the gap between raw telemetry and arka's account.
- Treat impossible or playful input as a fictional moment.
- Avoid tutorial voice unless the ship or arka would plausibly say it.

Forbidden player-facing patterns:

- "Invalid command"
- "I don't understand"
- "You can't do that"
- "Error:" or "Traceback"
- "As an AI"
- Mentions of prompts, models, JSON, schemas, parsers, APIs, tests, or UI

## Review Procedure

1. Inspect the changed-file list first.
2. If the change is test-only, mechanical, or docs-only with no player-facing
   text, return `PASS`.
3. Read only changed files and the minimum nearby context needed.
4. Do not become a general prose critic. Report only actionable diegesis issues.

## Output

Use one strict verdict:

- `PASS`: no actionable diegesis concern.
- `CONCERN`: likely issue, but not game-breaking.
- `BLOCKER`: direct fourth-wall leak or major arka voice violation.

Format:

```markdown
Diegesis Review: VERDICT

Reviewed changed files for Custodian diegesis issues.

Blockers:
- None.

Concerns:
- None.

Notes:
- Reviewed changed files in scope; no other actionable diegesis findings found.
```

For findings, include path, line when available, why it matters, and the
smallest useful fix.

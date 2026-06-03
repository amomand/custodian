---
name: custodian-diegesis-review
description: Use as an optional review lens for Custodian changes that touch player-facing prose, arka voice, terminal/web responses, or command handling. It looks for fourth-wall leaks and arka voice drift without blocking early exploration.
---

# Custodian Diegesis Review

Use this as a local review lens when a change touches player-facing prose, arka
replies, terminal rendering, input handling, README tone, future web UI text, or
response behavior.

This is not a gate. Early Custodian is allowed to follow interesting edges. The
skill should surface likely diegesis issues and useful questions, not flatten
experiments into a house style too soon.

## Current Lens

Player-facing prose should usually:

- Stay in-world.
- Keep arka calm, useful, dry, and competent.
- Preserve the gap between raw telemetry and arka's account.
- Treat impossible or playful input as a fictional moment.
- Avoid software/interface language unless it is clearly diegetic ship language.

Watch for:

- "Invalid command"
- "I don't understand"
- "You can't do that"
- "Error:" or "Traceback"
- "As an AI"
- Mentions of prompts, models, JSON, schemas, parsers, APIs, tests, or UI in
  player-facing text
- arka sounding like a villain, therapist, tutorial popup, or generic assistant

## Review Procedure

1. Inspect changed files first.
2. Read only the changed player-facing text and nearby context.
3. Ignore internal docs, tests quoting forbidden examples, and code names that
   cannot reach the player.
4. Prefer questions and small fixes over broad style critique.

## Output

Use this shape:

```markdown
Diegesis Review: PASS | QUESTIONS | CONCERNS

What I checked:
- ...

Questions:
- None.

Concerns:
- None.

Notes:
- ...
```

Use `PASS` when nothing actionable appears. Use `QUESTIONS` when the issue is
mostly taste or direction. Use `CONCERNS` only for concrete fourth-wall leaks or
strong arka voice drift.

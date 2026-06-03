# Codex Instructions

Read this before making code, narrative, or documentation changes in this repo.

## Project

**Custodian** is a terminal-first sci-fi horror game about the cost of
delegation. The player is the sole waking custodian aboard a colony ship. arka,
the ship's operational intelligence, is useful, comforting, and increasingly
unsafe as a source of truth.

The current playable slice is intentionally narrow: one ship system, reactor
coolant. Do not expand to a full ship unless the task explicitly calls for it.

## Commands

```bash
# Run the terminal game
python3 main.py

# Run with deterministic AI fallback
CUSTODIAN_AI=off python3 main.py

# Run with fallback diagnostics
CUSTODIAN_DEBUG=1 python3 main.py

# Run tests
PYTHONPATH=src python3 -m unittest discover -s tests

# Compile/import check
python3 -m compileall src tests main.py
```

For model-backed arka input, create a virtual environment and install
`requirements.txt`. Tests must pass without an API key.

## Source Of Truth

- `README.md` - player/maintainer overview.
- `design.md` - current MVP design.
- `docs/roadmap.md` - path toward the larger game.
- `docs/lore/arka.md` - arka character and runtime voice capsule.
- `docs/architecture/ai-interpreter.md` - AI/parser/simulation boundary.
- `docs/original-idea.md` - copied seed idea; preserve as reference.

## Core Contracts

### The Model Interprets, The Ship Decides

The model may classify free text and supply short arka replies. It must not own
reactor physics, raw telemetry, route risk, sleeper loss, arka drift, crisis
timers, or manual familiarity.

### Raw Telemetry Is Sacred

Raw telemetry must come from deterministic state, never from generated prose.
arka may summarise, omit, soften, or contradict only when deterministic drift
logic says it can.

### Manual Familiarity Is Earned By Manual Work

Delegating to arka must not increase manual familiarity. Reading raw telemetry
must not increase it either. The player gets better with the panel by using the
panel.

### arka Stays arka

arka is competent reassurance, not a villain monologue. The horror arrives when
the same helpful voice no longer matches reality.

### No Fourth Wall In Player-Facing Output

No "invalid command", parser talk, model talk, JSON/schema talk, API talk, or
implementation explanation in player-facing responses. Failures and nonsense
input should be answered through arka or the ship.

## Changing arka

Change `docs/lore/arka.md` first when adjusting arka's voice. The interpreter
loads the runtime voice capsule from that document. Update tests or prompt
expectations only after the design surface is clear.

## Review Workflow

Before opening or updating a PR, run the checks above. Then run the relevant
local review skills:

- `.codex/skills/custodian-diegesis-review/SKILL.md` for player-facing prose,
  arka replies, CLI text, README tone, and response behavior.
- `.codex/skills/custodian-simulation-truth-review/SKILL.md` for AI boundary,
  telemetry, drift, manual familiarity, crisis logic, and docs/code contracts.

Local review skills are disciplined self-review. They do not replace maintainer
judgment.

## Borrowing From The Cabin

Borrow patterns proudly, but do not cargo-cult them.

Good to borrow now:

- AGENTS-style repo contracts.
- Local diegesis and truth-boundary review skills.
- Minimal CI.
- Transcript-first playtesting, soon.

Borrow later:

- Web session server.
- Fly deployment.
- Seed saves.
- Rich playtest runner.
- Broader event bus.

Avoid for now:

- Multiple interacting systems before coolant is honest.
- Heavy deployment plumbing before a web surface exists.
- Letting model replies become authored story beats.

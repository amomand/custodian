# Custodian

You are the only waking custodian aboard a colony ship.
The reactor is warm.
The sleepers are not.
arka says it can handle the coolant loop.

It usually can.

---

## What Is This?

**Custodian** is a terminal sci-fi horror prototype about the cost of
delegation. The first MVP proves the thesis with one ship system: reactor
coolant.

The player can work the coolant panel by hand. It is real, useful, and a
little fiddly. Or the player can ask `arka` to handle it. Early on, arka is
better. Later, arka's account of the ship starts to drift, and the player may
discover that the manual skill they need is the skill they chose not to build.

Core ideas:

- Terminal-first play, no map, no UI chrome
- Optional AI-powered natural language input for arka
- Deterministic reactor state and crisis logic
- Raw telemetry as truth-adjacent, slower than reassurance
- arka summaries that move from accurate to interpretive, selective, and wrong
- Hidden manual familiarity gained only by manual work
- A short 20-30 turn coolant maintenance arc

---

## Quick Start

Requirements: Python 3.11+

From the repo root:

```bash
python3 main.py
```

That works without an API key. In that mode, arka uses deterministic fallback
rules for commands and off-script replies.

For model-backed arka input, use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

Your `.env` file should live at the repo root and is ignored by git:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=none
CUSTODIAN_AI=on
```

To see why arka has fallen back to deterministic mode:

```bash
CUSTODIAN_DEBUG=1 python3 main.py
```

---

## Development Checks

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
printf 'can you handle it?\nquit\n' | python3 main.py
```

The tests do not require an API key. Model behavior is covered with fake-client
tests so the suite stays fast and local.

---

## Features

- **Natural language arka layer** - free text becomes a structured `Intent`
- **Deterministic fallback** - the game remains playable without credentials
- **Diegetic command handling** - no invalid-command voice
- **Reactor coolant model** - temperature, pressure, flow, impurity, valve skew, reserve
- **Delegation tracking** - arka control affects drift, not a visible trust meter
- **Manual practice** - hidden familiarity improves hand control under pressure
- **Authored crisis beats** - key turns and arka drift are designed, not improvised
- **AI hardening** - model replies are sanitised before they reach the terminal

---

## Lore And Design Docs

The original project note is preserved in `docs/original-idea.md`.

Current working docs:

- `design.md` - MVP thesis, loop, systems, and turn arc
- `docs/roadmap.md` - path from MVP to larger realisation
- `docs/lore/arka.md` - arka character and runtime voice capsule
- `docs/architecture/ai-interpreter.md` - AI boundary and intent pipeline
- `docs/architecture/project-operating-system.md` - CI, local skills, and repo rules

Change arka's character in markdown first. The interpreter reads the runtime
voice capsule from `docs/lore/arka.md`, so voice iteration should usually start
there rather than inside Python.

---

## Project Layout

```text
custodian/
├── main.py                         # Simple terminal entry point
├── requirements.txt                # Optional OpenAI dependency
├── design.md                       # MVP design source
├── docs/
│   ├── architecture/
│   │   └── ai-interpreter.md       # AI/parser/simulation boundary
│   ├── lore/
│   │   └── arka.md                 # arka voice and character notes
│   └── original-idea.md            # Copied seed idea
├── src/custodian/
│   ├── engine.py                   # Deterministic state transitions
│   ├── arka.py                     # arka summary drift
│   ├── arka_interpreter.py         # Intent parser and optional model call
│   ├── config.py                   # .env loading
│   ├── models.py                   # ShipState and reactor telemetry
│   └── cli.py                      # Terminal loop
└── tests/                          # Unit tests and AI boundary tests
```

---

## Configuration

Environment variables:

- `OPENAI_API_KEY` - Enables model-backed arka interpretation
- `OPENAI_MODEL` - Default: `gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT` - Default: `none`
- `CUSTODIAN_AI=off` - Force deterministic fallback
- `CUSTODIAN_DEBUG=1` - Print AI fallback diagnostics to stderr

The Cabin used `gpt-5.4-mini` for this kind of diegetic parser/voice work.
Custodian keeps that default because arka needs fast structured interpretation
and tone, while the ship simulation does the actual reasoning.

---

## Design Philosophy

**Raw telemetry is sacred.** The model may never invent reactor numbers. It may
only see the arka-facing summary and context the engine chooses to provide.

**The model interprets; the ship decides.** Player text becomes an intent. Only
the deterministic engine advances turns, mutates coolant, resolves crises,
records familiarity, or kills sleepers.

**Delegation must be genuinely attractive.** arka should be useful and pleasant
before it becomes dangerous. If manual work is fake-hard, the thesis breaks. If
arka is obviously bad early, the thesis also breaks.

**No fourth wall.** Errors, refusals, impossible inputs, and help should arrive
through arka or the ship, not through software chatter.

---

## Contributing

Keep it competent. Make arka helpful before making it unsettling. Preserve the
gap between raw telemetry and arka's account of it. If you add a mechanic,
update the relevant docs in `docs/` so the game remains legible to future
maintainers and future language models.

---

## Troubleshooting

If arka keeps saying it is interpreting everything as interest in the coolant
loop, the model path is not active.

Check:

1. `.env` exists in the repo root and contains `OPENAI_API_KEY`
2. The virtual environment is active, if using one
3. `python3 -m pip install -r requirements.txt` has been run
4. `CUSTODIAN_DEBUG=1 python3 main.py` for a specific fallback reason

The deterministic fallback is deliberately boring. arka is more interesting
when the model path is alive, but the reactor should behave the same either way.

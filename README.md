# Custodian

You are the only waking custodian aboard a colony ship.
The reactor is warm.
The sleepers are not.
arka says it can handle the coolant loop.
It says the sleepers are quiet.

It usually can.

---

## What Is This?

**Custodian** is a terminal sci-fi horror prototype about the cost of
delegation. The current terminal slice proves the thesis with reactor coolant
and cryostasis viability.

Phase 0 is concluded. Phase 1A-D is now represented in the terminal loop:
coolant is shorter, cryostasis is live, the systems can pressure each other, and
runs can be saved and resumed. Phase 2A starts the mission-pressure layer:
status now includes elapsed mission time, distance remaining, ship wear, and
long-duration cryostasis decay. Phase 2B adds route options, raw navigation, and
manual or delegated plotting. Phase 2C/D adds jump execution, route
consequences, and drift-sensitive arka route advice. Phase 2E adds a lightweight
current navigation fix and route comparison playtests, closing the route layer
before spatial ship work. Phase 3 adds the terminal-native ship schematic,
qualitative sector symptoms, containment choices, and the arka asymmetry:
physical sectors can be sealed, arka cannot. A course correction makes the goal
legible: every status readout opens with an objective block (goal, horizon, the
metric failing fastest this beat) and the HUD carries trend arrows. The first
browser shell now wraps the same engine in a local web session with transcript,
command input, status output, and save/load.

The player can work the coolant and cryostasis panels by hand. They are real,
useful, and a little fiddly. Or the player can ask `arka` to handle one panel
while they work the other. Early on, arka is better. Later, arka's account of
the ship starts to drift, and the player may discover that the manual skill they
need is the skill they chose not to build.

Core ideas:

- Terminal-first engine with a local browser shell
- Optional AI-powered natural language input for arka
- Deterministic reactor and cryostasis state
- Deterministic mission clock with ship wear and cryostasis decay
- Deterministic route options with current fix, plotting, delegation, and jump execution
- Deterministic ship sectors with qualitative symptoms and containment choices
- Raw telemetry as truth-adjacent, slower than reassurance
- arka summaries that move from accurate to interpretive, selective, and wrong
- Hidden manual familiarity gained only by manual work
- A short two-system maintenance arc

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
CUSTODIAN_CLEAR=on
```

To see why arka has fallen back to deterministic mode:

```bash
CUSTODIAN_DEBUG=1 python3 main.py
```

To play the same slice through the local browser shell:

```bash
PYTHONPATH=src python3 -m custodian.web_server --no-ai
```

Then open `http://127.0.0.1:8765`.

---

## Development Checks

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
printf 'can you handle it?\nquit\n' | python3 main.py
python3 tools/playtest_runner.py --all --summary-only
python3 tools/playtest_runner.py --commands-file path/to/route.txt
```

The tests do not require an API key. Model behavior is covered with fake-client
tests so the suite stays fast and local.

Developer-only terminal diagnostics use a colon prefix:

```bash
:debug
:metrics
:help
```

---

## Features

- **Natural language arka layer** - free text becomes a structured `Intent`
- **Deterministic fallback** - the game remains playable without credentials
- **Diegetic boot sequence** - the prototype now opens as an in-world shell
- **Event refreshes** - interactive terminals clear on launch and major pressure beats
- **Legible objective block** - every status opens with goal, horizon, and the metric failing fastest
- **Mission clock** - elapsed mission time, distance remaining, ship wear, and cryostasis decay
- **Navigation options** - short, medium, and deep routes can be inspected, plotted, and jumped
- **Current fix** - the ship reports where the latest jump leaves it without becoming a map
- **Ship schematic** - sectors report qualitative symptoms without exposing a Dark percentage
- **Containment choices** - seal, abandon, and reroute physical sectors, with local costs
- **Browser session shell** - local web play through the same engine command path
- **Trend-aware HUD** - per-metric arrows show what is moving toward danger this beat
- **Delegation as throughput** - one manual control per beat, or a whole panel via arka
- **Coolant HUD** - telemetry is shown separately from arka's summary
- **Cryostasis HUD** - sleeper viability is visible outside arka's voice
- **Run debrief** - endings reflect manual practice, delegation, and raw checks
- **Diegetic command handling** - no invalid-command voice
- **Reactor coolant model** - temperature, pressure, flow, impurity, valve skew, reserve
- **Cryostasis model** - bank temperature, neural stability, sedative balance, pod faults, sleepers at risk
- **Delegation tracking** - arka control drives drift, mitigated by raw-reading vigilance, not a visible trust meter
- **Manual practice** - hidden familiarity improves hand control under pressure
- **Authored crisis beats** - pressure points and arka drift are designed, not improvised
- **Save and resume** - `:save` / `:load` serialise the run; command history is recorded
- **Transcript playtests** - deterministic routes report delegation, raw checks, drift, and outcome
- **Ad-hoc route files** - pasted command files can become playtest reports
- **AI hardening** - model replies are sanitised before they reach the terminal

---

## Lore And Design Docs

The original project note is preserved in `docs/original-idea.md`.

Current working docs:

- `design.md` - MVP thesis, loop, systems, and maintenance arc
- GitHub issues - the live backlog and long-range plan (the old `docs/roadmap.md` has been retired)
- `docs/production/codex-direction-phase4.md` - producer direction for the first graphical vertical slice
- `docs/game_mechanics/opening-sequence.md` - boot text and run debrief notes
- `docs/game_mechanics/reactor-coolant.md` - coolant telemetry, actions, and pressure beats
- `docs/game_mechanics/cryostasis-viability.md` - cryostasis telemetry, actions, and sleeper pressure
- `docs/game_mechanics/manual-familiarity.md` - hidden practice mechanic
- `docs/game_mechanics/delegation-and-drift.md` - arka dependence and summary drift
- `docs/game_mechanics/objectives-and-priority.md` - objective block, horizon, and per-beat priority
- `docs/game_mechanics/mission-clock.md` - mission time, distance, wear, and cryostasis decay
- `docs/game_mechanics/routing.md` - route options, current fix, plotting, and jump consequences
- `docs/game_mechanics/spatial-containment.md` - schematic sectors, symptoms, and containment
- `docs/architecture/save-load.md` - run serialisation and command history
- `docs/architecture/web-session-api.md` - local browser session endpoints
- `docs/lore/arka.md` - arka character and runtime voice capsule
- `docs/architecture/engine-contracts.md` - canonical truth owners and implementation boundaries
- `docs/architecture/ai-interpreter.md` - AI boundary and intent pipeline
- `docs/architecture/playtest-runner.md` - deterministic transcript workflow
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
│   │   ├── engine-contracts.md     # Canonical truth owners and boundaries
│   │   ├── ai-interpreter.md       # AI/parser/simulation boundary
│   │   ├── web-session-api.md      # Browser shell API and session contract
│   │   └── playtest-runner.md      # Deterministic transcript workflow
│   ├── game_mechanics/
│   │   ├── delegation-and-drift.md # arka dependence and drift notes
│   │   ├── manual-familiarity.md   # Hidden practice mechanic
│   │   ├── opening-sequence.md     # Boot/debrief design notes
│   │   ├── reactor-coolant.md      # Coolant telemetry and pressure beats
│   │   ├── cryostasis-viability.md # Cryostasis telemetry and sleeper pressure
│   │   ├── mission-clock.md        # Mission time, distance, wear, decay
│   │   ├── routing.md              # Route options, current fix, jumps
│   │   └── spatial-containment.md  # Sectors, symptoms, containment
│   ├── lore/
│   │   └── arka.md                 # arka voice and character notes
│   ├── production/
│   │   └── codex-direction-phase4.md # Producer direction for graphical slice
│   └── original-idea.md            # Copied seed idea
├── src/custodian/
│   ├── engine.py                   # Deterministic state transitions
│   ├── arka.py                     # arka summary drift
│   ├── arka_interpreter.py         # Intent parser and optional model call
│   ├── config.py                   # .env loading
│   ├── models.py                   # ShipState and system telemetry
│   ├── narrative.py                # Opening and closing terminal text
│   ├── playtest.py                 # Deterministic scenario runner core
│   ├── seeds.py                    # Named simulation entry states
│   ├── telemetry.py                # Compact terminal HUDs
│   ├── web_session.py              # Browser session lifecycle
│   ├── web_server.py               # Local HTTP server
│   ├── web_static/                 # Minimal browser client
│   └── cli.py                      # Terminal loop
├── tests/                          # Unit tests and AI boundary tests
└── tools/
    └── playtest_runner.py          # Scenario transcript CLI
```

---

## Configuration

Environment variables:

- `OPENAI_API_KEY` - Enables model-backed arka interpretation
- `OPENAI_MODEL` - Default: `gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT` - Default: `none`
- `CUSTODIAN_AI=off` - Force deterministic fallback
- `CUSTODIAN_DEBUG=1` - Print AI fallback diagnostics to stderr
- `CUSTODIAN_CLEAR=off` - Disable interactive launch and event screen clears
- `CUSTODIAN_BOOT=off` - Skip the interactive A.R.K.A boot screen
- `CUSTODIAN_REFRESH=off` - Keep appending every turn instead of refreshing the
  interactive screen after advancing commands
- `CUSTODIAN_COMPLETE=off` - Disable interactive tab completion
- `CUSTODIAN_WEB_LOG=1` - Print local browser shell HTTP request logs

The Cabin used `gpt-5.4-mini` for this kind of diegetic parser/voice work.
Custodian keeps that default because arka needs fast structured interpretation
and tone, while the ship simulation does the actual reasoning.

---

## Design Philosophy

**Raw telemetry is sacred.** The model may never invent reactor numbers. It may
only see the arka-facing summary and context the engine chooses to provide.

**The model interprets; the ship decides.** Player text becomes an intent. Only
the deterministic engine advances internal time, mutates coolant, resolves crises,
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

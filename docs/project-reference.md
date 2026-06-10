# Project Reference

This file holds the maintainer/spec material that used to live in the README.
The README is now short and in arka's voice; the catalogue lives here so nothing
is lost. For how to run each mode, see [`launch-modes.md`](launch-modes.md).

## What the prototype is

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

## Design philosophy

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

The Cabin used `gpt-5.4-mini` for this kind of diegetic parser/voice work.
Custodian keeps that default because arka needs fast structured interpretation
and tone, while the ship simulation does the actual reasoning.

## Contributing

Keep it competent. Make arka helpful before making it unsettling. Preserve the
gap between raw telemetry and arka's account of it. If you add a mechanic,
update the relevant docs in `docs/` so the game remains legible to future
maintainers and future language models.

Change arka's character in markdown first. The interpreter reads the runtime
voice capsule from `docs/lore/arka.md`, so voice iteration should usually start
there rather than inside Python.

## Project layout

```text
custodian/
├── main.py                         # Simple terminal entry point
├── Makefile                        # Convenience targets for each run mode
├── requirements.txt                # Optional OpenAI dependency
├── design.md                       # MVP design source
├── docs/
│   ├── launch-modes.md             # Canonical run commands for every mode
│   ├── project-reference.md        # This maintainer/spec catalogue
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
│   ├── ui/                         # Operating desk and zen-mode notes
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

## Lore and design docs

The original project note is preserved in `original-idea.md`.

Current working docs:

- [`launch-modes.md`](launch-modes.md) - canonical run commands for every mode
- `../design.md` - MVP thesis, loop, systems, and maintenance arc
- GitHub issues - the live backlog and long-range plan (the old `docs/roadmap.md` has been retired)
- `production/codex-direction-phase4.md` - producer direction for the first graphical vertical slice
- `game_mechanics/opening-sequence.md` - boot text and run debrief notes
- `game_mechanics/reactor-coolant.md` - coolant telemetry, actions, and pressure beats
- `game_mechanics/cryostasis-viability.md` - cryostasis telemetry, actions, and sleeper pressure
- `game_mechanics/manual-familiarity.md` - hidden practice mechanic
- `game_mechanics/delegation-and-drift.md` - arka dependence and summary drift
- `game_mechanics/objectives-and-priority.md` - objective block, horizon, and per-beat priority
- `game_mechanics/mission-clock.md` - mission time, distance, wear, and cryostasis decay
- `game_mechanics/routing.md` - route options, current fix, plotting, and jump consequences
- `game_mechanics/spatial-containment.md` - schematic sectors, symptoms, and containment
- `architecture/save-load.md` - run serialisation and command history
- `architecture/web-session-api.md` - local browser session endpoints
- `ui/operating-desk.md` - the graphical operating desk web client
- `ui/cabin-view.md` - the cockpit framing (window, cabin, head-turn) over the desk
- `ui/zen-mode.md` - focus / take-the-watch mode notes
- `lore/arka.md` - arka character and runtime voice capsule
- `architecture/engine-contracts.md` - canonical truth owners and implementation boundaries
- `architecture/ai-interpreter.md` - AI boundary and intent pipeline
- `architecture/playtest-runner.md` - deterministic transcript workflow
- `architecture/project-operating-system.md` - CI, local skills, and repo rules

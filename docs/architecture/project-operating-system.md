# Project Operating System

## Why This Exists

The Cabin is another Alex project, and it contains several useful patterns:

- explicit repo instructions
- local review skills
- CI that exercises tests and playtest scenarios
- docs that make the game legible to humans and agents
- deployment plumbing once a web surface exists

Custodian should borrow with pride, but not blindly. This game has a different
central risk: the in-game AI is not just a narrator. arka is a mechanic. That
means the repo needs guardrails around simulation truth as much as guardrails
around diegesis.

## Borrow Now, Lightly

### AGENTS.md

Custodian should have a short map for coding agents. This is worth having early
because the design has a few invariants that are easy to violate, but it should
not become a constitution while the game is still finding itself:

- raw telemetry never comes from the model
- model output never mutates ship state
- manual familiarity is earned only through manual control
- arka wrongness is deterministic and authored upstream
- player-facing failures stay in-world

### Minimal CI

The current CI should stay small:

- install Python dependencies
- run unit tests
- compile sources
- run a deterministic terminal smoke test

No deployment yet. No web checks until a web surface exists. No heavy lint stack
until style drift becomes a problem.

### Local Review Skills As Lenses

The Cabin's diegesis and continuity skills are a good pattern. Custodian has two
first-pass skills, but they should stay softer than The Cabin's for now:

- diegesis review
- simulation truth review

The second one is Custodian-specific. It watches the AI/simulation boundary
where this game's thesis lives. Both skills should surface questions and
concerns, not block every experiment.

## Borrow Soon

### Transcript Playtest Runner

This should probably be the next infrastructure lift now that the terminal
opening and debrief exist.

Custodian needs transcripts because the design is about player habits. A good
playtest report should show:

- the command transcript
- final outcome
- delegated intervention count
- raw inspection count
- manual familiarity label
- sleeper losses
- whether arka reached interpretive/selective/wrong drift
- forbidden player-facing phrases

This will help detect whether players really stop reading raw telemetry.

### Seed States

Seed states become useful once the coolant arc is stable enough to compare
against itself:

- clean start
- post-filter fouling
- pressure surge
- silicate bloom
- thermal runaway, unpractised
- thermal runaway, practised

### Mechanic Docs

The Cabin's docs are numerous because they make maintenance easier. Custodian
should add docs only as mechanics become real:

- `docs/game_mechanics/reactor-coolant.md`
- `docs/game_mechanics/manual-familiarity.md`
- `docs/game_mechanics/delegation-and-drift.md`
- `docs/game_mechanics/opening-sequence.md` (started)

## Borrow Later

### Web Server And Deployment

The Cabin's FastAPI/Fly shape is likely a good future path, but not yet.

Wait until:

- the terminal loop has save/load or session state worth preserving
- the opening and coolant arc are stable
- the UI needs a browser surface for schematics/readouts

Likely path:

- keep terminal engine canonical
- add `server/` with a session wrapper
- add browser client
- add Dockerfile and Fly config
- add deploy workflow on `main`

### Event Bus

The Cabin's event bus is useful for quests/cutscenes. Custodian may need
something similar once there are multiple systems, route jumps, sector
containment, and endings. It is too much for one coolant loop.

### Copilot Review Loop

The Cabin uses local skills plus Copilot review as an agent PR loop. Custodian
can adopt that once there are regular PRs and enough surface area to justify the
ceremony. For now, optional review lenses and CI are enough.

## Do Not Borrow Yet

- full web deployment
- FastAPI server
- Dockerfile/Fly config
- save manager
- quest/event framework
- broad pytest/dev dependency stack
- unrelated story hosting

Those are good tools, but they would make the current prototype feel heavier
without making it more true.

## Recommended Workflow

For ordinary changes:

1. Read `AGENTS.md`.
2. Make the narrow change.
3. Run tests.
4. Run compile check for code changes.
5. Consider diegesis review for player-facing text.
6. Consider simulation truth review for state, AI, telemetry, or mechanics.
7. Update docs when behavior changes.

For playtest-driven changes:

1. Capture transcript.
2. Mark when the player delegates, reads raw, or practises manual control.
3. Tune mechanics.
4. Keep arka attractive early.
5. Preserve deterministic failure/success routes.

## Open Platform Questions

- Should CI run on push to `main`, pull requests, or both? Current answer: both.
- Do we want `pytest`, or is `unittest` enough for now? Current answer:
  `unittest` is enough.
- When should we add a formatter/linter? Current answer: when style drift costs
  time.
- Where should transcript reports live? Candidate: `reports/playtests/`, ignored
  by git.
- Should local skills become installed personal skills? Not yet. Keep them
  repo-local until their shape stabilises.

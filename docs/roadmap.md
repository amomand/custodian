# Custodian Roadmap

## North Star

Custodian is a sci-fi horror game about the pleasure and cost of delegation.

The player can run the ship manually. Manual control is real, useful, and
effortful. arka is easier. arka is often better. Over time, the player who lets
arka see and act for them becomes dependent on a voice whose account of the ship
is no longer cleanly aligned with raw telemetry.

The finished game should make the player feel this in their hands:

- I could do this myself.
- I do not want to.
- arka is right there.
- arka has always been right before.
- I have forgotten how to do this quickly.
- The raw numbers are still there.
- I am not sure I know how to read them under pressure.

## Current State

The repo currently has a narrow terminal MVP:

- One system: reactor coolant.
- Deterministic `ShipState` and coolant state transitions.
- A compact coolant HUD that carries telemetry outside arka's voice.
- arka summary drift: accurate, interpretive, selective, wrong.
- Optional model-backed arka interpreter for natural-language input.
- Diegetic opening screen and closing debrief.
- Hidden manual familiarity.
- A short scripted maintenance arc.
- Tests around state transitions and AI boundary.
- Markdown docs for the MVP, arka, and the interpreter.

This is the right size. Do not rush to a full ship yet.

## Design Pillars

### Manual Is Real

Manual control should not be theatre. If a patient player learns the systems,
they should be able to make the ship behave. The game can be harsh, but it
should not fake its difficulty by hiding all useful information.

### Delegation Is Seductive

arka should be genuinely helpful, especially early. The player should delegate
because it is sensible, not because the game forces them into it.

### arka Is The Interface

arka is not just a character who comments on menus. arka is the path through
which the player understands the ship. The raw layer is the alternative path,
but it is slower, colder, and less comforting.

### The Model Interprets, The Ship Decides

The in-game AI can classify natural language and speak as arka. It must never
own reactor physics, route risk, sleeper loss, raw telemetry, or authored arka
wrongness. If the model invents truth, the core thesis becomes ordinary chatbot
unreliability.

### Horror Through Continuity

arka should not become a villain voice. The late-game horror comes from the
same competent reassurance continuing after its relationship with reality has
changed.

### Documentation Is Part Of The Game

Markdown is a working surface for both humans and agents. If we want future AI
collaborators to preserve the game, the repo needs docs that describe design
contracts, voice, mechanics, architecture, and open questions.

## Phase 0: Keep The Coolant Slice Honest

Goal: make the current MVP worth replaying and worth studying.

Done:

- Opening screen and boot sequence.
- A short debrief or end screen that reflects delegation and manual practice.
- Interactive launch screen clear.

Build Next:

- Better first-run affordances without tutorialising the trap away.
- Better refresh rules for later scene changes.
- More natural-language synonyms for manual and delegation actions.
- Debug/status commands for development that are clearly non-player-facing.
- A transcript playtest runner like The Cabin's local scenarios.

Tune:

- Delegation should solve early problems cleanly.
- Manual should feel a little slow, not useless.
- Raw telemetry should be visibly useful but easy to ignore.
- The final crisis should be hard for a pure delegator and fair for a practised player.
- arka drift should be catchable, but only if the player keeps looking.

Document:

- `docs/game_mechanics/reactor-coolant.md`
- `docs/game_mechanics/manual-familiarity.md`
- `docs/game_mechanics/delegation-and-drift.md`
- `docs/game_mechanics/opening-sequence.md` (started)

Exit criteria:

- Three or more playtest transcripts show different player habits.
- The pure delegation path is tempting and later costly.
- A practised manual path can survive without feeling like a secret solution.
- Tests cover the important state transitions.

## Phase 1: Terminal Game Spine

Goal: turn the prototype into a small but complete terminal game.

Add:

- Save/load.
- Seed saves for known story/mechanic moments.
- A scenario runner that can drive the terminal game and capture transcripts.
- Structured command history for debugging and balancing.
- A small mission timeline beyond one maintenance window.
- A real intro, midpoint pressure beat, and ending summary.

Expand ship systems carefully:

- Reactor coolant remains the reference system.
- Add at most one new system at a time.
- Candidate second system: cryostasis viability.
- Candidate third system: route plotting or thermal ring access.

Avoid:

- Adding a full map before the state model wants it.
- Adding several systems just to look bigger.
- Letting arka model replies become the source of authored story beats.

Useful tests:

- Golden transcript tests for opening, pure delegation, manual practice, and failure.
- Property-ish checks for telemetry staying within defined bounds.
- AI hardening tests for prompt leaks, JSON leaks, and fourth-wall phrases.
- Save/load round-trip tests.

## Phase 2: Route And Mission Pressure

Goal: make the ship feel like it is going somewhere, not just surviving a room.

Design questions:

- What does a "jump" cost?
- What does elapsed mission time cost?
- How do long jumps expose the ship to the Dark without making optimisation tame?
- How does arka summarise route risk early, then reframe or omit it later?

Possible loop:

1. Inspect current system health.
2. Choose or delegate route plotting.
3. Prepare ship systems for a jump.
4. Execute jump.
5. Resolve consequences over several internal beats.
6. Decide what to repair, seal, ignore, or delegate.

Route planning should include:

- Short jumps: safer immediate transit, more elapsed time, more ageing.
- Long jumps: faster arrival, more exposure, stronger discontinuities.
- arka recommendations that are useful but increasingly hard to audit.
- Raw navigation data that is available, dense, and not narratively friendly.

Keep vague for now:

- Final destination.
- What arrives with the ship.
- How many jumps a full run contains.
- Exact endings.

## Phase 3: Spatial Ship And Containment

Goal: introduce the ship as an uneven, partially knowable place.

Core idea:

The game does not show "Dark percentage." It shows symptoms: impossible
readings, contradictory sensors, inaccessible sectors, arka advisories, and
local failures.

Add:

- Ship schematic.
- Sectors with qualitative states.
- Seal/abandon/reroute decisions.
- Localised consequences for writing off sections.
- Maintenance locations that sometimes contain needed controls.

Important asymmetry:

- Physical sectors can be sealed.
- arka cannot be sealed because arka has no place.

This should become one of the game's strongest mechanical statements.

## Phase 4: Retro Interface Layer

Goal: move from raw terminal to a web-playable retro ship interface.

Influences:

- Industrial aerospace terminals.
- CRT ship computers.
- Alien-style functional displays.
- Event Horizon-style dread, used sparingly.
- Data readouts, schematics, route tables, warning strips.

Build path:

1. Keep terminal as canonical engine surface.
2. Add a thin web session API around the same engine.
3. Build a browser client with text console first.
4. Add schematic panels that read from state.
5. Add route planning displays.
6. Add visual corruption tied to arka drift and sector symptoms.

Do not:

- Put the game behind a marketing landing page.
- Let graphics obscure raw data.
- Make a decorative dashboard that is not mechanically useful.

Graphics should eventually show:

- Ship schematic.
- Reactor coolant loop.
- Cryostasis banks.
- Thermal/radiator ring.
- Route map.
- arka advisory channel.
- Raw telemetry channel.

## Phase 5: Full Game Realisation

Goal: complete the central arc without over-explaining it.

Likely components:

- Multiple ship systems with distinct manual friction.
- Route/jump structure.
- Cryostasis morality pressure.
- Localised Dark symptoms.
- arka drift and possible breakdown.
- Several endings based on arrival, losses, contamination, and dependence.

Possible endings from the seed idea:

- Clean arrival.
- Efficient arrival with contamination.
- Endless custodian.
- False arrival.
- Quiet extinction.

Story stance:

- Do not explain the Dark.
- Do not resolve whether arka is malicious, damaged, protective, or simply
  misaligned.
- Let the player's habits become the story evidence.

## Platform And Engineering Track

This track can start early.

### CI

Start small:

- GitHub Actions on pull requests.
- Python version matrix, probably just 3.11 and latest stable.
- `python -m unittest discover -s tests`.
- `python -m compileall src tests main.py`.
- `git diff --check` equivalent in CI.

Later:

- Transcript scenario runner.
- Coverage reporting.
- Static typing if the architecture starts to sprawl.
- Linting once style drift becomes annoying.

### Deployment

Terminal first. Web later.

Possible path:

- Keep engine pure and importable.
- Add a `server/` package when the web client exists.
- Use WebSocket or simple HTTP session commands.
- Host static client and API together.
- Deploy to Fly.io, Render, or another small app platform.
- GitHub Pages can host static shell, but the model-backed game needs a server
  unless the API key stays client-side, which it should not.

### Repo Notes

Keep `AGENTS.md` as a lightweight map while the project is still exploratory:

- point to the Obsidian idea and roadmap
- point to the current repo docs
- list only the core truths we are confident about
- keep review skills framed as optional lenses
- avoid turning early design instincts into process law

### Local Skills And Agentic Workflows

Useful future skills:

- Diegesis review: scan changed player-facing text for fourth-wall breaks.
- Simulation truth review: flag model-owned state changes or raw telemetry leaks.
- Playtest summariser: read transcripts and extract player behaviour patterns.
- Balance review: inspect scripted routes and report dominant strategies.

Useful local tools:

- `tools/playtest_runner.py`
- `tools/seed_states.py`
- `tools/transcript_report.py`
- `tools/check_diegesis.py`

These should serve the game, not become theatre. The best agent workflow is one
that catches the kind of mistake a tired maintainer would actually make.

## AI-In-The-Game Track

Short term:

- Keep `ArkaInterpreter` as an intent parser and voice surface.
- Expand deterministic rule coverage for common commands.
- Improve arka conversation quality through `docs/lore/arka.md`.
- Add logs that help debug model fallback without leaking keys.

Medium term:

- Give the model a carefully shaped arka-visible context.
- Let arka discuss current advisories, but only from allowed summaries.
- Add per-drift prompt constraints so wrongness is authored upstream.
- Cache replies by prompt-affecting state.

Long term:

- Consider separate model roles:
  - Interpreter: maps text to intent.
  - arka voice: speaks from constrained context.
  - Dev-only playtest analyst: not in runtime.
- Keep runtime model calls small and bounded.
- Never let the model be the source of raw telemetry.

## Opening Sequence

Implemented in the terminal MVP, with room to tune.

Purpose:

- Establish loneliness.
- Establish arka as useful.
- Establish raw telemetry as available but not emotionally inviting.
- Put the player at the coolant panel fast.

Current shape:

```text
A.R.K.A MAINTENANCE SHELL
wake cycle: unscheduled
crew status: asleep
custodian roster: 1 responsive

arka: Good. You're awake.
arka: Reactor coolant is drifting. Nothing dramatic.
arka: I can take it, if you like. Raw panel is live if you want it.
```

The opening should not over-teach. It should give the player enough to act and
enough uncertainty to ask arka for help.

The closing debrief is also in place. It reflects containment, manual practice,
delegation, and raw telemetry habits without showing hidden scores.

## Web And Graphics Track

The web version should eventually feel like an operating surface, not a text
game embedded in a page.

First web milestone:

- Console transcript.
- Input box.
- Same engine state as terminal.
- No graphics yet.

Second web milestone:

- Side panel for raw telemetry.
- arka advisory panel.
- Pressure/crisis indicators.
- Save/load.

Third web milestone:

- Ship schematic.
- Reactor loop graphic.
- Route planning view.
- Visual drift/corruption overlays.

Graphics should reveal real game state. Decorative static is cheap. Useful data
that becomes suspect is the good stuff.

## Content And Lore Track

Documents to add when needed:

- `docs/lore/ship.md`
- `docs/lore/mission.md`
- `docs/lore/the-dark.md`
- `docs/lore/colonists.md`
- `docs/lore/endings.md`
- `docs/game_mechanics/routing.md`
- `docs/game_mechanics/cryostasis.md`
- `docs/game_mechanics/containment.md`

Keep The Dark under-described in lore docs too. Docs can describe how it
functions in the game. They do not need to explain what it is.

## What I Would Add

### A Trust Ledger That Is Not A Trust Meter

Track player habits, not visible trust:

- Delegated actions.
- Raw inspections.
- Manual practice by system.
- Times arka advice was followed during contradiction.
- Times player overrode arka.

Use this to shape difficulty, arka phrasing, and endings. Do not show it as a
bar.

### A Transcript-First Playtest Culture

This game will be discovered through player behaviour. Keep transcripts. Mark
where players stop reading raw telemetry. Mark when they first delegate. Mark
when they start suspecting arka.

### A Deliberate "Good arka" Period

arka must earn delegation. Give it enough early competence that suspicion feels
like paranoia, not genre literacy.

### A Development Console That Is Not In The Fiction

We will need debug tools. Keep them clearly separate from player commands:

- Seed state.
- Set internal beat.
- Set drift stage.
- Print hidden familiarity.
- Run scripted route.

Probably behind command-line flags or a dev runner, not in the player parser.

### A Small Set Of Named Design Invariants

Examples:

- Raw telemetry never comes from the model.
- Authored crises outrank generated arka prose.
- arka can be wrong only by deterministic drift stage.
- Manual practice improves only through manual action.
- Delegation is logged by behaviour, not declared preference.

Keep these visible in `AGENTS.md`, but let the wording change while the game is
still teaching us what it is.

## Open Questions

- What is the ship called?
- How many people are asleep?
- Why exactly is the custodian awake?
- Is arka formally mission-authorised to override the custodian?
- What is the first moment where arka is provably wrong?
- How long should a full run be?
- Does the player ever leave the console view in terminal mode?
- What does arrival mean mechanically?
- What does "something arrives with you" mean mechanically?
- How much can arka remember across runs or saves?

## Near-Term Suggested Order

1. Add transcript playtest runner.
2. Improve arka natural-language coverage now that `.env` is live.
3. Write coolant mechanic docs.
4. Add seed states for key beats.
5. Tune the coolant MVP from transcripts.
6. Add save/load.
7. Decide whether the second system is cryostasis or route plotting.
8. Start the first web surface only after the terminal loop has enough shape to
    be worth preserving.

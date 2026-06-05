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

- Two systems: reactor coolant and cryostasis viability.
- Deterministic `ShipState` and coolant state transitions.
- Compact coolant and cryostasis HUDs that carry telemetry outside arka's voice.
- arka summary drift: accurate, interpretive, selective, wrong.
- Optional model-backed arka interpreter for natural-language input.
- Deterministic transcript playtest runner and seed routes.
- Diegetic opening screen and closing debrief.
- Hidden manual familiarity.
- A short scripted two-system maintenance arc.
- First coolant/cryostasis interactions: pressure events threaten sleepers, and
  emergency cryo chilling stresses coolant reserve.
- A legible objective block (goal, horizon, per-beat priority) and trend-aware
  HUD so the player always knows what they are trying to achieve.
- Delegation framed as a throughput choice: one manual control per beat versus a
  whole panel via arka, with drift weighted toward delegation and mitigated by
  raw-reading vigilance.
- Save/load of `ShipState` and structured command history records (Phase 1D).
- Mission clock, route options, first jump execution, and route-advice drift
  (Phase 2A-D).
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

Status: concluded. Phase 0 is now a playable, testable coolant slice.

Done:

- Opening screen and boot sequence.
- A short debrief or end screen that reflects delegation and manual practice.
- Interactive launch and event screen clears.
- Transcript playtest runner with seeded routes.
- Coolant, manual familiarity, and delegation/drift mechanic docs.
- Better first-run affordances without tutorialising the trap away.
- More natural-language synonyms for manual and delegation actions.
- Debug/status commands for development that are clearly non-player-facing.
- Ad-hoc command-file support for the playtest runner.

Tuned/Evidenced:

- Delegation should solve early problems cleanly.
- Manual should feel a little slow, not useless.
- Raw telemetry should be visibly useful but easy to ignore.
- The final crisis should be hard for a pure delegator and fair for a practised player.
- arka drift should be catchable, but only if the player keeps looking.

Documents:

- `docs/game_mechanics/reactor-coolant.md` (started)
- `docs/game_mechanics/manual-familiarity.md` (started)
- `docs/game_mechanics/delegation-and-drift.md` (started)
- `docs/game_mechanics/opening-sequence.md` (started)

Exit Evidence:

- `pure-delegation`: fails late with wrong drift, no raw inspections, no manual familiarity.
- `practised-manual`: survives cleanly with fluent hands and low delegation.
- `raw-curious`: survives with frequent raw inspections but cryostasis losses.
- `hesitant`: exposes a partial, uncertain route for affordance testing.
- Tests cover important state transitions and the playtest runner.

## Phase 1: Terminal Game Spine And System Variety

Goal: turn the prototype into a small but complete terminal game loop without
making the player twiddle one coolant panel for twenty-plus beats.

Phase 1 should keep the terminal surface, but improve rhythm:

- shorter maintenance windows, roughly 8-12 meaningful beats while building
- two ship systems, not one
- one light mission structure around them
- command history/transcripts for balancing
- save/load once the two-system loop has state worth preserving

### Phase 1A: Shorten Coolant

Status: implemented in the current terminal slice.

Goal: compress the existing coolant arc so it proves the same thesis faster.

Keep:

- early arka competence
- manual practice that matters
- raw telemetry as truth outside arka's voice
- wrongness that can be caught if the player keeps looking
- a final pressure moment where practised hands matter

Change:

- reduce the active coolant maintenance arc to about 10 internal beats
- remove filler beats that only repeat known information
- keep pure delegation tempting but costly
- keep practised manual control viable without making it a rote solution

Exit evidence:

- pure delegation still fails or pays a visible cost
- practised manual still survives
- raw-curious remains meaningfully different from both

### Phase 1B: Add Cryostasis Viability

Status: implemented in the current terminal slice.

Goal: add one more system that creates variety and moral pressure without
requiring a map.

Why cryostasis:

- it connects directly to sleeper losses
- it makes the ship feel populated
- it creates pressure beyond reactor numbers
- it can interact with coolant without needing route plotting yet

Current telemetry:

- cryo bank temperature
- neural stability
- sedative balance
- sleepers at risk
- pod fault load

Current actions:

- `stabilise bank`
- `reroute chill`
- `cycle pods`
- `triage`
- `delegate cryo`

Design constraint:

Cryostasis must not become a second coolant loop with renamed numbers. It should
feel like preserving fragile sleeping people, not tuning another machine.

### Phase 1C: System Interaction

Status: first pass implemented in the current terminal slice.

Goal: make the player divide attention.

Current examples:

- coolant pressure events can threaten cryo banks
- emergency cryo chilling can stress coolant reserve or reactor load
- arka can handle one system while the player works the other
- raw inspection becomes an attention choice across systems

This is where delegation becomes attractive for a better reason: there is too
much ship for one waking custodian.

### Phase 1C.5: Maintainer-Friendly Playtest Surface

Status: terminal-readout pass implemented, with a course correction.

Playtesting the two-system transcript surfaced a deeper problem than maintainer
fatigue: the *player* could not tell what they were trying to achieve. The course
correction addresses both at once.

Implemented:

- a legible objective block on every status readout: OBJECTIVE (goal), WATCH
  (horizon in beats), ATTENTION (the metric failing fastest this beat), and
  CREW LOAD (one manual control per beat vs a whole panel via arka)
- per-metric trend arrows on the HUD so the fastest-failing thing is scannable
- separated system blocks and threshold bars (already started)
- tab completion for multi-word controls (already started)
- interactive refresh of the current-state panel (already started)

Design constraint, resolved rather than dodged:

Trend arrows make raw telemetry more scannable, which on its own risks sanding
off the "delegating your eyes" friction. The resolution is that legibility of the
*goal* is high while capacity to *act manually* stays scarce: the player can see
the whole ship slipping and still be tempted to let arka take it all. Reading
stays useful; reading stops being sufficient. See
`docs/game_mechanics/objectives-and-priority.md`.

Drift was also reweighted toward delegation (with raw-reading vigilance as a
mitigation) so the cost of delegation is causal, not merely a timed cutscene. See
`docs/game_mechanics/delegation-and-drift.md`.

### Phase 1D: Save/Load And Command History

Status: implemented in the current terminal slice.

Add:

- save/load (`custodian.persistence`, `:save` / `:load`)
- structured command history records (`ShipState.history`) for debugging and balancing
- transcript reports that include both systems
- optional seed saves for known story/mechanic moments once those moments are stable

See `docs/architecture/save-load.md`. The engine stays pure: persistence only
serialises and deserialises `ShipState`, and history is recorded centrally in
`GameEngine.handle`.

### Phase 1E: Optional Third System Gate

Only add a third system if coolant plus cryostasis still feels too thin after
playtesting.

Candidate third systems:

- power distribution
- navigation preparation
- thermal/radiator ring

Avoid route plotting as the third Phase 1 system unless Phase 2 is being pulled
forward deliberately. Route plotting is likely the heart of Phase 2.

Expand ship systems carefully:

- Reactor coolant remains the reference system.
- Add at most one new system at a time.
- Second system: cryostasis viability.
- Optional third system: power distribution, navigation preparation, or thermal/radiator ring.

Avoid:

- Adding a full map before the state model wants it.
- Adding several systems just to look bigger.
- Letting arka model replies become the source of authored story beats.
- Letting cryostasis become coolant with softer nouns.

Useful tests:

- Golden transcript tests for pure delegation, practised manual, raw-curious, and mixed-system stress.
- Property-ish checks for telemetry staying within defined bounds.
- AI hardening tests for prompt leaks, JSON leaks, and fourth-wall phrases.
- Save/load round-trip tests.
- Cross-system interaction tests once cryostasis exists.

## Phase 2: Route And Mission Pressure

Goal: make the ship feel like it is going somewhere, not just surviving a room.

Status: nearing closeout. Phase 2A adds a passive deterministic mission clock to
the terminal slice: elapsed mission time, distance remaining, ship wear, and
long-duration cryostasis decay. Phase 2B adds route options and plotting. Phase
2C/D adds jump execution, route consequences, and drift-sensitive arka route
advice. Phase 2E should be the final balance and closeout pass before spatial
ship work.

Phase 2 should stay before the spatial ship phase. Routes create the strategic
loop; schematics and spatial containment should then reveal the consequences of
that loop rather than inventing one by themselves.

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

### Phase 2A: Mission Clock

Status: implemented in the current terminal slice.

Goal: give the existing maintenance watch a mission-scale pressure layer before
adding route choice.

Implemented:

- `MissionStatus` on `ShipState`.
- Elapsed mission days and distance remaining.
- Ship wear and cryostasis decay as deterministic pressure fields.
- A `MISSION CLOCK` status block and `raw mission` panel.
- Save/load support with migration for Phase 1D saves.
- Playtest summaries that report mission elapsed time, distance, wear, and decay.

Design stance:

The clock is intentionally passive and gentle for now. It makes time visible and
gives future route choices real state to push, but it should not become route
planning by stealth.

Exit evidence:

- Advancing commands move mission time and distance.
- High ship wear worsens coolant drift.
- High cryostasis decay worsens sleeper pressure.
- Mission telemetry remains raw deterministic state, outside arka's generated voice.

### Phase 2B: Route Options

Status: implemented in the current terminal slice.

Goal: let the player see and plot candidate routes before jumps exist.

Implemented:

- `NavigationState` on `ShipState`.
- Three deterministic route options: short, medium, and deep.
- A compact `NAVIGATION` status block.
- `raw nav` for dense route telemetry.
- `plot short`, `plot medium`, and `plot deep` for manual route plotting.
- `delegate nav` for arka route plotting, currently choosing the medium route.
- Save/load support with migration for Phase 2A saves.
- Playtest summaries that report plotted route and manual/delegated route plots.

Design stance:

Route options are facts, not consequences. Plotting a route costs attention and
records a choice, but it does not execute a jump, move the ship by the route
distance, apply Dark exposure, or apply route risk yet.

Exit evidence:

- Raw navigation data is visible outside arka's voice.
- Manual route plotting and delegated route plotting produce different habit
  records.
- arka can plot a useful route without owning navigation truth.
- At the Phase 2B boundary, jump execution remained unimplemented and explicit.

### Phase 2C/D: Jump Execution And Route Advice

Status: implemented in the current terminal slice.

Goal: make plotted routes materially affect the run, and let arka's route advice
begin to drift without giving the model ownership of navigation truth.

Implemented:

- `jump` / `execute jump` commits the currently plotted route.
- Jump execution clears the plotted route and records the last jump.
- Route distance, elapsed mission days, projected wear, cryostasis age, and Dark
  exposure are applied deterministically.
- Route instability and Dark exposure shock coolant and cryostasis state.
- `NavigationState` records jump count and total Dark exposure.
- Save/load support with migration for Phase 2B saves.
- Playtest summaries report last jump, jump count, and Dark exposure.
- arka's early navigation delegation selects the medium route and names the cost.
- under selective or wrong drift, arka delegates toward the deep route while
  omitting or contradicting the raw navigation risk.

Design stance:

Jumping is still one maintenance-watch action, not a new chapter of the game.
It should make route choice matter without becoming a full spatial or event
system. Raw navigation data remains the audit path; arka's advice is useful
early and less trustworthy under drift.

Exit evidence:

- A plotted route can be executed and has visible consequences.
- `raw nav` remains true before and after arka route advice.
- Jump consequences are deterministic engine state.
- arka can misframe route risk without inventing route facts.

### Phase 2E: Balance And Closeout

Status: next.

Goal: decide whether Phase 2's route loop is fun, legible, and dangerous enough
to support Phase 3.

Likely work:

- Tune short/medium/deep route costs.
- Add or adjust seeded playtest routes around manual plotting, delegated
  plotting, and jump execution.
- Decide whether post-jump pressure needs one more authored beat or whether the
  existing coolant/cryo drift is enough for now.
- Review arka route advice for usefulness, omission, and late contradiction.
- Close or rewrite Phase 2 docs before moving into spatial ship work.

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

Open UI hypothesis to test, not canon:

- System stats may want threshold bars, small dials, or banded indicators that
  show nominal ranges at a glance. The player should be able to see "too high",
  "too low", and "inside tolerance" without parsing every number under pressure.
  This should make raw truth quicker to scan without making arka obsolete, and
  it should be contested in mockups/playtests before becoming a rule.

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
arka: Reactor coolant is drifting. Cryostasis is colder than you are.
arka: I can take coolant or cryo, if you like. Raw panels and manual controls are live.
arka: Pumps, vent, flush, balance. Banks, chill, pods, triage. Unglamorous verbs, but they work.
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

1. Playtest the Phase 1A-C terminal slice and tune whether two systems create
   enough attention pressure.
2. Consider Phase 1C.5 if the maintainer surface is slowing playtest feedback.
3. Phase 1D: add save/load and structured command history records.
4. Decide whether Phase 1E needs a third system.
5. Start the first web surface only after the terminal loop has enough shape to
    be worth preserving.

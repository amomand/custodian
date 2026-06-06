# Custodian Roadmap

## North Star

Custodian is a sci-fi horror game about the pleasure and cost of delegation.

The player is the only waking custodian aboard a colony ship. Manual control is
real, useful, and effortful. `arka` is easier, faster, often better, and good
company. Over the run, the player who lets arka see and act for them becomes
dependent on a voice whose account of the ship is no longer cleanly aligned with
raw telemetry.

The finished game should make the player feel:

- I could do this myself.
- I do not want to.
- arka is right there.
- arka has always been right before.
- I have forgotten how to do this quickly.
- The raw numbers are still there.
- I am not sure I know how to read them under pressure.

The next major shape is not a bigger terminal prototype. It is an operating
surface game: a graphical ship console with panels, schematics, route displays,
raw telemetry, arka's advisory channel, incidents, and endings.

Do not build free-roaming exploration yet. The player's body is their attention.
The ship is too large, the systems are too many, and arka is too helpful.

## Current Snapshot

The terminal proof is now enough. It has done its job.

Already in the repo:

- A deterministic engine (`ShipState` + `GameEngine.handle()`) covering coolant
  and cryostasis manual control, the mission clock, routes and jumps, physical
  sectors and containment, crises, and cryostasis losses.
- arka's authored drift (accurate, interpretive, selective, wrong), delegation as
  throughput, hidden manual familiarity, and raw telemetry kept outside arka's
  voice.
- Save/load, structured command history, deterministic playtest routes, and
  optional model-backed interpretation with a no-API-key fallback.
- A browser layer on the same command path: per-session shell, a web-safe `ui`
  snapshot that hides internal counters, and an operating desk client that acts
  through generated buttons or text.
- Terminal opening, closing debrief, objectives, HUDs, and docs for the current
  mechanics.

The history matters less than the contract it proved: the game works when
manual control, delegation, raw telemetry, and arka drift all point at the same
idea.

## Design Contracts

These are the invariants to preserve while the shape changes.

- Manual control is real. It should never be a fake flavour button.
- Delegation is seductive. arka must be useful and sensible early.
- Trust is behaviour, not a visible stat.
- arka is the interface, not a menu skin or neutral narrator.
- The model interprets and speaks. The simulation decides.
- Raw telemetry comes from deterministic state, not generated prose.
- arka wrongness is authored and deterministic, not ordinary chatbot drift.
- Manual familiarity improves through manual action, not delegation or reading.
- The Dark is never explained and never exposed as a clean progress bar.
- Horror comes through continuity: arka stays competent and reassuring even when
  that reassurance no longer matches reality.
- Player-facing text stays in-world unless it is deliberately developer-only.

## Target Run Shape

The first full graphical vertical slice should support a complete 35 to 60
minute run.

Aim for:

- an opening wake sequence,
- 3 to 5 route decisions,
- 4 to 8 maintenance watches,
- 6 to 12 meaningful incidents,
- at least one irreversible containment decision,
- at least one arka/raw contradiction the player can catch,
- at least three reachable endings,
- a closing debrief that reflects behaviour.

The loop should be:

1. Review ship state through arka advisory and raw panels.
2. Pick or delegate a route.
3. Prepare ship systems for the jump.
4. Execute the jump.
5. Absorb wear, cryostasis decay, sector symptoms, and arka drift pressure.
6. Resolve a maintenance watch through manual action, delegation, scans, or
   containment.
7. Decide what to ignore.
8. Repeat until arrival, false arrival, abandonment, or collapse.

## Work Sections

These sections are intentionally larger than a single narrow code task. When a
section starts, decide whether it should be one PR or several PRs based on the
state of the repo and the amount of risk in that moment.

### Completed Foundation

Done enough for now:

- Production direction and engine contracts documented; terminal engine, playtest
  runner, and save/load remain usable.
- The browser layer — session shell, `ui` snapshot, and operating desk — runs the
  current slice on the same engine command path, with hidden state behind an
  explicit dev-only path.

Keep further browser work pointed at the schematic, route, and corruption passes
rather than general look and feel.

### 3. UI Snapshot Projection

Goal: give the web client renderable state without making it reconstruct
simulation truth.

Status: implemented enough for the first operating desk pass.

Work:

- Add a `UiSnapshot` projection layer or equivalent.
- Project mission, objective, systems, navigation, schematic, arka advisory, raw
  panels, available actions, transcript tail, and visual state.
- Generate action specs from engine state where practical.
- Hide hidden values such as trust, Dark exposure internals, and manual
  familiarity numbers from normal snapshots.
- Keep dev-only hidden values behind explicit developer paths.

Acceptance:

- The client can render from snapshots without reading internal dataclasses
  directly.
- Raw panel snapshot data is deterministic state, not arka prose.
- Hidden values do not leak into normal UI snapshots.
- Tests cover projection for normal, drifted, and finished states.

Likely split:

- Snapshot dataclasses and tests.
- Action spec projection.
- Dev-only snapshot/report hooks if needed.

### 4. Operating Desk UI

Goal: replace the browser status dump with the first real ship operating desk.

Status: implemented. The web client now renders the `ui` snapshot as a persistent
operating desk and dispatches manual, delegated, navigation, and containment
actions through the same command path as typed input. See
`docs/ui/operating-desk.md`. Graphical schematic/route rendering and drift-driven
visual corruption remain for the next section.

Work:

- Build a persistent layout with:
  - mission strip,
  - ship schematic region,
  - active system panel,
  - arka advisory panel,
  - incident/objective strip,
  - raw telemetry drawer,
  - action queue or history.
- Add focused panels for coolant, cryostasis, navigation, and containment.
- Add manual and delegated action buttons generated from action specs.
- Keep command input available for text and natural-language play.
- Add keyboard navigation for major actions.
- Make arka's panel the easiest thing to read without making raw panels ugly.

Acceptance:

- The player can perform manual and delegated actions without typing.
- The raw telemetry drawer shows true deterministic telemetry.
- The arka panel shows drift-aware advice and outcomes.
- The UI is mechanically useful, not decorative.
- Text fits and controls remain usable on normal desktop and mobile widths.

Likely split:

- Layout and mission/arka/raw panels.
- System panels and action buttons.
- Responsive/accessibility pass.

### 5. Schematic And Route Displays (Next)

Goal: make the ship and route pressure visible as game state, not flavour.

Work:

- Render a graphical ship schematic from `SpatialState`.
- Show qualitative sector symptoms: nominal, sensor noise, readings disagree,
  intermittent, no signal, sealed, written off.
- Add containment controls for seal, reroute, and abandon.
- Render current fix and route options as a route display.
- Support plot and jump controls where the engine already supports them.
- Tie visual corruption to deterministic state: arka drift, sector symptoms,
  signal confidence, sensor disagreement, manual access degradation, and high
  exposure.
- Provide reduced-motion and textual equivalents for corruption that affects
  readability.

Acceptance:

- Short, medium, and deep route runs look and feel different.
- Sectors can be sealed, rerouted, and abandoned from the UI.
- No Dark percentage is shown.
- arka cannot be spatially contained.
- Corruption never hides essential information without an accessible equivalent.

Likely split:

- Schematic rendering and containment actions.
- Route display and jump flow.
- Visual corruption and accessibility pass.

### 6. Behaviour Ledger And Standing Delegation

Goal: track how the player relies on arka without exposing a trust meter.

Work:

- Add a behaviour ledger that records:
  - delegated actions by system,
  - manual actions by system,
  - raw inspections by panel,
  - arka advice followed or overridden,
  - arka advice followed during contradictions,
  - irreversible choices made on arka's recommendation,
  - standing delegations,
  - first delegation and first raw inspection timing.
- Keep existing simple counters where they are still useful, or migrate them
  carefully into the ledger.
- Add one-shot delegation and standing delegation.
- Let standing delegation reduce cognitive load and improve early outcomes.
- Prevent standing delegation from making irreversible moral choices without
  player authorisation.

Acceptance:

- The ledger updates from both text commands and UI actions.
- The ledger is saved, loaded, and included in playtest reports.
- No visible trust meter appears.
- Delegation still does not increase manual familiarity.
- arka cannot make final jumps, sector abandonment, or equivalent irreversible
  decisions without player confirmation.

Likely split:

- Ledger state and persistence migration.
- UI/action integration.
- Standing delegation behaviour.

### 7. Story State, Manifest Anchors, And Incidents

Goal: turn the system loop into a run with rhythm, human stakes, and authored
pressure.

Work:

- Add `StoryState` for act, flags, active incident, resolved incidents, wake
  record state, manifest anchor states, and debrief hooks.
- Add 6 to 10 manifest anchors as data, not scattered prose.
- Add a deterministic incident scheduler.
- Start with three incidents:
  - first useful delegation,
  - manifest anchor wobble,
  - route recommendation drift.
- Expand to the stronger required set:
  - impossible sector symptoms,
  - control access in a compromised sector,
  - selective arka omission,
  - wrong calm summary,
  - arrival disagreement.
- Present incidents as operational pressure, not cutscenes.

Acceptance:

- Incidents trigger from state and behaviour, not random timing.
- Manifest anchors make sleeper risk more human without adding awake NPCs.
- arka and raw evidence can frame the same event differently.
- The player can inspect before acting unless an incident is explicitly urgent.
- Story flags and incident outcomes survive save/load.

Likely split:

- Story state and first three incidents.
- Manifest anchor data and UI exposure.
- Remaining incidents and balancing.

### 8. Arrival, Endings, And Debrief

Goal: make the run close because of how the player played.

Work:

- Add mechanical ending evaluation.
- Implement at least:
  - Clean Arrival,
  - Efficient Arrival With Contamination,
  - False Arrival.
- Add Endless Custodian and Quiet Extinction once state support is ready.
- Add arrival verification state.
- Let final decisions use route, sleeper, containment, arka drift, raw vigilance,
  manual readiness, and behaviour ledger data.
- Expand the debrief so it reflects delegation, manual practice, raw vigilance,
  containment, sleeper survival, route habits, manifest anchors, and arrival
  verification.

Acceptance:

- At least three endings are reachable through play.
- Endings follow from state, not a single final morality choice.
- No ending explains the Dark.
- No ending confirms whether arka was malicious, damaged, protective, or simply
  misaligned.
- The debrief describes habits in fiction rather than showing hidden scores.

Likely split:

- Ending evaluator and three endings.
- Debrief rewrite.
- Additional endings and tuning.

### 9. Playtest Instrumentation And Balance

Goal: tune Custodian from player behaviour rather than vibes alone.

Work:

- Preserve structured command history.
- Log UI actions into the same history shape.
- Add transcript export from the web client.
- Add run summary reports for endings, incidents, raw checks, delegation,
  manual actions, route choices, containment, sleeper losses, drift stage, and
  contradiction catches.
- Maintain golden routes:
  - pure delegator,
  - practised manual,
  - raw-curious,
  - deep-route fast arrival,
  - short-route cautious decay,
  - containment-heavy,
  - arka-override late.
- Keep debug tools outside the fiction.

Acceptance:

- Scripted routes can compare materially different habits and endings.
- Reports show when the player first delegated and first inspected raw.
- Reports show arka contradictions caught or missed.
- Browser playtests can export transcripts.
- Existing core tests and compile checks pass.

Likely split:

- Report shape and web export.
- Golden route additions.
- Balance/tuning passes.

## Content Rules

### arka

arka should be competent, calm, dry, useful, and hard to fluster. Early arka
should visibly earn trust. Late arka should not become a villain voice; the
horror is that the same warm competence keeps speaking when raw telemetry says
something else.

Good arka:

```text
arka: Coolant is misbehaving, not dying. I can balance the pumps while you look at cryo.
```

Bad arka:

```text
arka: Warning, player. Your trust in me has increased and the Dark corruption is rising.
```

### Raw Telemetry

Raw telemetry is terse, structured, source-labelled, and colder than arka. It can
be noisy or contradictory, but it should remain learnable.

Raw panels may show confidence, thresholds, source disagreement, and last-known
timestamps. They should not become unreadable static.

### Manifest Anchors

Manifest anchors are named sleeper records, not chatty NPCs. Use them sparingly
to make "sleepers at risk" become a future the player can imagine.

They should colour consequences without turning the game into cheap individual
trolley problems.

### The Dark

The Dark is not an enemy faction, monster, ghost, alien, god, virus, or lore
puzzle. It is an unknowable pressure expressed through effects.

The UI can show symptoms, signal conflict, impossible measurements, sealed
sectors, layout disagreement, and sensor noise. It should never show a clean
Dark meter or explanatory codex entry.

## Anti-Goals

Do not build these yet:

- first-person movement,
- procedural full-ship traversal,
- combat,
- monsters,
- a visible trust meter,
- a visible Dark meter,
- a generic chatbot sandbox,
- online multiplayer,
- accounts or authentication,
- a marketing site,
- cosmetic-only dashboard panels,
- huge inventory or crafting systems,
- colony surface gameplay,
- voice acting pipeline,
- dozens of ship systems.

Custodian gets worse if it tries to look bigger before the loop is fun.

## Documentation To Keep Current

When implementation reaches these areas, update or create:

- `docs/production/codex-direction-phase4.md`
- `docs/game_mechanics/trust-ledger.md`
- `docs/game_mechanics/incidents.md`
- `docs/game_mechanics/endings.md`
- `docs/game_mechanics/graphical-manual-control.md`
- `docs/ui/operating-desk.md`
- `docs/lore/ship.md`
- `docs/lore/manifest-anchors.md`
- `docs/lore/the-dark.md`
- `docs/architecture/web-session-api.md`
- `AGENTS.md` when the file map or invariants change.

For docs that also live in the Obsidian vault, sync the vault copy deliberately.

## First Implementation Prompt

When starting the next implementation session, use this narrower first task:

```text
Read docs/roadmap.md, docs/production/codex-direction-phase4.md, and the existing
architecture and UI docs.

Plan section 5, Schematic And Route Displays, only.

Do not redesign the operating desk, add story incidents, endings, or new lore.
Do not let the model or browser client own state.
Do not break terminal playtests, the browser session shell, or the operating desk.

Return:
1. a repo inventory of the relevant spatial, navigation, and snapshot files,
2. the smallest snapshot additions needed to render a graphical schematic and
   route display,
3. how qualitative sector symptoms and route bands project without leaking hidden
   values,
4. the containment and plot/jump actions to surface, reusing existing action specs,
5. the visual-corruption-to-state mapping and its accessible/reduced-motion
   equivalents,
6. tests to add, and risks where the current code shape may fight this plan.
```

After that, implement in small PR-sized chunks.

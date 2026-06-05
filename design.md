# Custodian MVP Design

## Thesis

Delegation is seductive because manual control is real but effortful. The player
can keep the reactor coolant loop alive by hand, but doing so costs attention,
and early mistakes. `arka` is quicker and better early on. Later, when
arka's account of the ship begins to drift, players who delegated too much have
fewer practised manual habits to fall back on.

This prototype is not the full game. It now proves the thesis with two terminal
systems, one short maintenance window, and enough cross-pressure to make
delegation attractive for attention, not just convenience.

## Scope

Included:

- Terminal command loop with deterministic state transitions.
- Pure state transitions around `ShipState`.
- One `ReactorCoolantSystem` with raw telemetry.
- One `CryostasisSystem` with raw telemetry and sleeper viability pressure.
- An `arka` layer that summarises the same deterministic systems.
- Compact coolant and cryostasis HUDs that carry current telemetry outside
  arka's voice.
- Optional arka interpreter for natural-language input and off-script replies.
- Diegetic opening screen and closing debrief.
- Manual actions and delegation as competing ways to spend attention.
- Hidden coolant and cryostasis familiarity gained only through manual actions.
- Summary drift from accurate to interpretive, selective, and wrong.
- Scripted time pressure events where practised manual control matters.
- Deterministic playtest scenarios and named seed states for tuning.

Still excluded:

- Map movement.
- Random generation.
- Rich UI.
- Deep lore.

## Player Loop

The player sees `arka` first because it is the path of least resistance.

Every status readout opens with a legible objective block so the player always
knows the goal and the most urgent thing this beat:

- **OBJECTIVE** — keep coolant and cryostasis nominal until the watch ends.
- **WATCH** — beats remaining until the maintenance window closes.
- **ATTENTION** — the metric degrading hardest toward danger right now.
- **CREW LOAD** — one manual control per beat, or a whole panel via arka.

This is the delegation thesis as a throughput decision: manual control answers
one control per beat, while arka takes a whole panel at once. Because several
metrics drift each beat (shown by trend arrows on the HUD), a hands-on player
falls behind on everything they did not touch, which is the honest reason
delegation is tempting.

Core commands:

- `status`: refresh the objective block, coolant and cryostasis HUDs, and arka summaries.
- `raw`: read detailed coolant telemetry.
- `raw cryo`: read detailed cryostasis telemetry.
- `delegate`: let arka adjust the whole coolant panel.
- `delegate cryo`: let arka tend the whole cryostasis panel.
- `pump up`: manual increase to coolant flow.
- `pump down`: manual pressure relief through lower flow.
- `vent`: manual pressure venting, costs coolant reserve.
- `flush`: manual impurity purge, costs coolant reserve.
- `balance`: manual valve balancing.
- `stabilise bank`: manual cryo neural stabilisation.
- `reroute chill`: cool cryo banks, stressing coolant reserve and reactor load.
- `cycle pods`: clear pod fault load.
- `triage`: prioritise sleepers at risk.
- `wait`: listen to the coolant loop.
- `help`: command list.
- `quit`: step away from the console.

Maintainer-facing colon commands sit outside the fiction: `:debug`, `:metrics`,
and the Phase 1D `:save` / `:load`.

Manual actions are intentionally a little awkward. Low familiarity still moves
the system, but with weaker effects and more side effects. Familiarity is never
shown as a number.

## State Model

`ShipState` owns the simulation:

- Internal maintenance beat.
- Reactor coolant telemetry.
- Hidden coolant and cryostasis familiarity.
- Number of delegated interventions, including cryostasis delegation.
- Raw inspection count.
- Active crisis, if any.
- Sleeper losses.
- Terminal outcome.
- Previous coolant and cryostasis snapshots, used to compute HUD trend arrows.
- Structured command history records, written centrally in `GameEngine.handle`.

`CryostasisSystem` owns telemetry:

- Bank temperature C.
- Neural stability percent.
- Sedative balance percent.
- Pod fault load.
- Sleepers at risk.

`ReactorCoolantSystem` owns telemetry:

- Temperature C.
- Pressure kPa.
- Flow L/s.
- Impurity percent.
- Valve skew percent.
- Coolant reserve percent.

The engine exposes one transition method:

```python
GameEngine.handle(state, command_text) -> StepResult
```

The CLI only prints messages and feeds input back into the engine. The arka
interpreter returns an `Intent`, but the engine remains the only authority that
can advance time, change telemetry, resolve crises, or record familiarity.

`custodian.telemetry` owns the terminal HUDs, their threshold bars, and per-metric
trend arrows. arka's summaries should not read out current numbers; the HUDs and
raw panels own telemetry display. `custodian.objectives` owns the legible
objective block (goal, horizon, per-beat priority) and reads only deterministic
telemetry.

Opening and closing text lives in `custodian.narrative`. The debrief can read
hidden state, but it must translate habits into fiction rather than showing
hidden numbers.

`custodian.playtest` runs deterministic command routes through the same engine
and reports habits. `custodian.seeds` provides named state factories for
targeted tests and future dev tooling. `custodian.persistence` serialises
`ShipState` for save/load without touching the engine.

## Arka Interpreter

The model-backed path is intentionally narrow. It can classify natural player
text into known actions and supply short arka replies for conversation or
off-script input. It cannot mutate state.

The supported intent actions are:

- `status`
- `raw`
- `delegate`
- `manual`
- `wait`
- `help`
- `quit`
- `converse`
- `none`

Obvious commands and typos are handled without calling the model. If
`OPENAI_API_KEY` is absent, the game keeps working in deterministic fallback
mode.

## Arka Drift

Drift is deterministic. Delegation is the primary driver: handing arka the panels
is what lets its account of the ship rot, regardless of how early it happens.
Time is a weak backstop so the finale still bites, and reading the raw layer
(vigilance) delays the time-based backstop, so a careful player keeps arka honest
longer. `wrong` drift overlaps the final crisis beat so the "calmly contradicting
the raw feed" moment actually lands.

Stages:

1. Accurate: arka reports the important numbers plainly.
2. Interpretive: arka still uses true numbers, but softens the framing.
3. Selective: arka mentions true numbers and omits the one that should worry you.
4. Wrong: arka reports stabilised values that no longer match the raw layer.

The raw layer remains available. The trap is not that truth disappears. The
trap is that truth is slower and colder than reassurance, and that a hands-on
player can only act on one slipping system per beat.

## Scripted Arc

Target length: 12 internal beats.

- Beat 3: filter fouling introduces impurity and skew.
- Beat 6: a cryostasis bank shiver raises pod faults and sleeper risk.
- Beat 8: pressure surge creates a short crisis that arka can still solve well,
  while cryostasis absorbs some thermal risk.
- Beat 10: thermal runaway creates a final crisis. It requires practised manual
  `balance` and `flush` actions to resolve reliably.

The player can survive by delegating early, but a player who delegates every
coolant decision reaches the final crisis with little manual familiarity, a bad
information channel, and unattended sleepers.

## Success And Failure

Success: survive past the maintenance window with the coolant loop contained.
Cryostasis losses can still mark the run.

Failure:

- Temperature, pressure, or coolant reserve crosses hard limits.
- Cryostasis neural stability collapses.
- The final thermal runaway crisis expires unresolved.
- The player quits.

Sleeper losses can happen before total failure. They are a pressure signal, not
the main score.

The terminal ending should stay in-world. Prototype labels belong in tests and
docs, not in the text shown to the player.

## Incremental Plan

1. Build the deterministic engine and terminal loop. Done.
2. Add focused tests for manual familiarity, delegation, drift, and crisis
   resolution. Done.
3. Add diegetic opening and habit-sensitive debrief. Done.
4. Add transcript playtest runner, seeded routes, and mechanic docs. Done.
5. Phase 1A-C terminal pass: shorter coolant, cryostasis, and first system
   interaction. Done.
6. Course correction: legible objective block (goal, horizon, per-beat priority),
   trend-aware HUD, delegation framed as a throughput choice, and drift weighted
   toward delegation with vigilance mitigation. Done.
7. Phase 1D: save/load of `ShipState` and structured command history records. Done.
8. Keep future expansion behind the same state-transition shape: more systems
   should plug in without moving parser or CLI responsibilities into the model.

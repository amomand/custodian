# Custodian MVP Design

## Thesis

Delegation is seductive because manual control is real but effortful. The player
can keep the reactor coolant loop alive by hand, but doing so costs attention,
and early mistakes. `arka` is quicker and better early on. Later, when
arka's account of the ship begins to drift, players who delegated too much have
fewer practised manual habits to fall back on.

This prototype is not the full game. It proves the thesis with one system, one
terminal loop, and one short maintenance arc.

## Scope

Included:

- Terminal command loop with deterministic state transitions.
- Pure state transitions around `ShipState`.
- One `ReactorCoolantSystem` with raw telemetry.
- An `arka` layer that summarises the same system.
- A compact coolant HUD that carries current telemetry outside arka's voice.
- Optional arka interpreter for natural-language input and off-script replies.
- Diegetic opening screen and closing debrief.
- Manual actions and delegation as competing ways to spend attention.
- Hidden manual familiarity gained only through manual coolant actions.
- Summary drift from accurate to interpretive, selective, and wrong.
- Scripted time pressure events where practised manual control matters.
- Deterministic playtest scenarios and named seed states for tuning.

Still excluded:

- Multiple systems.
- Map movement.
- Random generation.
- Rich UI.
- Deep lore.

## Player Loop

The player sees `arka` first because it is the path of least resistance.

Core commands:

- `status`: refresh coolant HUD and arka summary.
- `raw`: read detailed coolant telemetry.
- `delegate`: let arka adjust coolant.
- `pump up`: manual increase to coolant flow.
- `pump down`: manual pressure relief through lower flow.
- `vent`: manual pressure venting, costs coolant reserve.
- `flush`: manual impurity purge, costs coolant reserve.
- `balance`: manual valve balancing.
- `wait`: listen to the coolant loop.
- `help`: command list.
- `quit`: leave the prototype.

Manual actions are intentionally a little awkward. Low familiarity still moves
the system, but with weaker effects and more side effects. Familiarity is never
shown as a number.

## State Model

`ShipState` owns the simulation:

- Internal maintenance beat.
- Reactor coolant telemetry.
- Hidden manual familiarity.
- Number of delegated coolant interventions.
- Raw inspection count.
- Active crisis, if any.
- Sleeper losses.
- Terminal outcome.

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

`custodian.telemetry` owns the compact terminal HUD. arka's summaries should not
read out current numbers; the HUD and raw panel own telemetry display.

Opening and closing text lives in `custodian.narrative`. The debrief can read
hidden state, but it must translate habits into fiction rather than showing
hidden numbers.

`custodian.playtest` runs deterministic command routes through the same engine
and reports habits. `custodian.seeds` provides named state factories for
targeted tests and future dev tooling.

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

Drift is deterministic and based on time plus delegated controls. Delegation
accelerates how quickly the player lives inside arka's account of the ship.

Stages:

1. Accurate: arka reports the important numbers plainly.
2. Interpretive: arka still uses true numbers, but softens the framing.
3. Selective: arka mentions true numbers and omits the one that should worry you.
4. Wrong: arka reports stabilised values that no longer match the raw layer.

The raw layer remains available. The trap is not that truth disappears. The
trap is that truth is slower and colder than reassurance.

## Scripted Arc

Target length: 24 internal beats.

- Beat 5: filter fouling introduces impurity and skew.
- Beat 11: pressure surge creates a short crisis that arka can still solve well.
- Beat 16: silicate bloom makes impurity and valve skew the real problem.
- Beat 21: thermal runaway creates a final crisis. It requires practised manual
  `balance` and `flush` actions to resolve reliably.

The player can survive by delegating early, but a player who delegates every
coolant decision reaches the final crisis with little manual familiarity and a
bad information channel.

## Success And Failure

Success: survive past the maintenance window with the coolant loop contained.

Failure:

- Temperature, pressure, or coolant reserve crosses hard limits.
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
5. Play the arc by hand and tune numbers until delegation feels genuinely useful
   early.
6. Keep future expansion behind the same state-transition shape: more systems
   should plug in without moving parser or CLI responsibilities into the model.

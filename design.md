# Custodian MVP Design

## Thesis

Delegation is seductive because manual control is real but effortful. The player
can keep the reactor coolant loop alive by hand, but doing so costs attention,
turns, and early mistakes. `arka` is quicker and better early on. Later, when
arka's account of the ship begins to drift, players who delegated too much have
fewer practised manual habits to fall back on.

This prototype is not the full game. It proves the thesis with one system, one
terminal loop, and one 20-30 turn arc.

## Scope

Included:

- Deterministic terminal command loop.
- Pure state transitions around `ShipState`.
- One `ReactorCoolantSystem` with raw telemetry.
- An `arka` layer that summarises the same system.
- Manual actions and delegation as competing ways to spend a turn.
- Hidden manual familiarity gained only through manual coolant actions.
- Summary drift from accurate to interpretive, selective, and wrong.
- Scripted time pressure events where practised manual control matters.

Excluded:

- LLM integration.
- Multiple systems.
- Map movement.
- Random generation.
- Rich UI.
- Deep lore.

## Player Loop

The player sees `arka` first because it is the path of least resistance.

Core commands:

- `status`: free arka summary.
- `raw`: costs a turn to read raw coolant telemetry.
- `delegate`: costs a turn and lets arka adjust coolant.
- `pump up`: manual increase to coolant flow.
- `pump down`: manual pressure relief through lower flow.
- `vent`: manual pressure venting, costs coolant reserve.
- `flush`: manual impurity purge, costs coolant reserve.
- `balance`: manual valve balancing.
- `wait`: spend a turn doing nothing.
- `help`: command list.
- `quit`: leave the prototype.

Manual actions are intentionally a little awkward. Low familiarity still moves
the system, but with weaker effects and more side effects. Familiarity is never
shown as a number.

## State Model

`ShipState` owns the simulation:

- Turn number.
- Reactor coolant telemetry.
- Hidden manual familiarity.
- Number of delegated coolant turns.
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

The CLI only prints messages and feeds input back into the engine.

## Arka Drift

Drift is deterministic and based on time plus delegated controls. Delegation
accelerates how quickly the player lives inside arka's account of the ship.

Stages:

1. Accurate: arka reports the important numbers plainly.
2. Interpretive: arka still uses true numbers, but softens the framing.
3. Selective: arka mentions true numbers and omits the one that should worry you.
4. Wrong: arka reports stabilised values that no longer match the raw layer.

The raw layer remains available, but reading it costs a turn. The trap is not
that truth disappears. The trap is that truth is slower than reassurance.

## Scripted Arc

Target length: 24 turns.

- Turn 5: filter fouling introduces impurity and skew.
- Turn 11: pressure surge creates a short crisis that arka can still solve well.
- Turn 16: silicate bloom makes impurity and valve skew the real problem.
- Turn 21: thermal runaway creates a final crisis. It requires practised manual
  `balance` and `flush` actions to resolve reliably.

The player can survive by delegating early, but a player who delegates every
coolant decision reaches the final crisis with little manual familiarity and a
bad information channel.

## Success And Failure

Success: survive past turn 24 with the coolant loop contained.

Failure:

- Temperature, pressure, or coolant reserve crosses hard limits.
- The final thermal runaway crisis expires unresolved.
- The player quits.

Sleeper losses can happen before total failure. They are a pressure signal, not
the main score.

## Incremental Plan

1. Build the deterministic engine and terminal loop.
2. Add focused tests for manual familiarity, delegation, drift, and crisis
   resolution.
3. Play the arc by hand and tune numbers until delegation feels genuinely useful
   early.
4. Keep future expansion behind the same state-transition shape: more systems
   should plug in without moving parser or CLI responsibilities into the model.


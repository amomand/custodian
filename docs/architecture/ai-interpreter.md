# Arka Interpreter

## Purpose

The arka interpreter lets the player type natural language while keeping the
ship simulation deterministic. It borrows the shape that worked in The Cabin:

```text
player text -> Intent -> deterministic action -> authored state transition
```

The model is allowed to help understand and phrase player input. It is not
allowed to own the reactor.

## Pipeline

1. `GameEngine.handle()` receives raw player text.
2. `ArkaInterpreter.interpret()` returns an `Intent`.
3. Obvious commands use a deterministic rule path and do not call the model.
4. Ambiguous or conversational input can call the configured OpenAI model.
5. The engine executes only known `Intent.action` values.
6. Reactor telemetry, route plotting, internal clock advancement, crises,
   sleeper losses, arka drift, and manual familiarity remain owned by
   `ShipState` transitions.

## Intent Shape

```python
Intent(
    action="status|raw|delegate|plot|manual|wait|help|quit|converse|none",
    args={
        "operation": "pump_up|pump_down|vent|flush|balance",
        "target": "coolant|cryo|mission|nav",
        "route_id": "short|medium|deep|khepri-4|argos-12|carina-edge",
    },
    confidence=0.0,
    reply="optional arka line",
    rationale="debug note",
    correction="optional typo correction",
)
```

`manual` and `plot` require arguments. `raw` and `delegate` can carry a target.
The engine ignores model state-change suggestions because there are none.

## Authority Boundary

Deterministic and authored:

- Raw telemetry.
- Route options and plotted route state.
- arka summary drift stages.
- Coolant physics.
- Crisis timers and resolution.
- Manual familiarity.
- Sleeper losses and outcomes.
- Critical arka lies or omissions.

Model-assisted:

- Mapping free text to a known intent.
- Conversational arka replies for off-script input.
- Diegetic soft denials.
- Synonyms and phrasing.

This boundary is stricter than The Cabin because arka's wrongness is a game
mechanic. If the model invents wrong telemetry, the thesis collapses into
ordinary chatbot unreliability.

## Runtime Context

The model receives the arka-facing summary, not raw truth. If the player asks
for raw telemetry, the interpreter should return `action="raw"` and let the
engine print the raw panel.

Route handling follows the same rule. The model may classify a route command as
`raw`, `plot`, or `delegate`, but route options and plotted route state come from
the deterministic engine.

This preserves the central split:

- arka voice: convenient, drift-prone account of the ship.
- raw panel: slower, more literal telemetry.

## Offline Mode

If `OPENAI_API_KEY` is absent, the OpenAI SDK is not installed, or
`CUSTODIAN_AI=off`, the interpreter uses deterministic fallback rules. Tests and
playtest smoke runs should pass without network access or credentials.

## Model Choice

The Cabin defaulted to `gpt-5.4-mini` with `OPENAI_REASONING_EFFORT=none`.
Custodian uses the same default because this task needs low-latency structured
intent parsing and voice more than deep reasoning. `OPENAI_MODEL` can override
it in `.env`.

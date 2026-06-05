# Routing

## Purpose

Phase 2B gave the mission clock candidate routes. Phase 2C/D makes those
routes executable and gives arka's route advice the same drift problem as its
system summaries.

The slice stays narrow:

- inspect raw navigation data
- manually plot one route
- ask arka to plot a route
- execute the plotted route
- preserve plotted route, last jump, and Dark exposure in saves and playtest reports

## Route Options

`NavigationState` lives inside `ShipState` and owns deterministic route options.
The current table is deliberately small:

- `KHEPRI-4` — short jump, low exposure, more elapsed time
- `ARGOS-12` — medium jump, balanced recommendation
- `CARINA-EDGE` — deep jump, high exposure, low elapsed time

Each option carries:

- route id and label
- jump class
- distance
- elapsed days
- Dark exposure index
- instability percentage
- projected ship wear
- projected cryostasis ageing

These numbers are route facts. Plotting records a choice. `jump` commits the
choice and applies the consequences.

## Player Surface

The normal `status` readout includes a compact `NAVIGATION` block:

```text
NAVIGATION
PLOT      none          raw nav for candidate routes
JUMP      none          plot a route, then jump
OPTIONS   short, medium, deep routes available; plot or delegate nav
```

Detailed navigation data is available through:

```text
raw nav
```

Manual plotting:

```text
plot short
plot medium
plot deep
```

Delegated plotting:

```text
delegate nav
```

Manual and delegated plotting advance the watch because attention was spent.
They do not execute a jump by themselves.

Jump execution:

```text
jump
```

`jump` requires a plotted route. If no route is plotted, arka says so and the
watch does not advance. If a route is plotted, the engine:

- clears `plotted_route_id`
- records `last_jump_route_id`
- increments `jumps_executed`
- adds to `total_dark_exposure`
- closes the route distance
- spends the route elapsed mission days
- applies projected ship wear and cryostasis age
- shocks coolant and cryostasis according to route instability and Dark exposure

The normal per-beat mission clock and ambient system drift then run as usual.
This means a jump is not just a ledger update; the route can push the current
maintenance watch into worse coolant or sleeper conditions.

## arka Recommendation

Early, arka plots `ARGOS-12`, the medium route, and names the route cost plainly.
At interpretive drift it still chooses that compromise but softens the framing.
At selective or wrong drift it plots `CARINA-EDGE`, the deep route, and makes the
fast arrival sound cleaner than the raw table says.

This gives route delegation the same structure as coolant delegation:

- accurate early recommendation
- interpretive reframing of risk
- selective omission of important route cost
- late contradiction between arka route advice and raw nav data

## Boundaries

- Route options are deterministic state, not generated prose.
- The model may classify route commands, but the engine owns plotted route state.
- `raw nav` is raw telemetry and should remain available outside arka's voice.
- Jump execution and route consequence application are deterministic engine
  transitions.
- Post-jump balance and aftermath pacing remain Phase 2E work.

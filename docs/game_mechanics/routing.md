# Routing

## Purpose

Phase 2B gives the mission clock candidate routes without executing jumps yet.
The ship now has somewhere it might go next, but the consequences of actually
jumping remain Phase 2C.

This keeps the slice narrow:

- inspect raw navigation data
- manually plot one route
- ask arka to plot a route
- preserve the plotted route in saves and playtest reports

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

These numbers are not applied yet. They are route facts for plotting and future
jump execution.

## Player Surface

The normal `status` readout includes a compact `NAVIGATION` block:

```text
NAVIGATION
PLOT      none          raw nav for candidate routes
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
They do not execute a jump, apply route distance, apply Dark exposure, or resolve
route consequences.

## arka Recommendation

For now, arka plots `ARGOS-12`, the medium route. That gives delegation a useful
default without making Phase 2B responsible for route-risk drift.

Future Phase 2D work should decide how arka route advice changes under drift:

- accurate early recommendation
- interpretive reframing of risk
- selective omission of an important route cost
- late contradiction between arka route advice and raw nav data

## Boundaries

- Route options are deterministic state, not generated prose.
- The model may classify route commands, but the engine owns plotted route state.
- `raw nav` is raw telemetry and should remain available outside arka's voice.
- Jump execution, route consequence application, and post-jump pressure beats are
  not implemented in Phase 2B.

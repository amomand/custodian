# Routing

## Purpose

Phase 2B gave the mission clock candidate routes. Phase 2C/D makes those
routes executable and gives arka's route advice the same drift problem as its
system summaries. The current direction is a staged star chain: the ship must
pass through the listed fixes in order, and the player chooses how deep to cut
each leg.

The slice stays narrow:

- inspect raw navigation data
- manually plot the open leg at one depth
- ask arka to plot a route
- execute the plotted route
- preserve current fix, plotted route, last jump, and Dark exposure in saves and
  playtest reports

## Route Options

`NavigationState` lives inside `ShipState` and owns deterministic route options.
Each option is one stage of the route at one jump depth. The current map is
deliberately small and ordered:

- `WAKEFUL DRIFT -> KHEPRI-4` — cold beacon, stable reference
- `KHEPRI-4 -> ARGOS-12` — broken relay shadow, partial triangulation
- `ARGOS-12 -> CARINA-EDGE` — thin boundary, destination corridor

Each leg has shallow, medium, and deep solutions. Shallow solutions spend more
mission time and therefore push wear / cryostasis age harder. Deep solutions
arrive faster but carry higher Dark exposure, higher instability, and stronger
post-jump system shock. Medium solutions are the legible compromise.

Depth shortcuts apply to the currently open leg:

- `plot short` / `plot shallow` plots the open leg shallow
- `plot medium` plots the open leg medium
- `plot deep` plots the open leg deep

Each option carries:

- route id and label
- depth
- origin fix id
- arrival fix id
- stage index
- distance
- elapsed days
- Dark exposure index
- instability percentage
- projected ship wear
- projected cryostasis ageing
- star-map coordinates

These numbers are route facts. Plotting records a choice. `jump` commits the
choice and applies the consequences.

## Current Fix

`NavigationState` also carries a lightweight current fix, fixed star-map
coordinates, completed route ids, and the derived active stage. This is not a
generated maze yet. It answers the player's immediate questions after a jump:
where does the ship think it is now, which leg is open, and what path has
already been committed?

Current fixes:

- `WAKEFUL DRIFT` — starting fix, destination solution unresolved
- `KHEPRI-4` — cold beacon, long coast corridor
- `ARGOS-12` — broken relay shadow, partial triangulation
- `CARINA-EDGE` — thin Dark boundary, poor audit trail

Each jump sets the current fix to that route's arrival reference, independent of
the depth used to get there, and records the chosen route in
`completed_route_ids`. The normal HUD shows the fix label, the open leg, and the
available depths. The raw nav panel repeats the full staged graph as literal
telemetry.

This gives route planning a little fictional ground. The web star map draws the
current fix, future fixes, locked future legs, and taken depth variants from
deterministic route facts. Phase 3 turns the post-jump aftermath into
ship-sector symptoms, while generated maze traversal remains future work.

## Player Surface

The normal `status` readout includes a compact `NAVIGATION` block:

```text
NAVIGATION
FIX       WAKEFUL DRIFT destination solution unresolved
LEG       KHEPRI-4      next staged fix
PLOT      none          choose depth for open leg
JUMP      none          plot a route, then jump
OPTIONS   shallow, medium, deep; depth changes time and Dark exposure
```

Detailed navigation data is available through:

```text
raw nav
```

Explicit plotting works when the named star is the open leg:

```text
plot khepri-4 shallow
plot argos-12 medium
plot carina-edge deep
```

Legacy shortcuts:

```text
plot short
plot medium
plot deep
```

Delegated plotting:

```text
delegate nav
```

Plotting a future star fails without advancing the watch. Manual and delegated
plotting of the open leg advance the watch because attention was spent. They do
not execute a jump by themselves.

Jump execution:

```text
jump
```

`jump` requires a plotted solution for the open leg. If no route is plotted, or
if a loaded plot belongs to a different leg, arka says so and the watch does not
advance. If a route is plotted, the engine:

- clears `plotted_route_id`
- sets `current_fix_id` to the route's arrival fix
- records `last_jump_route_id`
- appends to `completed_route_ids`
- increments `jumps_executed`
- adds to `total_dark_exposure`
- closes the route distance
- spends the route elapsed mission days
- applies projected ship wear and cryostasis age
- shocks coolant and cryostasis according to route instability and Dark exposure

The normal per-beat mission clock and ambient system drift then run as usual.
This means a jump is not just a ledger update; the route can push the current
maintenance watch into worse coolant or sleeper conditions.

Natural `where are we?` style input maps to `status`, so the current fix is easy
to ask for without adding another visible command.

## arka Recommendation

Early, arka plots the open leg at medium depth and names the route cost plainly.
At interpretive drift it still chooses that compromise but softens the framing.
At selective or wrong drift it plots the open leg deep and makes the fast
arrival sound cleaner than the raw table says.

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
- Generated star-maze traversal remains future work. The current star map is a
  deterministic staged graph, not free movement.
- Full room traversal remains future work. The Phase 3 terminal schematic now
  owns local sectors and containment.

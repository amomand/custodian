# Spatial Containment

## Purpose

Phase 3 introduces the ship as a place without turning the terminal slice into a
room-navigation game.

The schematic does not show a Dark percentage. It shows reported symptoms:
sensor noise, readings that disagree, intermittent sectors, no signal, sealed
sections, and written-off sections. Those reports are deterministic state, but
they are still filtered through instruments and arka's account of them.

## State

`SpatialState` lives inside `ShipState` and owns physical sector state:

- bridge
- cryobay 1-3
- thermal ring
- maintenance D
- cargo spine
- hydroponics

Each sector carries:

- hidden symptom load
- containment state: open, sealed, or abandoned
- whether services have been rerouted
- profile metadata for labels, controls, and adjacency

The hidden load produces qualitative player-facing reports:

- `nominal`
- `sensor noise`
- `readings disagree`
- `intermittent`
- `no signal`
- `sealed`
- `written off`

The load is not displayed as a number. This preserves the original idea: the
ship detects impossible symptoms, not an objectively measurable Dark meter.

## Player Surface

The normal `status` readout includes a compact schematic:

```text
SHIP SCHEMATIC
CONTAIN   0 sealed, 0 written off  physical sectors only
BRIDGE         nominal            steady    primary
CRYOBAY 1-3    nominal            steady    primary
THERMAL RING   sensor noise       thin      primary
MAINTENANCE D  readings disagree  contested rerouted
```

Quick read:

```text
schematic
```

Detailed read:

```text
raw schematic
```

`raw schematic` advances the watch and increments raw inspections, like the
other raw panels. It shows reported state, signal confidence, containment,
routing, and the controls associated with each sector. It also states the
important asymmetry plainly: arka has no locus on the schematic.

## Containment Actions

Physical sectors can be contained:

```text
seal thermal
abandon cargo
reroute maintenance d
```

`seal` isolates a sector and reduces immediate symptom pressure, but the
section's controls become harder to use by hand unless services are rerouted.

`abandon` writes off a sector. It is stronger containment, but it can make
manual access unreachable and applies harsher local consequences.

`reroute` runs services around a sector. It is less final than sealing or
abandoning, but it costs ship wear and coolant reserve.

Attempts to seal or abandon the bridge are refused because the custodian is
using it. Attempts to seal arka are also refused, but for a different reason:
arka has no physical compartment.

## Consequences

Containment consequences are deterministic:

- cryobay containment costs sleepers and destabilises cryostasis
- thermal-ring containment worsens reactor heat rejection
- maintenance D containment degrades manual coolant access
- cargo-spine containment increases ship wear and weakens route redundancy
- hydroponics containment increases cryostasis decay pressure

Some manual controls are associated with physical sectors:

- coolant pump, flush, and balance route through maintenance D
- vent and reroute chill route through the thermal ring
- cryostasis stabilise, cycle pods, and triage route through cryobay 1-3

If the relevant sector is sealed, manual action works through secondary access
with reduced effective familiarity. If it is written off, the manual action is
not reachable and the watch still advances. Delegation remains tempting because
arka can try through distributed systems even when the custodian's hands cannot
reach a panel.

## Jump Interaction

Jump execution creates spatial symptoms:

- short routes mostly disturb the cargo spine
- medium routes mostly disturb hydroponics and route-support systems
- deep routes disturb maintenance D, the thermal ring, cargo spine, and cryo

After exposure, symptoms can spread along adjacency. Low exposure stays mostly
local; deep exposure can make the whole ship look wrong. This gives route choice
a spatial aftermath without introducing a full map.

## Boundaries

- The model may classify schematic and containment commands.
- The engine owns sectors, symptoms, containment consequences, manual access,
  and arka's authored wrongness.
- The player-facing schematic must not expose a Dark percentage.
- arka may summarise or misframe the schematic by drift stage, but it must not
  invent sector truth.
- arka cannot be spatially quarantined.

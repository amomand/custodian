# Mission Clock

## Purpose

Phase 2A makes the ship feel like it is travelling through a long mission, not
only surviving a local maintenance watch.

The clock began as passive mission pressure: every advancing command moves
mission time forward, closes a small amount of distance, and adds long-duration
pressure through ship wear and cryostasis decay. Phase 2B adds route options and
plotting. Phase 2C/D lets a plotted route execute and push those same mission
fields harder.

## State

`MissionStatus` lives inside `ShipState` and is deterministic engine state.

Current fields:

- `elapsed_days`
- `distance_remaining_tenths_ly`
- `ship_wear_pct`
- `cryo_decay_pct`

The distance is stored in tenths of a light year so the terminal can show useful
progress without introducing floating-point save data.

## Player Surface

Every status readout now includes a `MISSION CLOCK` block before coolant and
cryostasis. This is raw ship telemetry, not arka's voice.

The player can also use:

```text
raw mission
```

That raw read advances the watch, just like the coolant and cryostasis raw
panels. It counts as raw-layer vigilance because the player is choosing the
slower, colder information path instead of asking arka for reassurance.

## Current Pressure

The current 12-beat slice keeps mission pressure gentle so the Phase 1 coolant
and cryostasis playtest anchors remain readable.

- ship wear adds background coolant pressure when it gets high
- cryostasis decay adds background neural and sleeper-risk pressure when it gets high
- unstable coolant can increase ship wear
- unstable cryostasis can increase cryostasis decay

Jump execution now manipulates these fields directly. Phase 2E should tune how
harshly those jumps disturb the rest of the maintenance watch.

## Boundaries

- arka may interpret or comment on mission pressure from constrained context
- raw mission telemetry comes from `MissionStatus`, never generated prose
- route plotting, jump cost, and route-risk drift belong to Phase 2B-D
- post-jump balance and pacing belong to Phase 2E
- final destination and endings remain intentionally vague

# Reactor Coolant

## Purpose

Reactor coolant is the MVP's reference system. It proves the central thesis in
one place:

- manual control is real
- arka is easier
- raw telemetry is available
- familiarity matters later
- delegation changes the player's relationship with the system

Coolant is now short enough to share attention with cryostasis. It remains the
reference system for manual effort, arka drift, and final crisis pressure.

## Telemetry

`ReactorCoolantSystem` currently tracks:

- temperature C, nominal 560-620
- pressure kPa, nominal 210-270
- flow L/s, nominal 72-90
- impurity percent, nominal 0-18
- valve skew percent, nominal 0-16
- coolant reserve percent, caution below 35

The terminal HUD shows the current telemetry with `OK`, `LOW`, or `HIGH` bands
and threshold bars for maintainers/playtesters. arka's ordinary summary should
not recite the numbers. If the player asks for `raw`, the detailed panel prints
the literal field names and nominal bands.

## Manual Actions

Manual actions advance internal maintenance time and build hidden familiarity.

`pump up`

- raises flow
- lowers temperature
- raises pressure
- can increase valve skew when the custodian is clumsy

`pump down`

- lowers flow
- lowers pressure
- can let temperature rise

`vent`

- lowers pressure
- costs coolant reserve
- can slightly heat or skew the loop when done clumsily

`flush`

- lowers impurity
- costs coolant reserve
- can reduce flow while the custodian is still learning

`balance`

- lowers valve skew
- raises flow
- lowers temperature

## Ambient Drift

Every maintenance beat applies coolant drift:

- heat accumulates
- pressure responds to high flow and crisis state
- impurity and skew slowly worsen on schedule
- high impurity and skew make other problems harder to manage

This is deterministic. If a transcript changes, the code changed.

## Scheduled Pressure

Current authored beats:

- Beat 3: filter fouling adds impurity and valve skew.
- Beat 8: pressure surge starts a short crisis that arka can still solve while
  still accurate or interpretive. The surge also warms cryostasis.
- Beat 10: thermal runaway starts the final crisis and pressures cryostasis.

The player does not see beat numbers. They experience events, alarms, HUD
movement, arka framing, and their own competence or lack of it.

## Failure And Survival

Hard failures:

- temperature reaches 720 C
- pressure reaches 360 kPa
- coolant reserve reaches 0%
- thermal runaway expires unresolved

Survival means the reactor remains contained through the maintenance window.
Sleeper losses can happen before total failure, especially if the pressure surge
is handled badly.

## Playtest Routes

Use the runner to inspect behavior:

```bash
python3 tools/playtest_runner.py --all --summary-only
```

The current useful anchors are:

- `pure-delegation`: should be tempting, then costly.
- `practised-manual`: should split attention and survive without sleeper loss.
- `raw-curious`: should survive with frequent raw readings and a different cost profile.
- `mixed-system-stress`: should show arka covering one panel while the player
  works the other.
- `hesitant`: should expose whether the first-run affordances are too thin.

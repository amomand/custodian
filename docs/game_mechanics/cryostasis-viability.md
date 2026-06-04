# Cryostasis Viability

## Purpose

Cryostasis is the second terminal system. Its job is to make the ship feel
populated and to make attention morally expensive.

It should not feel like coolant with renamed numbers. Coolant is machinery.
Cryostasis is fragile sleeping people represented by cold telemetry.

## Telemetry

`CryostasisSystem` currently tracks:

- bank temperature C, nominal -196 to -170
- neural stability percent, caution below 78
- sedative balance percent, nominal 38-62
- pod fault load, nominal 0-12
- sleepers at risk, nominal 0

The compact cryostasis HUD shows the current telemetry outside arka's voice. The
raw cryo panel prints literal field names and nominal bands.

## Manual Actions

Manual cryostasis actions advance internal maintenance time and build hidden
cryo familiarity.

`stabilise bank`

- improves neural stability
- nudges sedative balance toward centre
- lowers sleepers at risk

`reroute chill`

- lowers cryo bank temperature
- lowers sleepers at risk
- spends coolant reserve and adds reactor heat/pressure
- can increase pod fault load when handled clumsily

`cycle pods`

- clears pod fault load
- can disturb neural stability or sedative balance when the custodian is clumsy

`triage`

- reduces sleepers at risk
- lowers fault load
- makes the player choose which alarms get answered first

## Delegation

`delegate cryo` asks arka to tend cryostasis. Early delegation is useful and can
reduce fault load, bank warming, or neural instability. Later delegation becomes
selective or wrong along with the rest of arka's drift.

Cryostasis delegation increments both the global delegation counter and
`delegated_cryo_controls`, so transcripts can show whether arka covered the cold
part of the ship.

## System Interaction

Cryostasis and coolant interact in three current ways:

- pressure surge and thermal runaway raise sleeper risk
- `reroute chill` helps cryostasis by spending coolant reserve and adding reactor
  load
- weak coolant state makes cryostasis ambient drift warmer and less stable

This is the first Phase 1C pressure: there is more ship than one custodian can
comfortably watch.

## Losses

Sleepers at risk are not themselves losses. If risk accumulates too high, the
engine emits a cryostasis loss report and reduces the immediate risk queue.

Losses are a pressure signal and a run texture. They are not currently the only
win/loss condition, though neural stability collapse can end the run.

## Playtest Signals

Use:

```bash
python3 tools/playtest_runner.py --all --summary-only
```

Current anchors:

- `pure-delegation`: coolant-only delegation leaves cryostasis unattended and
  causes heavy sleeper loss.
- `practised-manual`: split manual attention can preserve all sleepers.
- `raw-curious`: survives with raw attention and a different sleeper-loss
  profile.
- `mixed-system-stress`: arka covering cryostasis is useful but incomplete.

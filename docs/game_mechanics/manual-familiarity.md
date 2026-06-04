# Manual Familiarity

## Purpose

Manual familiarity is the cost of delegation made mechanical.

The player can always touch the coolant panel. Early manual work is clumsy but
real. Repeated manual work makes later crisis actions more effective. Delegating
does not build this familiarity.

The player should never see a familiarity number. They should feel it through
text, effectiveness, and whether a late manual crisis sequence is possible.

## How It Builds

Every manual coolant action increases `ShipState.manual_familiarity` by one, up
to the current cap of 8.

These actions count:

- `pump up`
- `pump down`
- `vent`
- `flush`
- `balance`

These actions do not count:

- `delegate`
- `raw`
- `status`
- `wait`
- conversation

## Current Labels

The playtest runner reports labels for maintainers:

- `unpractised`: no manual work
- `awkward`: early handling
- `practised`: useful competence
- `fluent`: the custodian can move before arka finishes speaking

These labels are for reports, not the HUD.

## Player-Facing Texture

Manual prose changes as familiarity rises:

- first touch: the player traces labels before touching anything
- early practice: hands find yesterday's path
- practised: the player moves before arka finishes the advisory
- fluent: hands know the coolant loop better than the voice does

This is important because it lets the player infer competence without seeing a
number.

## Crisis Use

Pressure surge:

- `delegate` can solve it while arka is still accurate or interpretive
- `vent` can solve it if the custodian has practised at least a little

Thermal runaway:

- `balance` requires meaningful manual practice
- `flush` requires stronger manual practice
- pure delegation should reach this moment without the hands for it

The exact thresholds can change, but the relationship should not: late manual
competence must be earned by earlier manual work.

## Playtest Signals

Useful routes:

- `pure-delegation`: manual familiarity should remain `unpractised`.
- `practised-manual`: should reach `fluent` and survive.
- `hesitant`: should show whether partial practice is enough or just tragic.

When tuning, watch whether manual actions feel like busywork. The thesis breaks
if manual practice is optimal rote grinding rather than a believable cost.

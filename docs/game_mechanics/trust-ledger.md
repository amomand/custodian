# Behaviour Ledger

## Purpose

Trust is behaviour, not a visible stat. The behaviour ledger is how Custodian
remembers the shape of a player's reliance on arka without ever printing a trust
meter.

It is the deterministic, saved record of *how* the player got through the watch:
what they delegated, what they did by hand, what raw panels they opened, which
systems they handed to arka's standing watch, and when they first leaned on arka
versus when they first read the raw layer. It feeds reports, debriefs, and later
difficulty. It never becomes "trust: 71%".

The ledger lives on `ShipState.behaviour` as `BehaviourLedger`
(`src/custodian/models.py`). Like the rest of ship truth it is owned by the
engine and serialised by persistence; arka never writes it.

## What It Records

- `delegated_by_system` — one-shot and standing delegations, counted per system
  (`coolant`, `cryostasis`, `navigation`).
- `manual_by_system` — manual control actions, counted per system.
- `raw_by_panel` — raw inspections, counted per panel (`coolant`, `cryostasis`,
  `navigation`, `schematic`, `mission`).
- `standing_delegations` — which systems are currently under arka's standing
  watch.
- `standing_adjustments` — how many automatic between-watch adjustments arka has
  made under standing delegation.
- `first_delegation_beat` / `first_raw_inspection_beat` — when the player first
  delegated and first read raw. The gap between them is a habit signal.

Fields for the §7 story layer (advice followed or overridden, advice followed
during a contradiction, contradictions caught, irreversible choices made on
arka's recommendation, and focus/zen-mode dwell) are not in the ledger yet. They
arrive with the incident system that gives "a recommendation" and "a
contradiction" a deterministic meaning, and with focus mode.

## One Path, One Ledger

The ledger is updated from the single canonical command path
(`GameEngine.handle`). Because the operating desk dispatches its action-spec
command strings through that same path as typed input, a button press and a
typed command land in the same ledger. There is no separate UI accounting.

Only time-advancing actions are recorded: a status read, a closed-window no-op,
or an unrecognised line is not practice or reliance. Manual familiarity still
comes from manual action only; delegation, standing or one-shot, never builds it.

## Visibility

- The ledger **counts** stay out of normal UI snapshots. They are exposed only on
  the explicit, loopback-only dev snapshot (`ui.dev.behaviour_ledger`) and in
  playtest reports and debriefs (developer/fiction surfaces, not a meter).
- **Standing-watch posture is shown.** Which systems arka currently holds appears
  in the snapshot (`systems[id].standing`, `navigation.standing`) and on the
  desk, because the player chose it. Showing a posture the player set is not a
  trust meter; hiding the reliance counts is what keeps it honest.

## Debrief And Reports

The closing debrief translates the ledger into fiction ("you handed coolant to
arka and mostly stopped watching what it did with them"), never numbers. The
playtest report prints the raw counts because it is a developer tool outside the
fiction. See `docs/architecture/web-session-api.md` for the snapshot contract and
`delegation-and-drift.md` for how standing delegation drives drift.

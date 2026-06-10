# Incidents

## Purpose

Incidents are the story layer's beats. They turn drift, containment, and
cryostasis pressure into named moments the player can answer or ignore.

An incident is never a random event. Every trigger reads deterministic ship
state and the behaviour ledger, so a scripted route always produces the same
incidents in the same order. The engine owns this truth; the model client and
the browser client only render what the engine already resolved.

Incidents ride `StoryState` on `ShipState` and survive save/load. They do not
change the numeric simulation. They project meaning onto the systems the player
is already working: an incident records how the player responded, updates the
behaviour ledger's incident-aware fields, and may move a manifest anchor or pull
the player out of focus mode.

## Lifecycle

1. **Selection.** When no incident is active, the scheduler looks at the current
   act and picks the highest-priority incident whose act window contains the
   current act, whose trigger is satisfied, and which has not already resolved.
2. **Presentation.** The incident announces itself, arka offers advice coloured
   by its current drift stage, and the raw evidence line states what the panel
   actually shows. arka's advice degrades with drift; the raw line does not.
3. **Resolution.** Each following beat, the active incident inspects the
   just-applied command. A matching response resolves the incident and records
   debrief flags, outcome tags, and ledger effects.
4. **Expiry.** Incidents with an urgency window count down each unanswered beat.
   When the window closes, the incident either resolves with a "missed" outcome
   or, for the manifest-anchor wobble, loses the anchor.

Urgent incidents (a short urgency window) break focus mode when they land, so a
contradiction stays catchable, and the ledger records that the calm did not
hold.

## Acts

Acts come from progress, never from a clock alone:

- Act 0 — wake
- Act 1 — competence
- Act 2 — drift
- Act 3 — containment
- Act 4 — contradiction
- Act 5 — arrival

The act is recomputed every beat from distance remaining, drift stage, and
containment state.

## The first eight incidents

| Incident | Trigger summary | Player answer that resolves it |
| --- | --- | --- |
| First useful delegation | Both coolant and cryostasis outside nominal | Delegate one panel, or hold both by hand |
| Manifest anchor wobble | A cryo bank holding a named cluster slips | Hold the bank by hand or hand it to arka before it expires |
| Route recommendation drift | A jump under interpretive-or-worse drift | Take arka's deep line or plot a steadier route by hand |
| Sector with impossible symptoms | A sector reporting against itself | Scan/raw the schematic, or act without looking |
| The control is in the bad place | Needed manual access sits inside a spreading sector | Seal the sector or keep the dangerous access open |
| A summary that leaves something out | Selective drift hiding a failing metric | Open the raw panel to catch the omission |
| A calm the panel disagrees with | Wrong drift over a system in danger | Intervene by hand against the calm, or trust it |
| Arrival disagreement | At the fix under drift, charts disagree | Verify the fix by hand, or accept arka's protocol |

## Behaviour ledger effects

Incidents feed the deferred behaviour-ledger fields that the debrief and the
endings later read:

- advice followed / advice overridden
- advice followed during a contradiction
- contradictions caught
- irreversible choices made on arka's advice
- focus held during a contradiction
- urgent-incident focus ejects

These counters never gate the simulation. They only shape the debrief and the
mechanical ending evaluation.

## Tuning questions

- Does each incident read as the same arka continuing, not a scripted villain?
- Is the raw evidence line always enough to catch a drifting summary?
- Do urgent incidents interrupt focus at the right moments, or too often?
- Does the priority order surface the most pressing incident first?

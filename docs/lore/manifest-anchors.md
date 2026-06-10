# Manifest Anchors

## Purpose

The cryostasis system makes attention morally expensive by representing sleeping
people as cold telemetry. Manifest anchors are the few sleepers the player can
actually name.

An anchor turns an abstract "sleepers at risk" number into a person with a role,
a pod bank, a manifest note, and a small personal fragment. When a bank holding
an anchor wobbles, the loss is no longer statistical. The point is not to make
every sleeper a character — it is to make the player feel the difference between
a number going down and a name going out.

## Data, not script

Anchors are static data carried in `models.default_manifest_anchors()`. Each
anchor records:

- `id` and `name`
- `role` — what the colony needed them for
- `pod_bank` — the cryo bank they sleep in
- `manifest_note` — the dry, official line
- `personal_fragment` — the human detail the manifest does not capture
- `loss_tag` and `arrival_tag` — debrief hooks the ending reads later

Anchor status rides `StoryState.manifest_anchor_states` and survives save/load.
Status is one of: stable, wobbling, saved, or lost.

## How anchors move

Anchors change state only through the manifest-anchor-wobble incident:

- A cryo bank carrying an anchor slips below tolerance and the anchor begins
  **wobbling**.
- If the player steadies the bank by hand or hands it to arka in time, the
  anchor is **saved** and the debrief records `manifest_anchor_saved`.
- If the player leaves the wobble unanswered until its window closes, the anchor
  is **lost** and the debrief records `manifest_anchor_lost`.

Saving or losing an anchor never changes the numeric simulation. It changes what
the arrival debrief is able to say.

## The eight anchors

- **Mara Vey** (anchor_01) — soil microbiologist; bank CRYO-B2. Recorded three
  wake-day messages for a daughter in another bank.
- **Idris Calwell** (anchor_02) — structural lattice engineer; bank CRYO-B2.
  Left a folded paper model of a house in his locker.
- **Suni Okafor** (anchor_03) — paediatric physician; bank CRYO-A1. Asked to be
  woken last so she could greet the children rested.
- **Tomas Reuel** (anchor_04) — water systems technician; bank CRYO-A1. Trained
  on the same coolant trunks the custodian now walks.
- **Beatriz Lind** (anchor_05) — seed archivist; bank CRYO-C3. Catalogued the
  vault by smell as much as by code.
- **Joon-ho Park** (anchor_06) — reactor second; bank CRYO-C3. Listed as the
  custodian's eventual relief on the watch.
- **Asha Mwangi** (anchor_07) — colony teacher; bank CRYO-D4. Packed nothing but
  books and a single warm coat.
- **Elias Vorne** (anchor_08) — cartographer; bank CRYO-D4. Believed the
  destination was real enough to draw it from memory.

## Tone

Fragments should be specific and quiet. They are not eulogies and they are not
plot. arka mentions anchors the way it mentions everything else — as
mission-relevant continuity — and the gap between that flatness and what the
fragment implies is where the weight sits. No anchor's fragment explains the
Dark, and no anchor's fate resolves whether arka is malicious, damaged, or
simply misaligned.

# Endings

## Purpose

Endings follow from state, never from a final morality menu. The engine decides
the ending condition mechanically; the debrief later translates behaviour into
fiction. No ending explains the Dark, and no ending resolves whether arka was
malicious, damaged, protective, or simply misaligned.

The evaluator lives in `endings.evaluate_ending(state)`. It reads the finished
ship state — distance, viability, Dark exposure, unresolved symptoms, drift
stage, arrival verification, and a few story flags — and returns one ending
candidate. The candidate is stored on `StoryState.ending_candidate` so the
debrief, the UI, and the tests share one vocabulary.

## Arrival

A run arrives when the remaining distance reaches the arrival threshold
(`ARRIVAL_DISTANCE_TENTHS`, currently 0 tenths of a light-year). Arrival is a
terminal condition checked in the engine's outcome logic, alongside the existing
failure conditions.

Before the final approach, the arrival-disagreement incident gives the player a
chance to **verify** the fix by hand or **accept** arka's protocol. That choice
feeds the verification state the ending evaluator reads.

## The five ending candidates

The evaluator checks conditions in a deliberate order, because some endings are
darker twins of others.

1. **False arrival.** Arrived, but under selective-or-worse drift, the fix was
   never verified by hand, and the player leaned entirely on arka's routing (more
   delegated plots than manual, no raw nav inspection). Also reached directly if
   the arrival-disagreement incident set the `false_arrival_path` flag. The star
   charts disagree and nothing confirms where the ship is.
2. **Efficient arrival with contamination.** Arrived fast and intact, but the
   ship carries unresolved symptoms (an open sector at or above the symptom
   threshold) and heavy Dark exposure. The colony arrives ahead of decay,
   carrying something it did not contain.
3. **Quiet extinction.** Viability collapsed — neural stability at or below the
   floor, or sleeper losses at or above the ceiling. If the ship arrived, it
   arrived as an ark with no colony to wake; if it did not, the watch failed its
   people either way.
4. **Clean arrival.** Arrived with viable sleepers (neural stability at or above
   the clean threshold) and contained symptoms, with arka kept aligned or the fix
   verified by hand. The hardest target: it demands both a maintained ship and a
   maintained crew.
5. **Endless custodian.** Did not arrive, but the ship remains maintainable and
   the sleepers viable. The watch does not close. It only continues.

## Thresholds

The thresholds are deliberately explicit so a scripted route can reach each
ending deterministically and so balancing has a single place to move them:

- `VIABILITY_FLOOR` — neural stability at or below this is sleeper collapse.
- `CLEAN_VIABILITY` — neural stability required for a clean arrival.
- `HIGH_DARK_EXPOSURE` — Dark exposure that, with unresolved symptoms, reads as
  contamination.
- `ARRIVAL_DISTANCE_TENTHS` — distance at which the ship has arrived.

## Debrief

`endings.ending_lines(state)` renders a diegetic arrival-protocol debrief for the
resolved candidate, and the narrative debrief appends it after the route,
containment, vigilance, and manifest-anchor lines. The debrief never narrates
the player's morality; it states what the protocol accepted and lets arka offer
one last, characteristically flat reassurance.

## Coverage

- `tests/test_endings.py` exercises every branch of the evaluator with
  constructed states.
- The `arrival-verified` and `arrival-accepted` playtest scenarios drive the
  arrival path end to end; `arrival-accepted` lands on false arrival.
- The existing non-arrival scenarios cover the endless-custodian and
  quiet-extinction fallbacks.

## Tuning questions

- Is clean arrival reachable by a careful player without being trivial?
- Does false arrival feel earned by reliance, not punished by a single misstep?
- Does each ending read as a consequence of play, never as a verdict?

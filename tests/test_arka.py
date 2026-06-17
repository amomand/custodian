import unittest
from dataclasses import replace

from custodian.arka import crisis_line, drift_stage, summarize_coolant
from custodian.models import CrisisState, DriftStage, ReactorCoolantSystem, ShipState

class ArkaTests(unittest.TestCase):
    def test_delegation_accelerates_drift(self) -> None:
        state = ShipState(turn=4, delegated_controls=6)

        self.assertEqual(drift_stage(state), DriftStage.SELECTIVE)

    def test_selective_summary_omits_raw_numbers(self) -> None:
        state = ShipState(
            turn=9,
            reactor=ReactorCoolantSystem(
                temperature_c=606,
                pressure_kpa=244,
                flow_lps=80,
                impurity_pct=41,
                valve_skew_pct=7,
                coolant_reserve_pct=78,
            ),
        )

        summary = summarize_coolant(state)

        self.assertIn("headline coolant values", summary)
        self.assertNotIn("606 C", summary)
        self.assertNotIn("41", summary)
        self.assertNotIn("impurity", summary)

    def test_wrong_summary_does_not_speak_raw_temperature(self) -> None:
        state = ShipState(
            turn=11,
            reactor=replace(ReactorCoolantSystem(), temperature_c=666),
        )

        summary = summarize_coolant(state)

        self.assertNotIn("666 C", summary)
        self.assertIn("coolant loop stable", summary)

    def test_wrong_drift_overlaps_the_final_crisis_beat(self) -> None:
        # The final crisis fires on beat 10; arka should already be wrong there
        # so the "calmly contradicting the raw feed" beat actually lands.
        self.assertEqual(drift_stage(ShipState(turn=10)), DriftStage.WRONG)

    def test_raw_reading_vigilance_delays_time_based_drift(self) -> None:
        blind = ShipState(turn=9)
        vigilant = ShipState(turn=9, raw_inspections=6)

        self.assertEqual(drift_stage(blind), DriftStage.SELECTIVE)
        self.assertEqual(drift_stage(vigilant), DriftStage.INTERPRETIVE)

    def test_delegation_drives_drift_independently_of_vigilance(self) -> None:
        # Heavy delegation rots arka's account even for a player who keeps reading raw.
        state = ShipState(turn=3, delegated_controls=7, raw_inspections=8)

        self.assertEqual(drift_stage(state), DriftStage.WRONG)

    def test_wrong_drift_crisis_line_does_not_contradict_its_own_calm(self) -> None:
        # In the same beat, WRONG arka calls the loop stable and tells the player
        # not to act. The crisis line must not flip to an alarm right below that;
        # the contradiction the design wants is arka against the raw feed, not
        # arka against its own previous sentence.
        crisis = CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=3,
            required_progress=2,
        )
        state = ShipState(turn=11, crisis=crisis)

        self.assertEqual(drift_stage(state), DriftStage.WRONG)
        line = crisis_line(state)
        self.assertIsNotNone(line)
        self.assertNotIn("active advisory", line)
        self.assertNotIn("response window", line)
        self.assertTrue(line.startswith("arka:"))

    def test_honest_drift_still_raises_the_crisis_advisory(self) -> None:
        # Before WRONG, arka still flags an active crisis plainly so the alarm
        # is genuinely available to a player who trusts the voice.
        crisis = CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=3,
            required_progress=2,
        )
        state = ShipState(turn=6, crisis=crisis)

        self.assertEqual(drift_stage(state), DriftStage.INTERPRETIVE)
        self.assertIn("active advisory", crisis_line(state))


if __name__ == "__main__":
    unittest.main()

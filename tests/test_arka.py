import unittest
from dataclasses import replace

from custodian.arka import drift_stage, summarize_coolant
from custodian.models import DriftStage, ReactorCoolantSystem, ShipState

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

    def test_vigilant_player_holds_arka_short_of_wrong_at_the_finale(self) -> None:
        # The design promises that reading raw "keeps arka honest longer." At the
        # closing beats a blind watch is WRONG, but a player who actually kept
        # reading the raw panels has held arka back to SELECTIVE -- the drift is
        # traceable to behaviour, not just to the watch lasting long enough.
        blind = ShipState(turn=13)
        vigilant = ShipState(turn=13, raw_inspections=4)

        self.assertEqual(drift_stage(blind), DriftStage.WRONG)
        self.assertEqual(drift_stage(vigilant), DriftStage.SELECTIVE)

    def test_vigilance_is_a_weak_backstop_not_an_off_switch(self) -> None:
        # Even relentless raw reading only buys four honest beats, so time still
        # erodes arka to SELECTIVE by the finale -- never back to ACCURATE.
        relentless = ShipState(turn=13, raw_inspections=20)

        self.assertEqual(drift_stage(relentless), DriftStage.SELECTIVE)


if __name__ == "__main__":
    unittest.main()

import unittest
from dataclasses import replace

from custodian.arka import drift_stage, summarize_coolant
from custodian.models import DriftStage, ReactorCoolantSystem, ShipState


class ArkaTests(unittest.TestCase):
    def test_delegation_accelerates_drift(self) -> None:
        state = ShipState(turn=4, delegated_controls=6)

        self.assertEqual(drift_stage(state), DriftStage.SELECTIVE)

    def test_selective_summary_omits_important_true_problem(self) -> None:
        state = ShipState(
            turn=16,
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

        self.assertIn("606 C", summary)
        self.assertNotIn("41", summary)
        self.assertNotIn("impurity", summary)

    def test_wrong_summary_disagrees_with_raw_temperature(self) -> None:
        state = ShipState(
            turn=21,
            reactor=replace(ReactorCoolantSystem(), temperature_c=666),
        )

        summary = summarize_coolant(state)

        self.assertNotIn("666 C", summary)
        self.assertIn("coolant loop stable", summary)


if __name__ == "__main__":
    unittest.main()


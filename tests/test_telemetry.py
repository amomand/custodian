import unittest

from custodian.models import CryostasisSystem, ReactorCoolantSystem, ShipState
from custodian.telemetry import coolant_hud_lines, cryostasis_hud_lines


class TelemetryTests(unittest.TestCase):
    def test_coolant_hud_carries_raw_readings_outside_arka_voice(self) -> None:
        state = ShipState(
            reactor=ReactorCoolantSystem(
                temperature_c=641,
                pressure_kpa=244,
                flow_lps=68,
                impurity_pct=9,
                valve_skew_pct=21,
                coolant_reserve_pct=88,
            )
        )

        hud = "\n".join(coolant_hud_lines(state))

        self.assertIn("COOLANT LOOP", hud)
        self.assertIn("641 C", hud)
        self.assertIn("HIGH", hud)
        self.assertIn("68 L/s", hud)
        self.assertIn("LOW", hud)
        self.assertIn("[", hud)
        self.assertIn("nominal 560-620", hud)
        self.assertNotIn("arka:", hud)

    def test_cryo_hud_carries_sleepers_without_arka_voice(self) -> None:
        state = ShipState(
            cryostasis=CryostasisSystem(
                bank_temperature_c=-164,
                neural_stability_pct=71,
                sedative_balance_pct=66,
                pod_fault_load=17,
                sleepers_at_risk=23,
            )
        )

        hud = "\n".join(cryostasis_hud_lines(state))

        self.assertIn("CRYOSTASIS", hud)
        self.assertIn("-164 C", hud)
        self.assertIn("71%", hud)
        self.assertIn("23 sleepers", hud)
        self.assertIn("HIGH", hud)
        self.assertIn("[", hud)
        self.assertIn("nominal -196 to -170", hud)
        self.assertNotIn("arka:", hud)


if __name__ == "__main__":
    unittest.main()

import unittest

from custodian.models import ReactorCoolantSystem, ShipState
from custodian.telemetry import coolant_hud_lines


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
        self.assertNotIn("arka:", hud)


if __name__ == "__main__":
    unittest.main()

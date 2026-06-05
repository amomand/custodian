import unittest

from custodian.models import (
    CryostasisSystem,
    MissionStatus,
    NavigationState,
    ReactorCoolantSystem,
    ShipState,
)
from custodian.telemetry import (
    coolant_hud_lines,
    cryostasis_hud_lines,
    mission_hud_lines,
    navigation_hud_lines,
)


class TelemetryTests(unittest.TestCase):
    def test_mission_hud_carries_clock_without_arka_voice(self) -> None:
        state = ShipState(
            mission=MissionStatus(
                elapsed_days=15_000,
                distance_remaining_tenths_ly=97,
                ship_wear_pct=36,
                cryo_decay_pct=25,
            )
        )

        hud = "\n".join(mission_hud_lines(state))

        self.assertIn("MISSION CLOCK", hud)
        self.assertIn("41y 35d", hud)
        self.assertIn("9.7 ly", hud)
        self.assertIn("WEAR", hud)
        self.assertIn("CRYO AGE", hud)
        self.assertIn("HIGH", hud)
        self.assertNotIn("arka:", hud)

    def test_mission_hud_adds_breathing_room_after_range(self) -> None:
        lines = mission_hud_lines(ShipState())

        range_index = lines.index(
            "RANGE     11.8 ly       destination solution unresolved"
        )

        self.assertEqual(lines[range_index + 1], "")
        self.assertTrue(lines[range_index + 2].startswith("WEAR"))

    def test_navigation_hud_shows_plot_without_arka_voice(self) -> None:
        state = ShipState(
            navigation=NavigationState(
                plotted_route_id="argos-12",
                last_jump_route_id="khepri-4",
                jumps_executed=1,
                total_dark_exposure=4,
            )
        )

        hud = "\n".join(navigation_hud_lines(state))

        self.assertIn("NAVIGATION", hud)
        self.assertIn("WAKEFUL DRIFT", hud)
        self.assertIn("ARGOS-12", hud)
        self.assertIn("medium solution held", hud)
        self.assertIn("last KHEPRI-4, dark 4", hud)
        self.assertIn("short, medium, deep", hud)
        self.assertNotIn("arka:", hud)

    def test_navigation_hud_has_breathing_room_around_block(self) -> None:
        lines = navigation_hud_lines(ShipState())

        self.assertEqual(lines[0], "")
        self.assertEqual(lines[-1], "")
        self.assertEqual(lines[1], "NAVIGATION")

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

    def test_coolant_hud_marks_worsening_trend_against_previous(self) -> None:
        state = ShipState(
            reactor=ReactorCoolantSystem(temperature_c=600),
            previous_reactor=ReactorCoolantSystem(temperature_c=580),
        )

        temp_line = next(
            line for line in coolant_hud_lines(state) if line.startswith("TEMP")
        )

        self.assertIn("^!", temp_line)


if __name__ == "__main__":
    unittest.main()

import json
import unittest

from custodian.models import (
    CryostasisSystem,
    NavigationState,
    ReactorCoolantSystem,
    ShipSector,
    ShipState,
    SpatialState,
)
from custodian.ui_snapshot import project_ui_snapshot


class UiSnapshotTests(unittest.TestCase):
    def test_normal_snapshot_projects_renderable_panels_without_hidden_values(self) -> None:
        state = ShipState(
            navigation=NavigationState(
                plotted_route_id="argos-12",
                last_jump_route_id="khepri-4",
                jumps_executed=1,
                total_dark_exposure=4,
            )
        )

        snapshot = project_ui_snapshot(
            state,
            transcript_tail=(
                "RAW NAVIGATION SOLUTIONS",
                "dark_exposure_total  4",
                "KHEPRI-4            short     1.8 ly   126 d    4      6%    +3    +3",
                "NAVIGATION jump applied: 1.8 ly closed, 126 mission days spent, Dark exposure 4.",
            ),
        ).to_dict()
        encoded = json.dumps(snapshot)

        self.assertIn("mission", snapshot)
        self.assertIn("systems", snapshot)
        self.assertIn("navigation", snapshot)
        self.assertIn("schematic", snapshot)
        self.assertIn("arka", snapshot)
        self.assertIn("raw_panels", snapshot)
        self.assertIn("actions", snapshot)
        self.assertEqual(snapshot["navigation"]["exposure_band"], "low")
        self.assertEqual(
            snapshot["navigation"]["route_options"][1]["exposure_band"],
            "moderate",
        )
        self.assertIn("exposure_band        low", encoded)
        self.assertIn("exposure band low", encoded)
        self.assertNotIn("dark_exposure", encoded)
        self.assertNotIn("total_dark_exposure", encoded)
        self.assertNotIn("manual_familiarity", encoded)
        self.assertNotIn("cryo_familiarity", encoded)
        self.assertNotIn("drift_stage", encoded)
        self.assertNotIn("symptom_load", encoded)
        self.assertIsNone(snapshot["dev"])

    def test_raw_panels_use_deterministic_state_not_arka_prose(self) -> None:
        state = ShipState(
            turn=10,
            reactor=ReactorCoolantSystem(temperature_c=666, impurity_pct=41),
            cryostasis=CryostasisSystem(neural_stability_pct=49, sleepers_at_risk=37),
            delegated_controls=7,
        )

        snapshot = project_ui_snapshot(state).to_dict()
        coolant_raw = "\n".join(snapshot["raw_panels"]["coolant"]["lines"])
        cryo_raw = "\n".join(snapshot["raw_panels"]["cryostasis"]["lines"])
        advisory = "\n".join(snapshot["arka"]["advisory_lines"])

        self.assertIn("temperature_c", coolant_raw)
        self.assertIn("666", coolant_raw)
        self.assertIn("neural_stability_pct", cryo_raw)
        self.assertIn("49", cryo_raw)
        self.assertIn("coolant loop stable", advisory)
        self.assertIn("cryostasis banks stable", advisory)
        self.assertNotIn("arka:", coolant_raw)
        self.assertNotIn("arka:", cryo_raw)

    def test_action_specs_cover_manual_delegated_navigation_and_containment(self) -> None:
        state = ShipState()

        actions = project_ui_snapshot(state).to_dict()["actions"]
        by_id = {action["id"]: action for action in actions}

        self.assertEqual(by_id["delegate-coolant"]["command"], "delegate coolant")
        self.assertEqual(by_id["manual-balance"]["command"], "balance")
        self.assertEqual(by_id["plot-argos-12"]["command"], "plot medium")
        self.assertFalse(by_id["execute-jump"]["enabled"])
        self.assertEqual(by_id["execute-jump"]["reason"], "no route plotted")
        self.assertFalse(by_id["seal-bridge"]["enabled"])
        self.assertTrue(by_id["seal-cryo-1-3"]["requires_confirmation"])
        self.assertTrue(by_id["abandon-cryo-1-3"]["requires_confirmation"])

    def test_finished_snapshot_marks_outcome_and_removes_actions(self) -> None:
        state = ShipState(outcome="The reactor survives the maintenance window.")

        snapshot = project_ui_snapshot(state).to_dict()

        self.assertTrue(snapshot["mission"]["is_finished"])
        self.assertEqual(snapshot["mission"]["watch_label"], "maintenance window closed")
        self.assertEqual(snapshot["mission"]["outcome"], state.outcome)
        self.assertEqual(snapshot["actions"], ())

    def test_visual_state_projects_drift_and_schematic_qualitatively(self) -> None:
        state = ShipState(
            turn=10,
            delegated_controls=7,
            spatial=SpatialState(
                sectors=(
                    ShipSector("bridge"),
                    ShipSector("cryo-1-3", symptom_load=30),
                    ShipSector("thermal-ring", containment="sealed"),
                    ShipSector("maintenance-d", symptom_load=65),
                    ShipSector("cargo-spine"),
                    ShipSector("hydroponics"),
                )
            ),
        )

        snapshot = project_ui_snapshot(state).to_dict()
        visual = snapshot["visual_state"]
        schematic = snapshot["schematic"]

        self.assertEqual(visual["arka_panel_intensity"], "contradictory-calm")
        self.assertEqual(visual["schematic_noise_by_sector"]["cryo-1-3"], "disagreeing")
        self.assertEqual(visual["schematic_noise_by_sector"]["thermal-ring"], "isolated")
        self.assertEqual(visual["schematic_noise_by_sector"]["maintenance-d"], "broken")
        self.assertEqual(schematic["sectors"][1]["reported_state"], "readings disagree")
        self.assertNotIn("symptom_load", json.dumps(snapshot))

    def test_dev_snapshot_is_explicit_and_contains_hidden_values(self) -> None:
        state = ShipState(
            turn=10,
            manual_familiarity=3,
            cryo_familiarity=2,
            delegated_controls=7,
            raw_inspections=4,
            navigation=NavigationState(total_dark_exposure=21),
        )

        normal = project_ui_snapshot(state).to_dict()
        dev = project_ui_snapshot(state, include_dev=True).to_dict()

        self.assertIsNone(normal["dev"])
        self.assertEqual(dev["dev"]["drift_stage"], "wrong")
        self.assertEqual(dev["dev"]["manual_familiarity"], 3)
        self.assertEqual(dev["dev"]["cryo_familiarity"], 2)
        self.assertEqual(dev["dev"]["total_dark_exposure"], 21)


if __name__ == "__main__":
    unittest.main()

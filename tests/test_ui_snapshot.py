import json
import unittest

from custodian.arka_interpreter import ArkaInterpreter
from custodian.config import Config
from custodian.models import (
    BehaviourLedger,
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

    def test_standing_delegation_specs_toggle_between_assign_and_release(self) -> None:
        # Each system offers exactly one of assign / release, depending on whether
        # arka currently holds its standing watch. The system panel reads the
        # posture from `standing`.
        fresh = project_ui_snapshot(ShipState()).to_dict()
        by_id = {action["id"]: action for action in fresh["actions"]}
        self.assertEqual(by_id["assign-coolant"]["command"], "assign coolant")
        self.assertEqual(by_id["assign-navigation"]["command"], "assign navigation")
        self.assertNotIn("release-coolant", by_id)
        self.assertFalse(fresh["systems"]["coolant"]["standing"])
        self.assertFalse(fresh["navigation"]["standing"])

        held = project_ui_snapshot(
            ShipState(behaviour=BehaviourLedger(standing_delegations=("coolant", "navigation")))
        ).to_dict()
        held_by_id = {action["id"]: action for action in held["actions"]}
        self.assertEqual(held_by_id["release-coolant"]["command"], "release coolant")
        self.assertEqual(held_by_id["release-navigation"]["command"], "release navigation")
        self.assertNotIn("assign-coolant", held_by_id)
        self.assertTrue(held["systems"]["coolant"]["standing"])
        self.assertTrue(held["navigation"]["standing"])
        self.assertFalse(held["systems"]["cryostasis"]["standing"])

    def test_behaviour_ledger_counts_never_leak_into_normal_snapshot(self) -> None:
        # The ledger is reliance behaviour, not a trust meter. Standing posture is
        # shown (the player chose it), but the counts stay dev-only.
        state = ShipState(
            behaviour=BehaviourLedger(
                delegated_by_system={"coolant": 5},
                raw_by_panel={"coolant": 2},
                standing_delegations=("coolant",),
                standing_adjustments=4,
                first_delegation_beat=1,
            )
        )

        normal = project_ui_snapshot(state).to_dict()
        encoded = json.dumps(normal)
        self.assertNotIn("behaviour_ledger", encoded)
        self.assertNotIn("delegated_by_system", encoded)
        self.assertNotIn("standing_adjustments", encoded)
        self.assertNotIn("first_delegation_beat", encoded)

        dev = project_ui_snapshot(state, include_dev=True).to_dict()
        ledger = dev["dev"]["behaviour_ledger"]
        self.assertEqual(ledger["delegated_by_system"], {"coolant": 5})
        self.assertEqual(ledger["standing_delegations"], ["coolant"])
        self.assertEqual(ledger["standing_adjustments"], 4)

    def test_action_specs_resolve_under_deterministic_interpreter(self) -> None:
        # Every desk button dispatches its action-spec `command` through the same
        # engine path as text. Those strings must resolve to the intended intent
        # under the no-AI interpreter, which is the default playtest/test mode.
        interpreter = ArkaInterpreter(Config(custodian_ai=False))
        expected = {
            "watch": {"wait"},
            "raw": {"raw"},
            "delegate": {"delegate"},
            "standing": {"assign", "release"},
            "manual": {"manual"},
            "navigation": {"plot", "jump"},
            "containment": {"seal", "reroute", "abandon"},
        }

        for state in (
            ShipState(),
            ShipState(navigation=NavigationState(plotted_route_id="argos-12")),
            # A standing delegation flips assign specs to release specs, so this
            # state exercises the "release coolant" command path too.
            ShipState(behaviour=BehaviourLedger(standing_delegations=("coolant",))),
        ):
            for action in project_ui_snapshot(state).to_dict()["actions"]:
                with self.subTest(action=action["id"]):
                    intent = interpreter.interpret(action["command"], state)
                    self.assertIn(
                        intent.action,
                        expected[action["kind"]],
                        f"{action['command']!r} resolved to {intent.action!r}",
                    )

    def test_snapshot_exposes_operating_desk_panel_contract(self) -> None:
        # Lock the shape the operating desk client renders against so future
        # projection changes cannot silently break panels.
        snapshot = project_ui_snapshot(ShipState()).to_dict()

        for system in snapshot["systems"].values():
            self.assertTrue(system["arka_summary"].startswith("arka:"))
            self.assertTrue(system["metrics"])
            self.assertIn(system["status"], {"nominal", "attention"})

        self.assertEqual(
            set(snapshot["raw_panels"]),
            {"mission", "coolant", "cryostasis", "navigation", "schematic"},
        )
        self.assertTrue(snapshot["navigation"]["route_options"])
        self.assertTrue(snapshot["schematic"]["sectors"])
        self.assertIn("no compartment", snapshot["schematic"]["arka_locus"])

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

    # ---- Section 5: schematic and route displays ----

    def test_schematic_sectors_expose_symmetric_adjacency_and_no_arka_locus(self) -> None:
        # The graphical schematic draws connecting edges from reported adjacency,
        # deduping each undirected pair. That only works if adjacency is
        # symmetric. arka must never appear as a sector — it has no compartment.
        schematic = project_ui_snapshot(ShipState()).to_dict()["schematic"]
        sectors = schematic["sectors"]
        adjacency = {sector["id"]: set(sector["adjacent"]) for sector in sectors}

        self.assertNotIn("arka", adjacency)
        for sector_id, neighbours in adjacency.items():
            for neighbour in neighbours:
                self.assertIn(neighbour, adjacency, f"{sector_id} -> unknown {neighbour}")
                self.assertIn(
                    sector_id,
                    adjacency[neighbour],
                    f"adjacency not symmetric: {sector_id} <-> {neighbour}",
                )
        self.assertIn("no compartment", schematic["arka_locus"])

    def test_no_containment_action_can_target_arka(self) -> None:
        # arka cannot be spatially contained. The desk only ever offers seal /
        # reroute / abandon for physical sectors, never for arka.
        actions = project_ui_snapshot(ShipState()).to_dict()["actions"]
        containment = [a for a in actions if a["kind"] == "containment"]

        self.assertTrue(containment, "expected physical containment actions")
        for action in containment:
            self.assertNotEqual(action["target"], "arka")
            self.assertNotIn("arka", action["command"])

    def test_route_options_project_distinct_qualitative_bands(self) -> None:
        # Short, medium, and deep routes must read differently: the route display
        # leads with ascending exposure / instability bands, not a flat table.
        nav = project_ui_snapshot(ShipState()).to_dict()["navigation"]
        options = nav["route_options"]

        self.assertEqual([o["jump_class"] for o in options], ["short", "medium", "deep"])
        self.assertEqual(
            [o["exposure_band"] for o in options], ["low", "moderate", "high"]
        )
        instabilities = [o["instability_pct"] for o in options]
        self.assertEqual(instabilities, sorted(instabilities))
        self.assertLess(instabilities[0], instabilities[-1])
        self.assertTrue(nav["current_fix_label"])

    def test_corruption_keeps_a_textual_equivalent_for_every_sector(self) -> None:
        # Visual corruption is allowed to degrade a sector's appearance, but never
        # to hide it: each sector keeps a non-empty reported state and signal
        # confidence (the accessible equivalent), including blanked-out ones.
        state = ShipState(
            spatial=SpatialState(
                sectors=(
                    ShipSector("bridge"),
                    ShipSector("cryo-1-3", symptom_load=50),
                    ShipSector("thermal-ring", containment="sealed"),
                    ShipSector("maintenance-d", symptom_load=70),
                    ShipSector("cargo-spine", containment="abandoned"),
                    ShipSector("hydroponics"),
                )
            ),
        )

        snapshot = project_ui_snapshot(state).to_dict()
        noise = snapshot["visual_state"]["schematic_noise_by_sector"]
        self.assertEqual(noise["cargo-spine"], "blank")
        self.assertEqual(noise["maintenance-d"], "broken")
        for sector in snapshot["schematic"]["sectors"]:
            self.assertTrue(sector["reported_state"], f"{sector['id']} lost its state")
            self.assertTrue(sector["signal_confidence"], f"{sector['id']} lost confidence")

    def test_drift_atmosphere_never_leaks_into_player_text(self) -> None:
        # arka_panel_intensity and label_instability drive CSS atmosphere only.
        # If their values surfaced as player-facing text they would leak the
        # hidden drift stage, so they must appear nowhere outside visual_state.
        for state in (
            ShipState(turn=10, delegated_controls=7),  # wrong: contradictory-calm
            ShipState(turn=9, delegated_controls=5),  # selective: filtered
        ):
            snapshot = project_ui_snapshot(state).to_dict()
            visual = snapshot["visual_state"]
            rest = {k: v for k, v in snapshot.items() if k not in {"visual_state", "dev"}}
            encoded = json.dumps(rest)
            with self.subTest(intensity=visual["arka_panel_intensity"]):
                self.assertNotIn(visual["arka_panel_intensity"], encoded)
                self.assertNotIn(visual["label_instability"], encoded)


if __name__ == "__main__":
    unittest.main()

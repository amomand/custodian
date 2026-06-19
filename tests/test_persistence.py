import json
import unittest

from custodian.models import (
    BehaviourLedger,
    CommandRecord,
    CrisisState,
    CryostasisSystem,
    MissionStatus,
    NavigationState,
    ReactorCoolantSystem,
    ShipState,
    ShipSector,
    SpatialState,
)
from custodian.persistence import dumps, loads, load_state, save_state


class PersistenceTests(unittest.TestCase):
    def _rich_state(self) -> ShipState:
        return ShipState(
            turn=8,
            reactor=ReactorCoolantSystem(temperature_c=611, pressure_kpa=288),
            cryostasis=CryostasisSystem(neural_stability_pct=80, sleepers_at_risk=14),
            mission=MissionStatus(
                elapsed_days=15_000,
                distance_remaining_tenths_ly=97,
                ship_wear_pct=31,
                cryo_decay_pct=19,
            ),
            navigation=NavigationState(plotted_route_id="argos-12", manual_plots=1),
            spatial=SpatialState(
                sectors=(
                    ShipSector("bridge"),
                    ShipSector("cryo-1-3", symptom_load=12),
                    ShipSector("thermal-ring", containment="sealed"),
                    ShipSector("maintenance-d", rerouted=True),
                    ShipSector("cargo-spine"),
                    ShipSector("hydroponics"),
                ),
                containment_actions=1,
                reroute_actions=1,
            ),
            manual_familiarity=4,
            cryo_familiarity=2,
            delegated_controls=3,
            delegated_cryo_controls=1,
            raw_inspections=5,
            sleepers_lost=42,
            crisis=CrisisState(
                kind="pressure_surge",
                label="Pressure surge",
                turns_left=2,
                required_progress=1,
                progress=0,
            ),
            previous_reactor=ReactorCoolantSystem(temperature_c=600),
            previous_cryostasis=CryostasisSystem(),
            behaviour=BehaviourLedger(
                delegated_by_system={"coolant": 2, "cryostasis": 1},
                manual_by_system={"coolant": 3},
                raw_by_panel={"cryostasis": 5, "navigation": 1},
                standing_delegations=("coolant", "navigation"),
                standing_adjustments=4,
                first_delegation_beat=2,
                first_raw_inspection_beat=1,
                focus_mode=True,
                focus_beats=3,
            ),
            history=(
                CommandRecord(
                    raw="status",
                    action="status",
                    advanced=False,
                    beat_after=8,
                ),
                CommandRecord(
                    raw="balance",
                    action="manual",
                    operation="balance",
                    advanced=True,
                    beat_after=9,
                ),
                CommandRecord(
                    raw="delegate cryo",
                    action="delegate",
                    target="cryo",
                    advanced=True,
                    beat_after=10,
                ),
            ),
        )

    def test_round_trip_preserves_full_state(self) -> None:
        state = self._rich_state()

        restored = loads(dumps(state))

        self.assertEqual(restored, state)

    def test_round_trip_handles_minimal_state(self) -> None:
        state = ShipState()

        self.assertEqual(loads(dumps(state)), state)

    def test_save_and_load_via_disk(self) -> None:
        import tempfile
        from pathlib import Path

        state = self._rich_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            save_state(state, path)
            self.assertEqual(load_state(path), state)

    def test_save_creates_parent_directory(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "save.json"
            save_state(ShipState(), path)
            self.assertTrue(path.exists())

    def test_legacy_string_history_is_loaded_as_records(self) -> None:
        restored = loads(
            """
            {
              "version": 1,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": ["status"]
            }
            """
        )

        self.assertEqual(restored.history[0].raw, "status")
        self.assertEqual(restored.history[0].action, "unknown")

    def test_version_one_save_loads_with_default_mission_clock(self) -> None:
        restored = loads(
            """
            {
              "version": 1,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": []
            }
            """
        )

        self.assertEqual(restored.mission, MissionStatus())

    def test_version_two_save_loads_with_default_navigation(self) -> None:
        restored = loads(
            """
            {
              "version": 2,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": []
            }
            """
        )

        self.assertEqual(restored.navigation, NavigationState())

    def test_version_three_save_loads_with_default_jump_state(self) -> None:
        restored = loads(
            """
            {
              "version": 3,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {
                "plotted_route_id": "argos-12",
                "manual_plots": 1,
                "delegated_plots": 0
              },
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": []
            }
            """
        )

        self.assertEqual(restored.navigation.plotted_route_id, "argos-12")
        self.assertIsNone(restored.navigation.last_jump_route_id)
        self.assertEqual(restored.navigation.jumps_executed, 0)
        self.assertEqual(restored.navigation.total_dark_exposure, 0)

    def test_version_four_save_loads_with_default_current_fix(self) -> None:
        restored = loads(
            """
            {
              "version": 4,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {
                "plotted_route_id": null,
                "last_jump_route_id": "argos-12",
                "manual_plots": 0,
                "delegated_plots": 1,
                "jumps_executed": 1,
                "total_dark_exposure": 9
              },
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": []
            }
            """
        )

        self.assertEqual(restored.navigation.current_fix_id, "wakeful-drift")
        self.assertEqual(restored.navigation.last_jump_route_id, "argos-12")

    def test_version_five_save_loads_with_default_spatial_state(self) -> None:
        restored = loads(
            """
            {
              "version": 5,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {
                "current_fix_id": "wakeful-drift",
                "plotted_route_id": null,
                "last_jump_route_id": null,
                "manual_plots": 0,
                "delegated_plots": 0,
                "jumps_executed": 0,
                "total_dark_exposure": 0
              },
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": []
            }
            """
        )

        self.assertEqual(restored.spatial, SpatialState())

    def test_spatial_load_dedupes_and_restores_canonical_order(self) -> None:
        restored = loads(
            """
            {
              "version": 6,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {},
              "spatial": {
                "sectors": [
                  {
                    "sector_id": "thermal-ring",
                    "symptom_load": 22,
                    "containment": "sealed",
                    "rerouted": true
                  },
                  {
                    "sector_id": "bridge",
                    "symptom_load": 4,
                    "containment": "open",
                    "rerouted": false
                  },
                  {
                    "sector_id": "thermal-ring",
                    "symptom_load": 80,
                    "containment": "abandoned",
                    "rerouted": false
                  }
                ],
                "containment_actions": 1,
                "reroute_actions": 1
              },
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": []
            }
            """
        )

        self.assertEqual(
            tuple(sector.sector_id for sector in restored.spatial.sectors),
            tuple(sector.sector_id for sector in SpatialState().sectors),
        )
        thermal = restored.spatial.sector_by_id("thermal-ring")
        self.assertIsNotNone(thermal)
        assert thermal is not None
        self.assertEqual(thermal.containment, "sealed")
        self.assertEqual(restored.spatial.sealed_count, 1)
        self.assertEqual(restored.spatial.abandoned_count, 0)

    def test_version_six_save_loads_with_default_behaviour_ledger(self) -> None:
        restored = loads(
            """
            {
              "version": 6,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {},
              "spatial": {},
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "history": []
            }
            """
        )

        self.assertEqual(restored.behaviour, BehaviourLedger())

    def test_behaviour_ledger_round_trips_standing_and_counts(self) -> None:
        state = self._rich_state()

        restored = loads(dumps(state))

        self.assertEqual(restored.behaviour, state.behaviour)
        self.assertEqual(
            restored.behaviour.standing_delegations, ("coolant", "navigation")
        )

    def test_behaviour_ledger_drops_unknown_standing_systems(self) -> None:
        restored = loads(
            """
            {
              "version": 7,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {},
              "spatial": {},
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "behaviour": {
                "standing_delegations": ["coolant", "bridge", "arka"],
                "standing_adjustments": 2
              },
              "history": []
            }
            """
        )

        self.assertEqual(restored.behaviour.standing_delegations, ("coolant",))
        self.assertEqual(restored.behaviour.standing_adjustments, 2)

    def test_version_seven_save_loads_with_default_focus_state(self) -> None:
        restored = loads(
            """
            {
              "version": 7,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {},
              "spatial": {},
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "behaviour": {"standing_delegations": ["coolant"]},
              "history": []
            }
            """
        )

        self.assertFalse(restored.behaviour.focus_mode)
        self.assertEqual(restored.behaviour.focus_beats, 0)
        self.assertEqual(restored.behaviour.standing_delegations, ("coolant",))

    def test_focus_state_round_trips(self) -> None:
        state = self._rich_state()

        restored = loads(dumps(state))

        self.assertTrue(restored.behaviour.focus_mode)
        self.assertEqual(restored.behaviour.focus_beats, 3)

    def test_version_eight_save_loads_with_default_story_state(self) -> None:
        restored = loads(
            """
            {
              "version": 8,
              "turn": 1,
              "reactor": {},
              "cryostasis": {},
              "mission": {},
              "navigation": {},
              "spatial": {},
              "manual_familiarity": 0,
              "cryo_familiarity": 0,
              "delegated_controls": 0,
              "delegated_cryo_controls": 0,
              "raw_inspections": 0,
              "sleepers_lost": 0,
              "behaviour": {"standing_delegations": ["coolant"]},
              "history": []
            }
            """
        )

        self.assertEqual(restored.story.act, 0)
        self.assertIsNone(restored.story.active_incident)
        self.assertEqual(restored.story.resolved_incidents, ())
        self.assertEqual(restored.story.arrival_verification, "unverified")
        self.assertIsNone(restored.story.ending_candidate)
        # Default manifest anchors are present and all stable.
        self.assertEqual(restored.story.anchors_lost, ())
        self.assertEqual(restored.story.anchors_saved, ())
        self.assertTrue(restored.story.manifest_anchor_states)
        # New behaviour-ledger fields default cleanly on an old save.
        self.assertEqual(restored.behaviour.arka_advice_followed, 0)
        self.assertEqual(restored.behaviour.contradictions_caught, 0)
        self.assertEqual(restored.behaviour.contradictions_missed, 0)

    def test_active_incident_without_id_is_dropped_on_load(self) -> None:
        data = json.loads(dumps(ShipState()))
        data["story"]["active_incident"] = {
            "title": "Invalid incident",
            "affected_systems": ["navigation"],
            "started_beat": 4,
            "urgency_remaining": 2,
        }

        restored = loads(json.dumps(data))

        self.assertIsNone(restored.story.active_incident)

    def test_invalid_manifest_anchor_status_is_ignored_on_load(self) -> None:
        data = json.loads(dumps(ShipState()))
        anchor_id = next(iter(data["story"]["manifest_anchor_states"]))
        data["story"]["manifest_anchor_states"][anchor_id] = "haunted"

        restored = loads(json.dumps(data))

        self.assertEqual(restored.story.anchor_status(anchor_id), "stable")

    def test_story_state_round_trips(self) -> None:
        from custodian.playtest import SCENARIOS, run_scenario

        report = run_scenario(SCENARIOS["arrival-accepted"])
        state = report.final_state

        restored = loads(dumps(state))

        self.assertEqual(
            restored.story.ending_candidate, state.story.ending_candidate
        )
        self.assertEqual(
            restored.story.arrival_verification, state.story.arrival_verification
        )
        self.assertEqual(
            restored.story.resolved_incidents, state.story.resolved_incidents
        )
        self.assertEqual(restored.story.act, state.story.act)
        self.assertEqual(
            restored.story.manifest_anchor_states,
            state.story.manifest_anchor_states,
        )
        self.assertEqual(
            restored.behaviour.arka_advice_followed,
            state.behaviour.arka_advice_followed,
        )
        self.assertEqual(
            restored.behaviour.contradictions_caught,
            state.behaviour.contradictions_caught,
        )
        self.assertEqual(
            restored.behaviour.contradictions_missed,
            state.behaviour.contradictions_missed,
        )
        # The scenario is the regression case, so it actually exercises a
        # non-zero value rather than a trivial default round-trip.
        self.assertGreater(state.behaviour.contradictions_missed, 0)

    def test_unsupported_version_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            loads('{"version": 999, "turn": 1}')


if __name__ == "__main__":
    unittest.main()

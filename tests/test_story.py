import unittest
from dataclasses import replace

from custodian.arka import drift_stage
from custodian.models import (
    ANCHOR_LOST,
    ANCHOR_SAVED,
    ANCHOR_WOBBLING,
    BehaviourLedger,
    CommandRecord,
    CryostasisSystem,
    DriftStage,
    IncidentState,
    MissionStatus,
    NavigationState,
    ReactorCoolantSystem,
    ShipState,
    StoryState,
)
from custodian.story import (
    INCIDENTS,
    SHIP_NAME,
    _compute_act,
    advance_story,
    incident_def,
)


def _danger_state(**kwargs) -> ShipState:
    base = dict(
        turn=3,
        reactor=ReactorCoolantSystem(temperature_c=640, pressure_kpa=290),
        cryostasis=CryostasisSystem(neural_stability_pct=70, sleepers_at_risk=10),
    )
    base.update(kwargs)
    return ShipState(**base)


class IncidentCatalogueTests(unittest.TestCase):
    def test_eight_incidents_are_defined(self) -> None:
        self.assertEqual(len(INCIDENTS), 8)

    def test_incident_ids_are_unique(self) -> None:
        ids = [definition.id for definition in INCIDENTS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_incident_def_lookup(self) -> None:
        self.assertIsNotNone(incident_def("first-useful-delegation"))
        self.assertIsNone(incident_def("no-such-incident"))

    def test_ship_is_named(self) -> None:
        self.assertEqual(SHIP_NAME, "Calyx")


class IncidentSchedulerTests(unittest.TestCase):
    def test_first_delegation_activates_when_both_systems_in_danger(self) -> None:
        state = _danger_state()
        advanced, _ = advance_story(state)
        self.assertIsNotNone(advanced.story.active_incident)
        self.assertEqual(
            advanced.story.active_incident.incident_id, "first-useful-delegation"
        )

    def test_first_delegation_resolves_on_delegate_and_records_advice(self) -> None:
        state = _danger_state()
        activated, _ = advance_story(state)

        record = CommandRecord(
            raw="delegate", action="delegate", advanced=True, beat_after=4
        )
        resolved, _ = advance_story(replace(activated, turn=4), record=record)

        self.assertIn("first-useful-delegation", resolved.story.resolved_incidents)
        self.assertIsNone(resolved.story.active_incident)
        self.assertEqual(resolved.behaviour.arka_advice_followed, 1)

    def test_first_delegation_resolves_on_manual_and_records_override(self) -> None:
        state = _danger_state()
        activated, _ = advance_story(state)

        record = CommandRecord(
            raw="balance",
            action="manual",
            operation="balance",
            advanced=True,
            beat_after=4,
        )
        resolved, _ = advance_story(replace(activated, turn=4), record=record)

        self.assertIn("first-useful-delegation", resolved.story.resolved_incidents)
        self.assertEqual(resolved.behaviour.arka_advice_overridden, 1)

    def test_incidents_do_not_repeat_once_resolved(self) -> None:
        state = _danger_state()
        activated, _ = advance_story(state)
        record = CommandRecord(
            raw="delegate", action="delegate", advanced=True, beat_after=4
        )
        resolved, _ = advance_story(replace(activated, turn=4), record=record)

        # Even though both systems remain in danger, the resolved incident is
        # not re-selected.
        again, _ = advance_story(replace(resolved, turn=5))
        active = again.story.active_incident
        if active is not None:
            self.assertNotEqual(active.incident_id, "first-useful-delegation")


class ManifestAnchorTests(unittest.TestCase):
    def test_anchor_wobble_saved_by_manual_cryo_work(self) -> None:
        state = ShipState(
            turn=3,
            cryostasis=CryostasisSystem(neural_stability_pct=70, sleepers_at_risk=8),
        )
        activated, _ = advance_story(state)
        self.assertEqual(
            activated.story.active_incident.incident_id, "manifest-anchor-wobble"
        )
        wobbling = [
            anchor_id
            for anchor_id, status in activated.story.manifest_anchor_states.items()
            if status == ANCHOR_WOBBLING
        ]
        self.assertTrue(wobbling)

        record = CommandRecord(
            raw="stabilise bank",
            action="manual",
            operation="stabilise_bank",
            advanced=True,
            beat_after=4,
        )
        resolved, _ = advance_story(replace(activated, turn=4), record=record)
        self.assertEqual(len(resolved.story.anchors_saved), 1)
        self.assertIn("manifest_anchor_saved", resolved.story.debrief_flags)

    def test_anchor_wobble_lost_when_left_unanswered(self) -> None:
        state = ShipState(
            turn=3,
            cryostasis=CryostasisSystem(neural_stability_pct=70, sleepers_at_risk=8),
        )
        story = state.story
        # Drive the wobble incident to its final watch so the next idle beat expires it.
        activated, _ = advance_story(state)
        idle = CommandRecord(raw="wait", action="wait", advanced=True, beat_after=4)
        current = replace(activated, turn=4)
        for _ in range(activated.story.active_incident.urgency_remaining + 1):
            current, _ = advance_story(current, record=idle)
            if current.story.active_incident is None:
                break
        self.assertEqual(len(current.story.anchors_lost), 1)
        self.assertIn("manifest_anchor_lost", current.story.debrief_flags)


class FocusEjectTests(unittest.TestCase):
    def test_urgent_incident_breaks_focus(self) -> None:
        state = ShipState(
            turn=6,
            delegated_controls=7,
            cryostasis=CryostasisSystem(neural_stability_pct=70, sleepers_at_risk=10),
            behaviour=BehaviourLedger(focus_mode=True, focus_beats=4),
        )
        self.assertEqual(drift_stage(state), DriftStage.WRONG)

        advanced, _ = advance_story(state)
        self.assertEqual(
            advanced.story.active_incident.incident_id, "wrong-calm-summary"
        )
        self.assertFalse(advanced.behaviour.focus_mode)
        self.assertEqual(advanced.behaviour.urgent_incident_ejects, 1)


class ActProgressionTests(unittest.TestCase):
    def test_act_starts_at_wake(self) -> None:
        self.assertEqual(_compute_act(ShipState(turn=0)), 0)

    def test_act_advances_with_competence(self) -> None:
        self.assertEqual(_compute_act(ShipState(turn=2)), 1)

    def test_arrival_proximity_is_final_act(self) -> None:
        state = ShipState(mission=MissionStatus(distance_remaining_tenths_ly=10))
        self.assertEqual(_compute_act(state), 5)

    def test_wrong_drift_is_contradiction_act(self) -> None:
        state = ShipState(turn=6, delegated_controls=7)
        self.assertEqual(drift_stage(state), DriftStage.WRONG)
        self.assertEqual(_compute_act(state), 4)


if __name__ == "__main__":
    unittest.main()

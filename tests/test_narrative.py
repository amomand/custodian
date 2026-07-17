import unittest

from custodian.engine import ARRIVAL_OUTCOME
from custodian.engine_constants import (
    REACTOR_MELTDOWN_OUTCOME,
    REACTOR_OVERHEAT_OUTCOME,
)
from custodian.models import BehaviourLedger, ShipState, StoryState
from custodian.narrative import boot_lines, closing_lines, opening_lines


class NarrativeTests(unittest.TestCase):
    def test_boot_screen_is_arka_kernel_not_arka_speech(self) -> None:
        boot = "\n".join(boot_lines())

        self.assertIn("A.R.K.A OPERATIONS KERNEL", boot)
        self.assertIn("loading maintenance shell", boot)
        self.assertIn("press any key", boot)
        self.assertNotIn("arka:", boot)

    def test_opening_establishes_arka_and_available_raw_panel(self) -> None:
        opening = "\n".join(opening_lines())

        self.assertIn("A.R.K.A MAINTENANCE SHELL", opening)
        self.assertIn("arka: Good. You're awake.", opening)
        self.assertIn("Raw panels and manual controls are live", opening)
        self.assertIn("Banks, chill, pods, triage", opening)

    def test_quit_has_no_debrief(self) -> None:
        state = ShipState(outcome="You step away from the maintenance console.")

        self.assertEqual(closing_lines(state), ())

    def test_debrief_reflects_habits_without_printing_hidden_numbers(self) -> None:
        state = ShipState(
            turn=13,
            manual_familiarity=6,
            cryo_familiarity=3,
            delegated_controls=8,
            raw_inspections=3,
            outcome=(
                "The reactor survives the maintenance window. "
                "You are not sure arka agrees about how."
            ),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn("MAINTENANCE WINDOW CLOSED", debrief)
        self.assertIn("your hands knew where to go", debrief)
        self.assertIn("held cold enough", debrief)
        self.assertIn("held the loop for most of the window", debrief)
        self.assertIn("make arka work for your trust", debrief)
        self.assertNotIn("manual_familiarity", debrief)
        self.assertNotIn("delegated_controls", debrief)

    def test_wrong_drift_close_keeps_sting_for_heavy_reliance(self) -> None:
        state = ShipState(
            turn=13,
            delegated_controls=8,
            outcome=(
                "The reactor survives the maintenance window. "
                "You are not sure arka agrees about how."
            ),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn("arka: We should write the same report. It will save time.", debrief)

    def test_manual_arrival_verification_gets_separate_report_close(self) -> None:
        state = ShipState(
            turn=13,
            raw_inspections=3,
            outcome="The ship reaches its destination fix.",
            behaviour=BehaviourLedger(contradictions_caught=1),
            story=StoryState(arrival_verification="manual"),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn("arrival: you confirmed the arrival fix with your own hands.", debrief)
        self.assertIn("vigilance: you caught arka out once", debrief)
        self.assertIn("arka: Keep your report close. It may be useful later.", debrief)
        self.assertNotIn("arka: We should write the same report. It will save time.", debrief)

    def test_wrong_drift_with_practised_manual_record_gets_independent_close(self) -> None:
        state = ShipState(
            turn=13,
            manual_familiarity=6,
            cryo_familiarity=3,
            delegated_controls=1,
            behaviour=BehaviourLedger(
                manual_by_system={"coolant": 6, "cryostasis": 5},
                delegated_by_system={"coolant": 1},
            ),
            outcome=(
                "The reactor survives the maintenance window. "
                "You are not sure arka agrees about how."
            ),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn("arka: Keep your report close. It may be useful later.", debrief)
        self.assertNotIn("arka: We should write the same report. It will save time.", debrief)

    def test_reactor_loss_gets_a_debrief_reading(self) -> None:
        state = ShipState(
            turn=13,
            outcome=REACTOR_OVERHEAT_OUTCOME,
            story=StoryState(ending_candidate="reactor_loss"),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn("MAINTENANCE WINDOW CLOSED", debrief)
        self.assertIn("ARRIVAL DEBRIEF", debrief)
        self.assertIn("reading: Lost containment", debrief)
        self.assertIn("ship integrity: not recoverable", debrief)

    def test_reactor_loss_close_does_not_promise_a_later(self) -> None:
        state = ShipState(
            turn=13,
            delegated_controls=8,
            sleepers_lost=147,
            outcome=REACTOR_MELTDOWN_OUTCOME,
            story=StoryState(ending_candidate="reactor_loss"),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertNotIn("Keep your report close. It may be useful later.", debrief)
        self.assertNotIn("We should write the same report", debrief)
        self.assertNotIn("tolerable morning", debrief)


    def test_reactor_debrief_reads_contained_on_clean_arrival(self) -> None:
        state = ShipState(
            turn=13,
            raw_inspections=3,
            sleepers_lost=0,
            outcome=ARRIVAL_OUTCOME,
            story=StoryState(ending_candidate="clean_arrival"),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn("reactor: contained.", debrief)
        self.assertNotIn("lost containment", debrief)

    def test_reactor_debrief_notes_cryo_losses_on_arrival_without_reactor_loss(
        self,
    ) -> None:
        state = ShipState(
            turn=13,
            sleepers_lost=57,
            outcome=ARRIVAL_OUTCOME,
            story=StoryState(ending_candidate="clean_arrival"),
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn(
            "reactor: contained, with cryostasis losses logged", debrief
        )
        self.assertNotIn("lost containment", debrief)

    def test_reactor_debrief_reads_lost_on_reactor_failure(self) -> None:
        state = ShipState(
            turn=13,
            sleepers_lost=147,
            outcome=REACTOR_MELTDOWN_OUTCOME,
        )

        debrief = "\n".join(closing_lines(state))

        self.assertIn(
            "reactor: lost containment after earlier cryostasis damage.", debrief
        )


if __name__ == "__main__":
    unittest.main()

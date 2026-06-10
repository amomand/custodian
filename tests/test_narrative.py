import unittest

from custodian.models import ShipState
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

    def test_catastrophic_failure_has_no_arrival_debrief(self) -> None:
        state = ShipState(outcome="Reactor temperature exceeds containment.")

        debrief = "\n".join(closing_lines(state))

        self.assertIn("MAINTENANCE WINDOW CLOSED", debrief)
        self.assertNotIn("ARRIVAL DEBRIEF", debrief)


if __name__ == "__main__":
    unittest.main()

import unittest

from custodian.models import ShipState
from custodian.narrative import closing_lines, opening_lines


class NarrativeTests(unittest.TestCase):
    def test_opening_establishes_arka_and_available_raw_panel(self) -> None:
        opening = "\n".join(opening_lines())

        self.assertIn("A.R.K.A MAINTENANCE SHELL", opening)
        self.assertIn("arka: Good. You're awake.", opening)
        self.assertIn("Raw panel is live", opening)

    def test_quit_has_no_debrief(self) -> None:
        state = ShipState(outcome="You step away from the coolant console.")

        self.assertEqual(closing_lines(state), ())

    def test_debrief_reflects_habits_without_printing_hidden_numbers(self) -> None:
        state = ShipState(
            turn=25,
            manual_familiarity=6,
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
        self.assertIn("held the loop for most of the window", debrief)
        self.assertIn("make arka work for your trust", debrief)
        self.assertNotIn("manual_familiarity", debrief)
        self.assertNotIn("delegated_controls", debrief)


if __name__ == "__main__":
    unittest.main()

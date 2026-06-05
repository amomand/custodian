import unittest

from custodian.models import CryostasisSystem, ReactorCoolantSystem, ShipState
from custodian.objectives import (
    beats_remaining,
    objective_lines,
    priority,
    trend,
)


class ObjectivesTests(unittest.TestCase):
    def test_beats_remaining_counts_down_to_window_close(self) -> None:
        self.assertEqual(beats_remaining(ShipState(turn=1)), 12)
        self.assertEqual(beats_remaining(ShipState(turn=12)), 1)
        self.assertEqual(beats_remaining(ShipState(turn=20)), 0)

    def test_objective_lines_state_goal_and_capacity_asymmetry(self) -> None:
        lines = "\n".join(objective_lines(ShipState()))

        self.assertIn("OBJECTIVE", lines)
        self.assertIn("WATCH", lines)
        self.assertIn("ATTENTION", lines)
        self.assertIn("whole panel", lines)
        # In-world readout must not leak the forbidden meta vocabulary.
        self.assertNotIn("turn", lines.lower())

    def test_priority_names_the_worst_breach(self) -> None:
        state = ShipState(
            reactor=ReactorCoolantSystem(temperature_c=700, impurity_pct=20),
        )

        top = priority(state)

        self.assertIsNotNone(top)
        assert top is not None
        self.assertEqual(top.spec.label, "temperature")

    def test_priority_uses_rate_when_nothing_is_breached_yet(self) -> None:
        state = ShipState(
            reactor=ReactorCoolantSystem(temperature_c=600),
            previous_reactor=ReactorCoolantSystem(temperature_c=580),
        )

        top = priority(state)

        self.assertIsNotNone(top)
        assert top is not None
        self.assertEqual(top.spec.label, "temperature")
        self.assertEqual(top.breach, 0)
        self.assertGreater(top.rate, 0)

    def test_priority_none_when_calm_and_steady(self) -> None:
        state = ShipState(previous_reactor=ReactorCoolantSystem())

        self.assertIsNone(priority(state))

    def test_trend_marks_worsening_direction(self) -> None:
        self.assertEqual(trend(600, 580, "high"), "^!")
        self.assertEqual(trend(560, 580, "high"), "v ")
        self.assertEqual(trend(70, 80, "low"), "v!")
        self.assertEqual(trend(80, 80, "high"), "->")
        self.assertEqual(trend(80, None, "high"), "->")


if __name__ == "__main__":
    unittest.main()

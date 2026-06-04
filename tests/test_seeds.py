import unittest

from custodian.engine import GameEngine
from custodian.seeds import SEEDS, seed_state


class SeedTests(unittest.TestCase):
    def test_expected_seed_names_exist(self) -> None:
        self.assertEqual(
            set(SEEDS),
            {
                "clean-start",
                "post-filter-fouling",
                "pressure-surge",
                "silicate-bloom",
                "thermal-runaway-unpractised",
                "thermal-runaway-practised",
            },
        )

    def test_pressure_surge_seed_has_active_crisis(self) -> None:
        state = seed_state("pressure-surge")

        self.assertIsNotNone(state.crisis)
        self.assertEqual(state.crisis.kind, "pressure_surge")

    def test_final_crisis_seeds_show_manual_competence_difference(self) -> None:
        engine = GameEngine()
        unpractised = seed_state("thermal-runaway-unpractised")
        practised = seed_state("thermal-runaway-practised")

        for command in ("balance", "flush"):
            unpractised = engine.handle(unpractised, command).state
            practised = engine.handle(practised, command).state

        self.assertIsNotNone(unpractised.crisis)
        self.assertIsNone(practised.crisis)

    def test_unknown_seed_reports_known_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "known seeds"):
            seed_state("missing")


if __name__ == "__main__":
    unittest.main()

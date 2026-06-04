import tempfile
import unittest
from pathlib import Path

from custodian.playtest import (
    SCENARIOS,
    commands_from_file,
    run_commands,
    run_scenario,
    scenario_from_file,
    write_report,
)


class PlaytestTests(unittest.TestCase):
    def test_practised_manual_scenario_completes_window(self) -> None:
        report = run_scenario(SCENARIOS["practised-manual"])

        self.assertTrue(report.completed)
        self.assertIn("survives the maintenance window", report.final_outcome)
        self.assertEqual(report.final_state.sleepers_lost, 0)
        self.assertEqual(report.forbidden_hits, ())

    def test_pure_delegation_records_dependence_and_drift(self) -> None:
        report = run_scenario(SCENARIOS["pure-delegation"])

        self.assertGreaterEqual(report.final_state.delegated_controls, 9)
        self.assertEqual(report.final_state.manual_familiarity, 0)
        self.assertGreater(report.final_state.sleepers_lost, 0)
        self.assertIn("arka drift: wrong", "\n".join(report.summary_lines()))

    def test_raw_curious_scenario_completes_with_a_different_cost_profile(self) -> None:
        report = run_scenario(SCENARIOS["raw-curious"])

        self.assertTrue(report.completed)
        self.assertEqual(report.final_state.raw_inspections, 4)
        self.assertEqual(report.final_state.sleepers_lost, 42)
        self.assertIn("survives the maintenance window", report.final_outcome)

    def test_mixed_system_stress_tracks_cryo_delegation(self) -> None:
        report = run_scenario(SCENARIOS["mixed-system-stress"])

        self.assertTrue(report.completed)
        self.assertGreaterEqual(report.final_state.delegated_cryo_controls, 2)
        self.assertIn("delegated cryo interventions", "\n".join(report.summary_lines()))

    def test_transcript_includes_opening_commands_and_closing(self) -> None:
        report = run_commands(("status", "quit"))
        transcript = "\n".join(report.transcript_lines())

        self.assertIn("A.R.K.A MAINTENANCE SHELL", transcript)
        self.assertIn("> status", transcript)
        self.assertIn("> quit", transcript)
        self.assertIn("arka: I will keep the loop warm. Go, then.", transcript)

    def test_write_report_creates_markdown_file(self) -> None:
        report = run_commands(("quit",))
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_report(report, Path(tmpdir))

            self.assertTrue(path.exists())
            self.assertIn("# Playtest: ad-hoc", path.read_text(encoding="utf-8"))

    def test_commands_from_file_ignores_comments_and_transcript_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "route.txt"
            path.write_text(
                "# opening hesitation\n\n> status\nraw\n# let arka work\ndelegate\n",
                encoding="utf-8",
            )

            self.assertEqual(commands_from_file(path), ("status", "raw", "delegate"))
            scenario = scenario_from_file(path)
            self.assertEqual(scenario.name, "route")
            self.assertEqual(scenario.commands, ("status", "raw", "delegate"))

    def test_empty_command_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.txt"
            path.write_text("# nothing yet\n\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "did not contain any commands"):
                scenario_from_file(path)


if __name__ == "__main__":
    unittest.main()

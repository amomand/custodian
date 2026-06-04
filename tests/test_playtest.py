import tempfile
import unittest
from pathlib import Path

from custodian.playtest import SCENARIOS, run_commands, run_scenario, write_report


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
        self.assertIn("arka drift: wrong", "\n".join(report.summary_lines()))

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


if __name__ == "__main__":
    unittest.main()

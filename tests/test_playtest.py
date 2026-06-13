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
    def test_section_nine_golden_routes_are_named(self) -> None:
        expected = {
            "pure-delegation",
            "practised-manual",
            "raw-curious",
            "deep-route-fast-arrival",
            "short-route-cautious-decay",
            "containment-heavy",
            "arka-override-late",
            "focus-mode",
        }

        self.assertTrue(expected.issubset(SCENARIOS))

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

    def test_containment_route_tracks_sector_consequences(self) -> None:
        report = run_scenario(SCENARIOS["containment-route"])
        summary = "\n".join(report.summary_lines())

        self.assertTrue(report.completed)
        self.assertGreaterEqual(report.final_state.spatial.containment_actions, 1)
        self.assertGreaterEqual(report.final_state.spatial.reroute_actions, 1)
        self.assertIn("sector reports:", summary)
        self.assertIn("sealed sectors:", summary)
        self.assertEqual(report.forbidden_hits, ())

    def test_standing_delegation_scenario_reports_reliance(self) -> None:
        report = run_scenario(SCENARIOS["standing-delegation"])
        summary = "\n".join(report.summary_lines())

        # Standing delegation never builds the player's hands, drives drift, and
        # surfaces in the report as behaviour rather than a trust score.
        self.assertEqual(report.final_state.manual_familiarity, 0)
        self.assertGreater(report.final_state.behaviour.standing_adjustments, 0)
        self.assertIn("standing delegations: coolant, cryostasis", summary)
        self.assertIn("arka drift: wrong", summary)
        self.assertEqual(report.forbidden_hits, ())

    def test_focus_mode_scenario_records_dwell_and_reliance(self) -> None:
        report = run_scenario(SCENARIOS["focus-mode"])
        summary = "\n".join(report.summary_lines())

        # Living in the quiet records dwell, never builds hands, and reaches wrong
        # drift — calm bought with vigilance.
        self.assertGreater(report.final_state.behaviour.focus_beats, 0)
        self.assertEqual(report.final_state.manual_familiarity, 0)
        self.assertIn("focus dwell beats:", summary)
        self.assertIn("arka drift: wrong", summary)
        self.assertEqual(report.forbidden_hits, ())

    def test_deep_route_fast_arrival_reaches_destination_by_hand(self) -> None:
        report = run_scenario(SCENARIOS["deep-route-fast-arrival"])
        state = report.final_state

        self.assertTrue(report.completed)
        self.assertEqual(state.mission.distance_remaining_tenths_ly, 0)
        self.assertGreater(
            state.navigation.manual_plots, state.navigation.delegated_plots
        )
        self.assertEqual(state.story.arrival_verification, "manual")
        self.assertEqual(report.forbidden_hits, ())

    def test_short_route_cautious_decay_tracks_attrition(self) -> None:
        report = run_scenario(SCENARIOS["short-route-cautious-decay"])
        state = report.final_state

        self.assertTrue(report.completed)
        self.assertGreaterEqual(state.navigation.jumps_executed, 5)
        self.assertEqual(state.navigation.delegated_plots, 0)
        self.assertGreater(state.mission.cryo_decay_pct, 24)
        self.assertGreater(state.sleepers_lost, 0)
        self.assertEqual(report.forbidden_hits, ())

    def test_containment_heavy_records_multiple_containment_actions(self) -> None:
        report = run_scenario(SCENARIOS["containment-heavy"])
        state = report.final_state

        self.assertTrue(report.completed)
        self.assertGreaterEqual(state.spatial.containment_actions, 3)
        self.assertGreaterEqual(state.spatial.sealed_count, 2)
        self.assertGreaterEqual(state.spatial.abandoned_count, 1)
        self.assertEqual(report.forbidden_hits, ())

    def test_arka_override_late_records_arrival_contradiction_catch(self) -> None:
        report = run_scenario(SCENARIOS["arka-override-late"])
        state = report.final_state
        summary = "\n".join(report.summary_lines())

        self.assertTrue(report.completed)
        self.assertEqual(state.story.arrival_verification, "manual")
        self.assertIn("arrival-disagreement", state.story.resolved_incidents)
        self.assertGreaterEqual(state.behaviour.contradictions_caught, 1)
        self.assertGreaterEqual(state.behaviour.arka_advice_overridden, 1)
        self.assertIn("contradictions missed:", summary)
        self.assertEqual(report.forbidden_hits, ())

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

    def test_arrival_accepted_scenario_reaches_false_arrival(self) -> None:
        report = run_scenario(SCENARIOS["arrival-accepted"])

        self.assertTrue(report.completed)
        self.assertEqual(report.final_state.story.ending_candidate, "false_arrival")
        self.assertEqual(report.forbidden_hits, ())

    def test_arrival_scenarios_record_an_ending_candidate(self) -> None:
        for key in ("arrival-verified", "arrival-accepted"):
            report = run_scenario(SCENARIOS[key])
            self.assertTrue(report.completed)
            self.assertIsNotNone(report.final_state.story.ending_candidate)
            self.assertEqual(report.forbidden_hits, ())

    def test_all_scenarios_avoid_forbidden_phrases(self) -> None:
        for key in SCENARIOS:
            report = run_scenario(SCENARIOS[key])
            self.assertEqual(
                report.forbidden_hits, (), f"{key} leaked a forbidden phrase"
            )


if __name__ == "__main__":
    unittest.main()

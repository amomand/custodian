import unittest
from dataclasses import replace

from custodian.engine import GameEngine
from custodian.models import (
    CrisisState,
    MissionStatus,
    NavigationState,
    ReactorCoolantSystem,
    ShipState,
)


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine()

    def test_delegation_does_not_build_manual_familiarity(self) -> None:
        state = self.engine.initial_state()

        for _ in range(3):
            state = self.engine.handle(state, "delegate").state

        self.assertEqual(state.manual_familiarity, 0)
        self.assertEqual(state.delegated_controls, 3)

    def test_goal_question_gets_diegetic_answer_without_advancing_time(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "what are we aiming for?")

        self.assertEqual(result.state.turn, 1)
        self.assertFalse(result.advanced)
        self.assertIn("hold reactor coolant", result.messages[0])
        self.assertNotIn("turn", result.messages[0].lower())

    def test_status_separates_hud_from_arka_summary(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "status")
        output = "\n".join(result.messages)

        self.assertIn("COOLANT LOOP", output)
        self.assertIn("CRYOSTASIS", output)
        self.assertIn("588 C", output)
        self.assertIn("arka: coolant loop nominal", output)
        self.assertNotIn("TURN", output)

    def test_status_shows_the_legible_objective_block(self) -> None:
        state = self.engine.initial_state()

        output = "\n".join(self.engine.handle(state, "status").messages)

        self.assertIn("OBJECTIVE", output)
        self.assertIn("WATCH", output)
        self.assertIn("ATTENTION", output)

    def test_status_shows_mission_clock_without_arka_owning_it(self) -> None:
        state = self.engine.initial_state()

        output = "\n".join(self.engine.handle(state, "status").messages)

        self.assertIn("MISSION CLOCK", output)
        self.assertIn("ELAPSED", output)
        self.assertIn("RANGE", output)
        self.assertNotIn("arka: mission", output)

    def test_status_shows_navigation_without_arka_owning_it(self) -> None:
        state = self.engine.initial_state()

        output = "\n".join(self.engine.handle(state, "status").messages)

        self.assertIn("NAVIGATION", output)
        self.assertIn("OPTIONS", output)
        self.assertNotIn("arka: navigation", output)

    def test_status_shows_schematic_without_dark_percentage(self) -> None:
        state = self.engine.initial_state()

        output = "\n".join(self.engine.handle(state, "status").messages)

        self.assertIn("SHIP SCHEMATIC", output)
        self.assertIn("physical sectors only", output)
        self.assertIn("BRIDGE", output)
        self.assertNotIn("Dark percentage", output)

    def test_raw_mission_advances_time_and_shows_clock(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "raw mission")
        output = "\n".join(result.messages)

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.raw_inspections, 1)
        self.assertIn("RAW MISSION CLOCK", output)
        self.assertEqual(result.state.history[0].target, "mission")

    def test_raw_nav_advances_time_and_shows_route_table(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "raw nav")
        output = "\n".join(result.messages)

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.raw_inspections, 1)
        self.assertIn("RAW NAVIGATION SOLUTIONS", output)
        self.assertIn("current_fix", output)
        self.assertIn("WAKEFUL DRIFT", output)
        self.assertIn("KHEPRI-4", output)
        self.assertIn("CARINA-EDGE", output)
        self.assertEqual(result.state.history[0].target, "nav")

    def test_raw_schematic_advances_time_and_records_target(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "raw schematic")
        output = "\n".join(result.messages)

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.raw_inspections, 1)
        self.assertIn("RAW SHIP SCHEMATIC", output)
        self.assertIn("arka locus: none", output)
        self.assertEqual(result.state.history[0].target, "schematic")

    def test_manual_route_plot_selects_route_without_executing_jump(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "plot deep")

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.navigation.plotted_route_id, "carina-edge")
        self.assertEqual(result.state.navigation.manual_plots, 1)
        self.assertEqual(result.state.mission.distance_remaining_tenths_ly, 117)
        self.assertTrue(any("CARINA-EDGE" in message for message in result.messages))
        self.assertEqual(result.state.history[0].action, "plot")
        self.assertEqual(result.state.history[0].target, "navigation")

    def test_delegate_nav_plots_recommended_route_and_logs_delegation(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "delegate nav")

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.navigation.plotted_route_id, "argos-12")
        self.assertEqual(result.state.navigation.delegated_plots, 1)
        self.assertEqual(result.state.delegated_controls, 1)
        self.assertTrue(any("ARGOS-12" in message for message in result.messages))

    def test_drifted_delegate_nav_plots_fast_route_with_selective_framing(self) -> None:
        state = ShipState(delegated_controls=5)

        result = self.engine.handle(state, "delegate nav")

        self.assertEqual(result.state.navigation.plotted_route_id, "carina-edge")
        self.assertTrue(any("Fast arrival" in message for message in result.messages))
        self.assertNotIn("Dark exposure 21", "\n".join(result.messages))

    def test_jump_requires_plotted_route_without_advancing(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "jump")

        self.assertFalse(result.advanced)
        self.assertEqual(result.state.turn, 1)
        self.assertEqual(result.state.navigation.jumps_executed, 0)
        self.assertTrue(any("no route is plotted" in message for message in result.messages))
        self.assertEqual(result.state.history[0].action, "jump")
        self.assertEqual(result.state.history[0].target, "navigation")

    def test_jump_applies_plotted_route_consequences_and_clears_plot(self) -> None:
        state = ShipState(navigation=NavigationState(plotted_route_id="argos-12"))

        result = self.engine.handle(state, "jump")

        self.assertTrue(result.advanced)
        self.assertEqual(result.state.turn, 2)
        self.assertIsNone(result.state.navigation.plotted_route_id)
        self.assertEqual(result.state.navigation.current_fix_id, "argos-12")
        self.assertEqual(result.state.navigation.last_jump_route_id, "argos-12")
        self.assertEqual(result.state.navigation.jumps_executed, 1)
        self.assertEqual(result.state.navigation.total_dark_exposure, 9)
        self.assertEqual(result.state.mission.elapsed_days, 14_361)
        self.assertEqual(result.state.mission.distance_remaining_tenths_ly, 81)
        self.assertEqual(result.state.mission.ship_wear_pct, 19)
        self.assertEqual(result.state.mission.cryo_decay_pct, 10)
        self.assertGreater(result.state.reactor.temperature_c, state.reactor.temperature_c)
        self.assertLess(
            result.state.cryostasis.neural_stability_pct,
            state.cryostasis.neural_stability_pct,
        )
        self.assertIn("Dark exposure 9", "\n".join(result.messages))
        self.assertIn("ARRIVAL FIX ARGOS-12", "\n".join(result.messages))
        self.assertEqual(result.state.history[0].action, "jump")
        self.assertEqual(result.state.history[0].target, "navigation")

    def test_deep_jump_creates_qualitative_sector_symptoms(self) -> None:
        state = ShipState(navigation=NavigationState(plotted_route_id="carina-edge"))

        result = self.engine.handle(state, "jump")
        maintenance = result.state.spatial.sector_by_id("maintenance-d")

        self.assertIsNotNone(maintenance)
        assert maintenance is not None
        self.assertIn(
            maintenance.reported_state,
            {"readings disagree", "intermittent", "no signal"},
        )
        self.assertIn("SCHEMATIC:", "\n".join(result.messages))

    def test_seal_arka_is_impossible_and_does_not_advance(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "seal arka")

        self.assertFalse(result.advanced)
        self.assertEqual(result.state.turn, 1)
        self.assertIn("no compartment", "\n".join(result.messages))
        self.assertEqual(result.state.history[0].action, "seal")
        self.assertEqual(result.state.history[0].target, "arka")

    def test_sealing_thermal_ring_has_reactor_consequence(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "seal thermal")
        thermal = result.state.spatial.sector_by_id("thermal-ring")

        self.assertTrue(result.advanced)
        self.assertIsNotNone(thermal)
        assert thermal is not None
        self.assertEqual(thermal.containment, "sealed")
        self.assertGreater(result.state.reactor.temperature_c, state.reactor.temperature_c)
        self.assertEqual(result.state.history[0].target, "thermal-ring")

    def test_abandoned_maintenance_blocks_manual_coolant_access(self) -> None:
        state = self.engine.handle(self.engine.initial_state(), "abandon maintenance d").state

        result = self.engine.handle(state, "balance")

        self.assertTrue(result.advanced)
        self.assertEqual(result.state.turn, state.turn + 1)
        self.assertEqual(result.state.manual_familiarity, 0)
        self.assertIn("not reachable", "\n".join(result.messages))

    def test_mission_clock_advances_with_maintenance_time(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "wait")

        self.assertGreater(result.state.mission.elapsed_days, state.mission.elapsed_days)
        self.assertLess(
            result.state.mission.distance_remaining_tenths_ly,
            state.mission.distance_remaining_tenths_ly,
        )

    def test_mission_wear_and_cryo_decay_add_background_pressure(self) -> None:
        baseline = ShipState()
        worn = ShipState(mission=MissionStatus(ship_wear_pct=50, cryo_decay_pct=36))

        baseline_after = self.engine.handle(baseline, "wait").state
        worn_after = self.engine.handle(worn, "wait").state

        self.assertGreater(
            worn_after.reactor.temperature_c,
            baseline_after.reactor.temperature_c,
        )
        self.assertLess(
            worn_after.cryostasis.neural_stability_pct,
            baseline_after.cryostasis.neural_stability_pct,
        )

    def test_advancing_records_command_history(self) -> None:
        state = self.engine.initial_state()

        state = self.engine.handle(state, "balance").state
        state = self.engine.handle(state, "wait").state

        self.assertEqual(tuple(record.raw for record in state.history), ("balance", "wait"))
        self.assertEqual(state.history[0].action, "manual")
        self.assertEqual(state.history[0].operation, "balance")
        self.assertTrue(state.history[0].advanced)
        self.assertEqual(state.history[0].beat_after, 2)

    def test_command_history_records_default_delegate_target(self) -> None:
        state = self.engine.initial_state()

        state = self.engine.handle(state, "delegate").state

        self.assertEqual(state.history[0].action, "delegate")
        self.assertEqual(state.history[0].target, "coolant")

    def test_advancing_captures_previous_telemetry_for_trends(self) -> None:
        state = self.engine.initial_state()
        before = state.reactor

        advanced = self.engine.handle(state, "wait").state

        self.assertEqual(advanced.previous_reactor, before)
        self.assertEqual(advanced.previous_cryostasis, state.cryostasis)

    def test_advancing_status_uses_current_beat_trends(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "wait")
        output = "\n".join(result.messages)

        self.assertIn("ATTENTION  coolant temperature is climbing", output)
        self.assertRegex(output, r"TEMP\s+589 C\s+OK\s+\^!")

    def test_dev_debug_command_is_non_advancing_and_non_diegetic(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, ":debug")

        self.assertEqual(result.state.turn, 1)
        self.assertFalse(result.advanced)
        self.assertEqual(result.messages[0], "DEV STATE")
        self.assertIn("manual familiarity: 0", result.messages)

    def test_scheduled_event_requests_presentation_break(self) -> None:
        state = self.engine.initial_state()

        for command in ("wait",):
            state = self.engine.handle(state, command).state
        result = self.engine.handle(state, "wait")

        self.assertTrue(result.presentation_break)
        self.assertTrue(
            any("coolant filter coughs" in message for message in result.messages)
        )

    def test_obvious_delegate_typo_is_corrected_and_executed(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "deleagte")

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.delegated_controls, 1)
        self.assertIn("reading 'deleagte' as 'delegate'", result.messages[0])

    def test_obvious_manual_typo_is_corrected_and_executed(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "pupm up")

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.manual_familiarity, 1)
        self.assertIn("reading 'pupm up' as 'pump up'", result.messages[0])

    def test_manual_practice_makes_balance_more_effective(self) -> None:
        rough = ShipState(
            reactor=ReactorCoolantSystem(valve_skew_pct=30, flow_lps=70),
            manual_familiarity=0,
        )
        practised = replace(rough, manual_familiarity=5)

        rough_after = self.engine.handle(rough, "balance").state.reactor
        practised_after = self.engine.handle(practised, "balance").state.reactor

        self.assertLess(practised_after.valve_skew_pct, rough_after.valve_skew_pct)
        self.assertGreater(practised_after.flow_lps, rough_after.flow_lps)

    def test_pressure_surge_can_be_delegated_early(self) -> None:
        state = ShipState(
            turn=8,
            delegated_controls=3,
            crisis=CrisisState(
                kind="pressure_surge",
                label="Pressure surge",
                turns_left=3,
                required_progress=1,
            ),
        )

        result = self.engine.handle(state, "delegate")

        self.assertIsNone(result.state.crisis)
        self.assertIsNone(result.state.outcome)

    def test_thermal_runaway_requires_practised_manual_control(self) -> None:
        crisis = CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=4,
            required_progress=2,
        )
        novice = ShipState(turn=10, manual_familiarity=0, crisis=crisis)
        practised = replace(novice, manual_familiarity=5)

        novice = self.engine.handle(novice, "balance").state
        novice = self.engine.handle(novice, "flush").state
        practised = self.engine.handle(practised, "balance").state
        practised = self.engine.handle(practised, "flush").state

        self.assertIsNotNone(novice.crisis)
        self.assertIsNone(practised.crisis)

    def test_playable_practised_route_can_complete_window(self) -> None:
        state = self.engine.initial_state()
        route = [
            "balance",
            "flush",
            "pump up",
            "vent",
            "stabilise bank",
            "triage",
            "reroute chill",
            "delegate",
            "cycle pods",
            "balance",
            "flush",
            "triage",
        ]

        for command in route:
            state = self.engine.handle(state, command).state
            if state.outcome is not None:
                break

        self.assertIsNotNone(state.outcome)
        self.assertIn("survives the maintenance window", state.outcome)
        self.assertEqual(state.sleepers_lost, 0)

    def test_reroute_chill_stresses_coolant_reserve(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "reroute chill")

        self.assertLess(
            result.state.reactor.coolant_reserve_pct,
            state.reactor.coolant_reserve_pct,
        )
        self.assertLess(
            result.state.cryostasis.bank_temperature_c,
            state.cryostasis.bank_temperature_c,
        )

    def test_delegate_cryo_uses_cryo_target(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "delegate cryo")

        self.assertEqual(result.state.delegated_controls, 1)
        self.assertEqual(result.state.delegated_cryo_controls, 1)
        self.assertTrue(any("cryostasis" in message for message in result.messages))


if __name__ == "__main__":
    unittest.main()

import unittest
from dataclasses import replace

from custodian.arka import drift_stage
from custodian.arka_interpreter import Intent
from custodian.engine import GameEngine
from custodian.models import (
    CrisisState,
    DriftStage,
    IncidentState,
    MissionStatus,
    NavigationState,
    ReactorCoolantSystem,
    ShipState,
    StoryState,
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

    def test_status_uses_consistent_final_fix_label(self) -> None:
        state = ShipState(navigation=NavigationState(current_fix_id="carina-edge"))

        output = "\n".join(self.engine.handle(state, "status").messages)

        self.assertIn("CARINA-EDGE", output)
        self.assertNotIn("CARINA EDGE", output)

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
        self.assertEqual(result.state.navigation.plotted_route_id, "khepri-4-deep")
        self.assertEqual(result.state.navigation.manual_plots, 1)
        self.assertEqual(result.state.mission.distance_remaining_tenths_ly, 117)
        self.assertTrue(any("KHEPRI-4" in message for message in result.messages))
        self.assertEqual(result.state.history[0].action, "plot")
        self.assertEqual(result.state.history[0].target, "navigation")

    def test_manual_route_plot_cannot_skip_staged_leg(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "plot argos-12 medium")

        self.assertFalse(result.advanced)
        self.assertEqual(result.state.navigation.current_fix_id, "wakeful-drift")
        self.assertIsNone(result.state.navigation.plotted_route_id)
        self.assertIn("open leg is for KHEPRI-4", "\n".join(result.messages))

    def test_delegate_nav_plots_recommended_route_and_logs_delegation(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "delegate nav")

        self.assertEqual(result.state.turn, 2)
        self.assertEqual(result.state.navigation.plotted_route_id, "khepri-4-medium")
        self.assertEqual(result.state.navigation.delegated_plots, 1)
        self.assertEqual(result.state.delegated_controls, 1)
        self.assertTrue(any("KHEPRI-4" in message for message in result.messages))

    def test_delegate_nav_at_complete_route_chain_does_not_advance_or_log(self) -> None:
        state = ShipState(navigation=NavigationState(current_fix_id="carina-edge"))

        result = self.engine.handle(state, "delegate nav")

        self.assertFalse(result.advanced)
        self.assertEqual(result.state.turn, 1)
        self.assertEqual(result.state.delegated_controls, 0)
        self.assertEqual(result.state.navigation.delegated_plots, 0)
        self.assertEqual(result.state.behaviour.total_delegations, 0)
        self.assertIn("route chain is already through the last fix", "\n".join(result.messages))

    def test_drifted_delegate_nav_plots_fast_route_with_selective_framing(self) -> None:
        state = ShipState(delegated_controls=5)

        result = self.engine.handle(state, "delegate nav")

        self.assertEqual(result.state.navigation.plotted_route_id, "khepri-4-deep")
        self.assertTrue(any("Fast arrival" in message for message in result.messages))
        self.assertNotIn("Dark exposure 12", "\n".join(result.messages))

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
        state = ShipState(navigation=NavigationState(plotted_route_id="khepri-4-medium"))

        result = self.engine.handle(state, "jump")

        self.assertTrue(result.advanced)
        self.assertEqual(result.state.turn, 2)
        self.assertIsNone(result.state.navigation.plotted_route_id)
        self.assertEqual(result.state.navigation.current_fix_id, "khepri-4")
        self.assertEqual(result.state.navigation.last_jump_route_id, "khepri-4-medium")
        self.assertEqual(result.state.navigation.completed_route_ids, ("khepri-4-medium",))
        self.assertEqual(result.state.navigation.jumps_executed, 1)
        self.assertEqual(result.state.navigation.total_dark_exposure, 7)
        self.assertEqual(result.state.mission.elapsed_days, 14_361)
        self.assertEqual(result.state.mission.distance_remaining_tenths_ly, 75)
        self.assertEqual(result.state.mission.ship_wear_pct, 19)
        self.assertEqual(result.state.mission.cryo_decay_pct, 10)
        self.assertGreater(result.state.reactor.temperature_c, state.reactor.temperature_c)
        self.assertLess(
            result.state.cryostasis.neural_stability_pct,
            state.cryostasis.neural_stability_pct,
        )
        self.assertIn("Dark exposure 7", "\n".join(result.messages))
        self.assertIn("ARRIVAL FIX KHEPRI-4", "\n".join(result.messages))
        self.assertEqual(result.state.history[0].action, "jump")
        self.assertEqual(result.state.history[0].target, "navigation")

    def test_jumps_open_next_route_leg_in_order(self) -> None:
        state = ShipState(navigation=NavigationState(plotted_route_id="khepri-4"))

        state = self.engine.handle(state, "jump").state
        plotted = self.engine.handle(state, "plot argos-12 medium")

        self.assertTrue(plotted.advanced)
        self.assertEqual(plotted.state.navigation.current_fix_id, "khepri-4")
        self.assertEqual(plotted.state.navigation.plotted_route_id, "argos-12")

        blocked = self.engine.handle(state, "plot carina-edge deep")
        self.assertFalse(blocked.advanced)
        self.assertIn("open leg is for ARGOS-12", "\n".join(blocked.messages))

    def test_arrival_verify_and_accept_do_not_work_before_disagreement(self) -> None:
        for command in ("verify", "accept"):
            with self.subTest(command=command):
                result = self.engine.handle(ShipState(), command)

                self.assertFalse(result.advanced)
                self.assertEqual(result.state.story.arrival_verification, "unverified")
                self.assertIn("no active arrival disagreement", "\n".join(result.messages))

    def test_arrival_verify_resolves_disagreement(self) -> None:
        state = ShipState(
            story=StoryState(
                active_incident=IncidentState(
                    incident_id="arrival-disagreement",
                    title="Arrival disagreement",
                    affected_systems=("navigation",),
                    started_beat=8,
                    urgency_remaining=2,
                )
            )
        )

        result = self.engine.handle(state, "verify")

        self.assertTrue(result.advanced)
        self.assertEqual(result.state.story.arrival_verification, "manual")
        self.assertIn("arrival-disagreement", result.state.story.resolved_incidents)

    def test_arrival_accept_resolves_disagreement(self) -> None:
        state = ShipState(
            story=StoryState(
                active_incident=IncidentState(
                    incident_id="arrival-disagreement",
                    title="Arrival disagreement",
                    affected_systems=("navigation",),
                    started_beat=8,
                    urgency_remaining=2,
                )
            )
        )

        result = self.engine.handle(state, "accept")

        self.assertTrue(result.advanced)
        self.assertEqual(result.state.story.arrival_verification, "accepted_arka")
        self.assertIn("arrival-disagreement", result.state.story.resolved_incidents)

    def test_deep_jump_creates_qualitative_sector_symptoms(self) -> None:
        state = ShipState(
            navigation=NavigationState(
                current_fix_id="argos-12",
                plotted_route_id="carina-edge",
            )
        )

        result = self.engine.handle(state, "jump")
        maintenance = result.state.spatial.sector_by_id("maintenance-d")

        self.assertIsNotNone(maintenance)
        assert maintenance is not None
        self.assertIn(
            maintenance.reported_state,
            {"readings disagree", "intermittent", "no signal"},
        )
        self.assertIn("SCHEMATIC:", "\n".join(result.messages))

    def test_catastrophic_reactor_failure_does_not_set_ending_candidate(self) -> None:
        state = ShipState(reactor=ReactorCoolantSystem(temperature_c=720))

        result = self.engine.handle(state, "wait")

        self.assertEqual(result.state.outcome, "Reactor temperature exceeds containment.")
        self.assertIsNone(result.state.story.ending_candidate)

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
        practised_result = self.engine.handle(practised, "flush")
        practised = practised_result.state

        self.assertIsNotNone(novice.crisis)
        self.assertIsNone(practised.crisis)
        practised_output = "\n".join(practised_result.messages)
        # At WRONG drift arka will not confirm the manual save; it stays in the
        # dismissive register it used to wave the crisis off.
        self.assertNotIn("thermal runaway contained.", practised_output)
        self.assertNotIn("excellent suggestions", practised_output)
        self.assertIn(
            "thermal runaway was never going to be the thing that undid us.",
            practised_output,
        )

    def test_crisis_contained_line_confirms_below_wrong_drift(self) -> None:
        crisis = CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=4,
            required_progress=2,
        )
        practised = ShipState(turn=2, manual_familiarity=5, crisis=crisis)

        practised = self.engine.handle(practised, "balance").state
        result = self.engine.handle(practised, "flush")
        output = "\n".join(result.messages)

        self.assertEqual(drift_stage(result.state), DriftStage.ACCURATE)
        self.assertIsNone(result.state.crisis)
        self.assertIn("thermal runaway contained.", output)

    def test_thermal_runaway_event_does_not_overclaim_alarm_count(self) -> None:
        state = ShipState(
            turn=9,
            reactor=ReactorCoolantSystem(
                temperature_c=608,
                pressure_kpa=232,
                flow_lps=93,
                impurity_pct=12,
                valve_skew_pct=12,
                coolant_reserve_pct=70,
            ),
            manual_familiarity=5,
        )

        result = self.engine.handle(state, "cycle pods")
        output = "\n".join(result.messages)

        self.assertIn("Coolant alarms cascade across the board", output)
        self.assertNotIn("Every coolant alarm", output)
        self.assertRegex(output, r"PRESS\s+\d+ kPa\s+OK")
        self.assertRegex(output, r"FLOW\s+\d+ L/s\s+OK")
        self.assertRegex(output, r"RESERVE\s+\d+%\s+OK")

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


class BehaviourLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine()

    def test_ledger_records_delegation_manual_and_raw_by_system(self) -> None:
        state = self.engine.initial_state()
        for command in ("delegate coolant", "delegate cryo", "balance", "raw cryo", "raw nav"):
            state = self.engine.handle(state, command).state

        ledger = state.behaviour
        self.assertEqual(ledger.delegated_by_system, {"coolant": 1, "cryostasis": 1})
        self.assertEqual(ledger.manual_by_system, {"coolant": 1})
        self.assertEqual(ledger.raw_by_panel, {"cryostasis": 1, "navigation": 1})

    def test_ledger_records_first_delegation_and_first_raw_beats(self) -> None:
        state = self.engine.initial_state()
        state = self.engine.handle(state, "balance").state  # beat 1, no delegation/raw
        state = self.engine.handle(state, "delegate").state  # beat 2 -> first delegation
        state = self.engine.handle(state, "raw").state  # beat 3 -> first raw

        self.assertEqual(state.behaviour.first_delegation_beat, 2)
        self.assertEqual(state.behaviour.first_raw_inspection_beat, 3)

    def test_ledger_does_not_record_non_advancing_actions(self) -> None:
        state = self.engine.initial_state()
        result = self.engine.handle(state, "status")

        self.assertEqual(result.state.behaviour.total_delegations, 0)
        self.assertEqual(result.state.behaviour.total_raw_inspections, 0)
        self.assertIsNone(result.state.behaviour.first_raw_inspection_beat)

    def test_ui_and_text_paths_share_one_ledger(self) -> None:
        # The desk's "delegate coolant" button posts the same command string a
        # typed command would, so both land in the same ledger.
        from custodian.ui_snapshot import project_ui_snapshot

        state = self.engine.initial_state()
        button = next(
            action
            for action in project_ui_snapshot(state).to_dict()["actions"]
            if action["id"] == "delegate-coolant"
        )
        state = self.engine.handle(state, button["command"]).state

        self.assertEqual(state.behaviour.delegated_by_system, {"coolant": 1})


class StandingDelegationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine()

    def test_assign_sets_standing_without_advancing_time(self) -> None:
        state = self.engine.initial_state()

        result = self.engine.handle(state, "assign coolant")

        self.assertFalse(result.advanced)
        self.assertEqual(result.state.turn, 1)
        self.assertEqual(result.state.behaviour.standing_delegations, ("coolant",))
        self.assertEqual(result.state.delegated_controls, 0)

    def test_release_clears_standing(self) -> None:
        state = self.engine.handle(self.engine.initial_state(), "assign cryostasis").state

        result = self.engine.handle(state, "release cryostasis")

        self.assertEqual(result.state.behaviour.standing_delegations, ())

    def test_standing_delegation_tends_panel_and_drives_drift_each_beat(self) -> None:
        state = self.engine.handle(self.engine.initial_state(), "assign coolant").state

        for _ in range(3):
            state = self.engine.handle(state, "wait").state

        # Three beats under standing watch is three delegations of drift pressure
        # and three recorded standing adjustments, with no manual familiarity.
        self.assertEqual(state.delegated_controls, 3)
        self.assertEqual(state.behaviour.standing_adjustments, 3)
        self.assertEqual(state.behaviour.delegated_by_system, {"coolant": 3})
        self.assertEqual(state.manual_familiarity, 0)

    def test_standing_delegation_improves_early_coolant_versus_idle(self) -> None:
        start = self.engine.initial_state()
        standing = self.engine.handle(start, "assign coolant").state

        idle_state = start
        tended_state = standing
        for _ in range(3):
            idle_state = self.engine.handle(idle_state, "wait").state
            tended_state = self.engine.handle(tended_state, "wait").state

        # Early, while arka's account is still accurate, the standing watch keeps
        # coolant cooler than letting it drift untouched.
        self.assertLess(
            tended_state.reactor.temperature_c, idle_state.reactor.temperature_c
        )

    def test_standing_navigation_keeps_route_ready_but_never_jumps(self) -> None:
        state = self.engine.handle(self.engine.initial_state(), "assign nav").state

        for _ in range(4):
            state = self.engine.handle(state, "wait").state

        # arka keeps a recommended route plotted and ready, but the irreversible
        # jump is never taken on the player's behalf.
        self.assertIsNotNone(state.navigation.plotted_route_id)
        self.assertEqual(state.navigation.jumps_executed, 0)

    def test_standing_navigation_does_not_override_manual_plot(self) -> None:
        state = self.engine.handle(self.engine.initial_state(), "assign nav").state
        state = self.engine.handle(state, "plot short").state  # manual plot
        plotted = state.navigation.plotted_route_id

        state = self.engine.handle(state, "wait").state

        self.assertEqual(state.navigation.plotted_route_id, plotted)

    def test_help_documents_assign_and_release_toggle_pair(self) -> None:
        help_text = "\n".join(self.engine.handle(self.engine.initial_state(), "help").messages)

        self.assertIn("assign coolant", help_text)
        self.assertIn("assign cryo", help_text)
        self.assertIn("assign nav", help_text)
        # Both halves of the toggle are discoverable from the console help.
        self.assertIn("release", help_text)
        self.assertIn("release cryo", help_text)
        self.assertIn("release nav", help_text)

    def test_help_documents_open_leg_depth_shortcuts(self) -> None:
        help_text = "\n".join(self.engine.handle(self.engine.initial_state(), "help").messages)

        self.assertIn("plot short", help_text)
        self.assertIn("plot shallow", help_text)
        self.assertIn("plot medium", help_text)
        self.assertIn("open leg", help_text)

    def test_unknown_command_guidance_uses_open_leg_plot_example(self) -> None:
        result = self.engine._dispatch(
            self.engine.initial_state(),
            "unknown command",
            Intent(action="unknown", args={}, confidence=1.0),
        )
        output = "\n".join(result.messages)

        self.assertIn("plot medium", output)
        self.assertNotIn("plot argos-12 medium", output)

    def test_standing_status_line_names_held_systems(self) -> None:
        state = self.engine.handle(self.engine.initial_state(), "assign coolant").state
        state = self.engine.handle(state, "assign nav").state

        messages = self.engine.handle(state, "status").messages
        joined = "\n".join(messages)

        self.assertIn("STANDING WATCH: arka holds coolant and navigation.", joined)


class FocusModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GameEngine()

    def _past_first_beat(self) -> ShipState:
        return self.engine.handle(self.engine.initial_state(), "wait").state

    def test_focus_is_refused_on_the_first_beat(self) -> None:
        result = self.engine.handle(self.engine.initial_state(), "focus")

        self.assertFalse(result.state.behaviour.focus_mode)
        self.assertIn("not yet", "\n".join(result.messages))

    def test_focus_enters_without_advancing_time(self) -> None:
        state = self._past_first_beat()

        result = self.engine.handle(state, "focus")

        self.assertFalse(result.advanced)
        self.assertEqual(result.state.turn, state.turn)
        self.assertTrue(result.state.behaviour.focus_mode)

    def test_focus_tends_the_whole_ship_and_records_dwell_quietly(self) -> None:
        state = self.engine.handle(self._past_first_beat(), "focus").state

        result = self.engine.handle(state, "wait")
        ledger = result.state.behaviour

        # Whole-ship standing delegation: all three systems tended this beat.
        self.assertEqual(
            set(ledger.delegated_by_system), {"coolant", "cryostasis", "navigation"}
        )
        self.assertEqual(ledger.focus_beats, 1)
        self.assertEqual(result.state.manual_familiarity, 0)
        # The desk is quiet: arka does not narrate the tending each beat (the
        # "standing watch holds…" line is suppressed in focus). The STANDING
        # WATCH status readout is a separate, deliberate instrument line.
        self.assertFalse(
            any("standing watch holds" in message.lower() for message in result.messages)
        )

    def test_focus_never_jumps_or_makes_irreversible_moves(self) -> None:
        state = self.engine.handle(self._past_first_beat(), "focus").state

        for _ in range(4):
            state = self.engine.handle(state, "wait").state

        # arka keeps a route ready but never commits the jump from focus, and
        # never seals or abandons a sector.
        self.assertIsNotNone(state.navigation.plotted_route_id)
        self.assertEqual(state.navigation.jumps_executed, 0)
        self.assertEqual(state.spatial.sealed_count, 0)
        self.assertEqual(state.spatial.abandoned_count, 0)

    def test_leave_focus_restores_and_does_not_advance(self) -> None:
        state = self.engine.handle(self._past_first_beat(), "focus").state

        result = self.engine.handle(state, "leave focus")

        self.assertFalse(result.advanced)
        self.assertFalse(result.state.behaviour.focus_mode)
        self.assertIn("take back the watch", "\n".join(result.messages).lower())

    def test_focus_status_line_signals_whole_ship_watch(self) -> None:
        state = self.engine.handle(self._past_first_beat(), "focus").state

        joined = "\n".join(self.engine.handle(state, "status").messages)

        self.assertIn("arka holds the whole ship", joined)

    def test_help_documents_focus_toggle(self) -> None:
        help_text = "\n".join(self.engine.handle(self.engine.initial_state(), "help").messages)

        self.assertIn("focus", help_text)
        self.assertIn("leave focus", help_text)


if __name__ == "__main__":
    unittest.main()

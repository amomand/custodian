import unittest
from dataclasses import replace

from custodian.engine import GameEngine
from custodian.models import CrisisState, ReactorCoolantSystem, ShipState


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

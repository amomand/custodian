import unittest

from custodian.arka_interpreter import ArkaInterpreter
from custodian.config import Config
from custodian.engine import GameEngine
from custodian.models import NavigationState, ShipState
from custodian.web_session import BrowserSession, SessionStore


def no_ai_engine() -> GameEngine:
    return GameEngine(ArkaInterpreter(Config(custodian_ai=False)))


class WebSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SessionStore(engine_factory=no_ai_engine)

    def test_create_session_opens_without_mutating_engine_state(self) -> None:
        session = self.store.create()
        output = "\n".join(session.last_messages)

        self.assertEqual(session.state.turn, 1)
        self.assertEqual(session.state.history, ())
        self.assertIn("A.R.K.A MAINTENANCE SHELL", output)
        self.assertIn("OBJECTIVE", output)

    def test_command_dispatch_uses_engine_and_records_transcript(self) -> None:
        session = self.store.create()

        response = self.store.command(session.session_id, "wait")

        self.assertEqual(response.snapshot["turn"], 2)
        self.assertEqual(response.snapshot["ui"]["mission"]["beat"], 2)
        self.assertIn("coolant", response.snapshot["ui"]["systems"])
        self.assertIsNone(response.snapshot["ui"]["dev"])
        self.assertEqual(session.state.history[0].raw, "wait")
        self.assertEqual(session.state.history[0].action, "wait")
        self.assertIn("> wait", session.transcript_lines())

    def test_dev_snapshot_requires_explicit_path(self) -> None:
        session = self.store.create()
        self.store.command(session.session_id, "delegate")

        normal = self.store.snapshot(session.session_id)
        dev = self.store.snapshot(session.session_id, include_dev=True)

        self.assertIsNone(normal["ui"]["dev"])
        self.assertEqual(dev["ui"]["dev"]["delegated_controls"], 1)
        self.assertIn("manual_familiarity", dev["ui"]["dev"])

    def test_web_command_and_snapshot_lines_sanitise_hidden_exposure(self) -> None:
        session = BrowserSession(
            "jumping",
            no_ai_engine(),
            ShipState(navigation=NavigationState(plotted_route_id="argos-12")),
        )

        response = session.command("jump")
        encoded_snapshot = str(response.snapshot)
        encoded_messages = "\n".join(response.messages)

        self.assertIn("exposure band moderate", encoded_messages)
        self.assertNotIn("Dark exposure 9", encoded_messages)
        self.assertNotIn("dark 9", encoded_snapshot)
        self.assertNotIn("dark_exposure_total", encoded_snapshot)
        self.assertIn(
            "exposure band moderate",
            "\n".join(response.snapshot["transcript_tail"]),
        )

    def test_sessions_do_not_share_mutable_ship_state(self) -> None:
        first = self.store.create()
        second = self.store.create()

        self.store.command(first.session_id, "wait")

        self.assertEqual(first.state.turn, 2)
        self.assertEqual(second.state.turn, 1)
        self.assertEqual(second.state.history, ())

    def test_save_and_load_restore_serialised_state(self) -> None:
        session = self.store.create()
        self.store.command(session.session_id, "wait")
        saved = self.store.save(session.session_id)["save"]
        self.store.command(session.session_id, "pump up")

        self.assertEqual(session.state.turn, 3)

        self.store.load(session.session_id, text=saved)

        self.assertEqual(session.state.turn, 2)
        self.assertEqual(session.state.history[-1].raw, "wait")

    def test_no_model_mode_keeps_off_script_input_deterministic(self) -> None:
        session = self.store.create()

        response = self.store.command(session.session_id, "sing to the coolant")

        self.assertFalse(response.snapshot["is_finished"])
        self.assertEqual(session.state.turn, 1)
        self.assertIn("arka: I heard that.", "\n".join(response.messages))

    def test_finished_session_does_not_repeat_closing_debrief(self) -> None:
        session = BrowserSession(
            "finished",
            no_ai_engine(),
            ShipState(outcome="The reactor survives the maintenance window."),
        )

        response = session.command("status")

        self.assertIn("already closed", "\n".join(response.messages))
        self.assertNotIn("MAINTENANCE WINDOW CLOSED", "\n".join(response.messages))


if __name__ == "__main__":
    unittest.main()

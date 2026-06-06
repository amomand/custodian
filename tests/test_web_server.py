import json
import threading
import unittest
from urllib.request import Request, urlopen

from custodian.arka_interpreter import ArkaInterpreter
from custodian.config import Config
from custodian.engine import GameEngine
from custodian.web_server import make_server
from custodian.web_session import SessionStore


def no_ai_engine() -> GameEngine:
    return GameEngine(ArkaInterpreter(Config(custodian_ai=False)))


class WebServerTests(unittest.TestCase):
    def setUp(self) -> None:
        store = SessionStore(engine_factory=no_ai_engine)
        self.server = make_server("127.0.0.1", 0, store=store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def test_session_command_and_snapshot_endpoints(self) -> None:
        created = self._post("/api/session")
        session_id = created["session_id"]

        command = self._post(f"/api/session/{session_id}/command", {"command": "wait"})
        snapshot = self._get(f"/api/session/{session_id}/snapshot")

        self.assertEqual(command["snapshot"]["turn"], 2)
        self.assertEqual(snapshot["turn"], 2)
        self.assertEqual(snapshot["history"][0]["raw"], "wait")
        self.assertIn("status", snapshot)

    def test_save_load_and_transcript_endpoints(self) -> None:
        created = self._post("/api/session")
        session_id = created["session_id"]
        self._post(f"/api/session/{session_id}/command", {"command": "wait"})
        saved = self._post(f"/api/session/{session_id}/save")
        self._post(f"/api/session/{session_id}/command", {"command": "pump up"})

        loaded = self._post(f"/api/session/{session_id}/load", {"save": saved["save"]})
        transcript = self._get(f"/api/session/{session_id}/transcript")

        self.assertEqual(loaded["snapshot"]["turn"], 2)
        self.assertIn("> wait", transcript["lines"])
        self.assertIn("Session image restored", "\n".join(transcript["lines"]))

    def _get(self, path: str) -> dict:
        with urlopen(f"{self.base_url}{path}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post(self, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload or {}).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method="POST",
            headers={"content-type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

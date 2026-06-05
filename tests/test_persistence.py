import unittest

from custodian.models import (
    CrisisState,
    CryostasisSystem,
    ReactorCoolantSystem,
    ShipState,
)
from custodian.persistence import dumps, loads, load_state, save_state


class PersistenceTests(unittest.TestCase):
    def _rich_state(self) -> ShipState:
        return ShipState(
            turn=8,
            reactor=ReactorCoolantSystem(temperature_c=611, pressure_kpa=288),
            cryostasis=CryostasisSystem(neural_stability_pct=80, sleepers_at_risk=14),
            manual_familiarity=4,
            cryo_familiarity=2,
            delegated_controls=3,
            delegated_cryo_controls=1,
            raw_inspections=5,
            sleepers_lost=42,
            crisis=CrisisState(
                kind="pressure_surge",
                label="Pressure surge",
                turns_left=2,
                required_progress=1,
                progress=0,
            ),
            previous_reactor=ReactorCoolantSystem(temperature_c=600),
            previous_cryostasis=CryostasisSystem(),
            history=("status", "balance", "delegate"),
        )

    def test_round_trip_preserves_full_state(self) -> None:
        state = self._rich_state()

        restored = loads(dumps(state))

        self.assertEqual(restored, state)

    def test_round_trip_handles_minimal_state(self) -> None:
        state = ShipState()

        self.assertEqual(loads(dumps(state)), state)

    def test_save_and_load_via_disk(self) -> None:
        import tempfile
        from pathlib import Path

        state = self._rich_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            save_state(state, path)
            self.assertEqual(load_state(path), state)

    def test_unsupported_version_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            loads('{"version": 999, "turn": 1}')


if __name__ == "__main__":
    unittest.main()

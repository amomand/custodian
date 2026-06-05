from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from custodian.models import (
    CrisisState,
    CryostasisSystem,
    ReactorCoolantSystem,
    ShipState,
)


SAVE_VERSION = 1
DEFAULT_SAVE_PATH = Path("custodian-save.json")


def state_to_dict(state: ShipState) -> dict:
    return {
        "version": SAVE_VERSION,
        "turn": state.turn,
        "reactor": asdict(state.reactor),
        "cryostasis": asdict(state.cryostasis),
        "manual_familiarity": state.manual_familiarity,
        "cryo_familiarity": state.cryo_familiarity,
        "delegated_controls": state.delegated_controls,
        "delegated_cryo_controls": state.delegated_cryo_controls,
        "raw_inspections": state.raw_inspections,
        "sleepers_lost": state.sleepers_lost,
        "crisis": asdict(state.crisis) if state.crisis is not None else None,
        "outcome": state.outcome,
        "previous_reactor": (
            asdict(state.previous_reactor) if state.previous_reactor is not None else None
        ),
        "previous_cryostasis": (
            asdict(state.previous_cryostasis)
            if state.previous_cryostasis is not None
            else None
        ),
        "history": list(state.history),
    }


def state_from_dict(data: dict) -> ShipState:
    version = data.get("version")
    if version != SAVE_VERSION:
        raise ValueError(f"unsupported save version {version!r}; expected {SAVE_VERSION}")

    crisis = data.get("crisis")
    return ShipState(
        turn=data["turn"],
        reactor=ReactorCoolantSystem(**data["reactor"]),
        cryostasis=CryostasisSystem(**data["cryostasis"]),
        manual_familiarity=data["manual_familiarity"],
        cryo_familiarity=data["cryo_familiarity"],
        delegated_controls=data["delegated_controls"],
        delegated_cryo_controls=data["delegated_cryo_controls"],
        raw_inspections=data["raw_inspections"],
        sleepers_lost=data["sleepers_lost"],
        crisis=CrisisState(**crisis) if crisis is not None else None,
        outcome=data.get("outcome"),
        previous_reactor=_optional_reactor(data.get("previous_reactor")),
        previous_cryostasis=_optional_cryo(data.get("previous_cryostasis")),
        history=tuple(data.get("history", ())),
    )


def dumps(state: ShipState) -> str:
    return json.dumps(state_to_dict(state), indent=2)


def loads(text: str) -> ShipState:
    return state_from_dict(json.loads(text))


def save_state(state: ShipState, path: Path = DEFAULT_SAVE_PATH) -> Path:
    path.write_text(dumps(state), encoding="utf-8")
    return path


def load_state(path: Path = DEFAULT_SAVE_PATH) -> ShipState:
    return loads(path.read_text(encoding="utf-8"))


def _optional_reactor(data: dict | None) -> ReactorCoolantSystem | None:
    return None if data is None else ReactorCoolantSystem(**data)


def _optional_cryo(data: dict | None) -> CryostasisSystem | None:
    return None if data is None else CryostasisSystem(**data)

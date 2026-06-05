from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from custodian.models import (
    CommandRecord,
    CrisisState,
    CryostasisSystem,
    MissionStatus,
    NavigationState,
    ReactorCoolantSystem,
    RouteOption,
    ShipState,
)


SAVE_VERSION = 5
SUPPORTED_SAVE_VERSIONS = {1, 2, 3, 4, SAVE_VERSION}
DEFAULT_SAVE_PATH = Path("saves/custodian-save.json")


def state_to_dict(state: ShipState) -> dict:
    return {
        "version": SAVE_VERSION,
        "turn": state.turn,
        "reactor": asdict(state.reactor),
        "cryostasis": asdict(state.cryostasis),
        "mission": asdict(state.mission),
        "navigation": asdict(state.navigation),
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
        "history": [asdict(record) for record in state.history],
    }


def state_from_dict(data: dict) -> ShipState:
    version = data.get("version")
    if version not in SUPPORTED_SAVE_VERSIONS:
        raise ValueError(
            f"unsupported save version {version!r}; expected one of "
            f"{sorted(SUPPORTED_SAVE_VERSIONS)}"
        )

    crisis = data.get("crisis")
    return ShipState(
        turn=data["turn"],
        reactor=ReactorCoolantSystem(**data["reactor"]),
        cryostasis=CryostasisSystem(**data["cryostasis"]),
        mission=MissionStatus(**data.get("mission", {})),
        navigation=_navigation_from_data(data.get("navigation")),
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
        history=_history_from_data(data.get("history", ())),
    )


def dumps(state: ShipState) -> str:
    return json.dumps(state_to_dict(state), indent=2)


def loads(text: str) -> ShipState:
    return state_from_dict(json.loads(text))


def save_state(state: ShipState, path: Path = DEFAULT_SAVE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(state) + "\n", encoding="utf-8")
    return path


def load_state(path: Path = DEFAULT_SAVE_PATH) -> ShipState:
    return loads(path.read_text(encoding="utf-8"))


def _optional_reactor(data: dict | None) -> ReactorCoolantSystem | None:
    return None if data is None else ReactorCoolantSystem(**data)


def _optional_cryo(data: dict | None) -> CryostasisSystem | None:
    return None if data is None else CryostasisSystem(**data)


def _navigation_from_data(data: object) -> NavigationState:
    if not isinstance(data, dict):
        return NavigationState()

    raw_options = data.get("options", ())
    options: list[RouteOption] = []
    if isinstance(raw_options, (list, tuple)):
        for option in raw_options:
            if isinstance(option, dict):
                options.append(RouteOption(**option))

    return NavigationState(
        options=tuple(options) or NavigationState().options,
        current_fix_id=str(data.get("current_fix_id", "wakeful-drift")),
        plotted_route_id=_optional_str(data.get("plotted_route_id")),
        last_jump_route_id=_optional_str(data.get("last_jump_route_id")),
        manual_plots=int(data.get("manual_plots", 0)),
        delegated_plots=int(data.get("delegated_plots", 0)),
        jumps_executed=int(data.get("jumps_executed", 0)),
        total_dark_exposure=int(data.get("total_dark_exposure", 0)),
    )


def _history_from_data(data: object) -> tuple[CommandRecord, ...]:
    if not isinstance(data, (list, tuple)):
        return ()

    records: list[CommandRecord] = []
    for item in data:
        if isinstance(item, str):
            records.append(CommandRecord(raw=item, action="unknown"))
        elif isinstance(item, dict):
            records.append(
                CommandRecord(
                    raw=str(item.get("raw", "")),
                    action=str(item.get("action", "unknown")),
                    target=_optional_str(item.get("target")),
                    operation=_optional_str(item.get("operation")),
                    advanced=bool(item.get("advanced", False)),
                    beat_after=int(item.get("beat_after", 1)),
                )
            )
    return tuple(records)


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)

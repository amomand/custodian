from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from custodian.models import (
    BehaviourLedger,
    CommandRecord,
    CrisisState,
    CryostasisSystem,
    MissionStatus,
    NavigationState,
    ReactorCoolantSystem,
    RouteOption,
    ShipState,
    ShipSector,
    SpatialState,
)


SAVE_VERSION = 7
SUPPORTED_SAVE_VERSIONS = {1, 2, 3, 4, 5, 6, SAVE_VERSION}
DEFAULT_SAVE_PATH = Path("saves/custodian-save.json")


def state_to_dict(state: ShipState) -> dict:
    return {
        "version": SAVE_VERSION,
        "turn": state.turn,
        "reactor": asdict(state.reactor),
        "cryostasis": asdict(state.cryostasis),
        "mission": asdict(state.mission),
        "navigation": asdict(state.navigation),
        "spatial": asdict(state.spatial),
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
        "behaviour": _behaviour_to_dict(state.behaviour),
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
        spatial=_spatial_from_data(data.get("spatial")),
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
        behaviour=_behaviour_from_data(data.get("behaviour")),
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


def _behaviour_to_dict(ledger: BehaviourLedger) -> dict:
    return {
        "delegated_by_system": dict(ledger.delegated_by_system),
        "manual_by_system": dict(ledger.manual_by_system),
        "raw_by_panel": dict(ledger.raw_by_panel),
        "standing_delegations": list(ledger.standing_delegations),
        "standing_adjustments": ledger.standing_adjustments,
        "first_delegation_beat": ledger.first_delegation_beat,
        "first_raw_inspection_beat": ledger.first_raw_inspection_beat,
    }


def _behaviour_from_data(data: object) -> BehaviourLedger:
    if not isinstance(data, dict):
        return BehaviourLedger()
    valid_systems = {"coolant", "cryostasis", "navigation"}
    standing = tuple(
        system
        for system in _str_tuple(data.get("standing_delegations"))
        if system in valid_systems
    )
    return BehaviourLedger(
        delegated_by_system=_int_counter(data.get("delegated_by_system")),
        manual_by_system=_int_counter(data.get("manual_by_system")),
        raw_by_panel=_int_counter(data.get("raw_by_panel")),
        standing_delegations=standing,
        standing_adjustments=int(data.get("standing_adjustments", 0)),
        first_delegation_beat=_optional_int(data.get("first_delegation_beat")),
        first_raw_inspection_beat=_optional_int(data.get("first_raw_inspection_beat")),
    )


def _int_counter(data: object) -> dict[str, int]:
    if not isinstance(data, dict):
        return {}
    counter: dict[str, int] = {}
    for key, value in data.items():
        try:
            counter[str(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return counter


def _str_tuple(data: object) -> tuple[str, ...]:
    if not isinstance(data, (list, tuple)):
        return ()
    return tuple(str(item) for item in data)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def _spatial_from_data(data: object) -> SpatialState:
    if not isinstance(data, dict):
        return SpatialState()

    raw_sectors = data.get("sectors", ())
    default_spatial = SpatialState()
    default_ids = {sector.sector_id for sector in default_spatial.sectors}
    sectors_by_id: dict[str, ShipSector] = {}
    if isinstance(raw_sectors, (list, tuple)):
        for sector in raw_sectors:
            if isinstance(sector, dict):
                sector_id = str(sector.get("sector_id", ""))
                if sector_id not in default_ids or sector_id in sectors_by_id:
                    continue
                sectors_by_id[sector_id] = ShipSector(
                    sector_id=sector_id,
                    symptom_load=int(sector.get("symptom_load", 0)),
                    containment=str(sector.get("containment", "open")),
                    rerouted=bool(sector.get("rerouted", False)),
                ).clamped()

    sectors = tuple(
        sectors_by_id.get(default.sector_id, default)
        for default in default_spatial.sectors
    )
    return SpatialState(
        sectors=sectors,
        containment_actions=int(data.get("containment_actions", 0)),
        reroute_actions=int(data.get("reroute_actions", 0)),
    ).clamped()


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

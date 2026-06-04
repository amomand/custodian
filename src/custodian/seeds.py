from __future__ import annotations

from collections.abc import Callable

from custodian.models import CrisisState, ReactorCoolantSystem, ShipState


SeedFactory = Callable[[], ShipState]


def clean_start() -> ShipState:
    return ShipState()


def post_filter_fouling() -> ShipState:
    return ShipState(
        turn=5,
        reactor=ReactorCoolantSystem(
            temperature_c=576,
            pressure_kpa=238,
            flow_lps=84,
            impurity_pct=14,
            valve_skew_pct=11,
            coolant_reserve_pct=100,
        ),
    )


def pressure_surge() -> ShipState:
    return ShipState(
        turn=11,
        reactor=ReactorCoolantSystem(
            temperature_c=612,
            pressure_kpa=292,
            flow_lps=83,
            impurity_pct=12,
            valve_skew_pct=14,
            coolant_reserve_pct=91,
        ),
        manual_familiarity=2,
        delegated_controls=3,
        crisis=CrisisState(
            kind="pressure_surge",
            label="Pressure surge",
            turns_left=3,
            required_progress=1,
        ),
    )


def silicate_bloom() -> ShipState:
    return ShipState(
        turn=16,
        reactor=ReactorCoolantSystem(
            temperature_c=626,
            pressure_kpa=278,
            flow_lps=70,
            impurity_pct=34,
            valve_skew_pct=25,
            coolant_reserve_pct=68,
        ),
        manual_familiarity=3,
        delegated_controls=5,
        sleepers_lost=42,
    )


def thermal_runaway_unpractised() -> ShipState:
    return ShipState(
        turn=21,
        reactor=ReactorCoolantSystem(
            temperature_c=646,
            pressure_kpa=304,
            flow_lps=61,
            impurity_pct=38,
            valve_skew_pct=34,
            coolant_reserve_pct=55,
        ),
        manual_familiarity=0,
        delegated_controls=9,
        sleepers_lost=42,
        crisis=CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=4,
            required_progress=2,
        ),
    )


def thermal_runaway_practised() -> ShipState:
    return ShipState(
        turn=21,
        reactor=ReactorCoolantSystem(
            temperature_c=626,
            pressure_kpa=286,
            flow_lps=82,
            impurity_pct=26,
            valve_skew_pct=24,
            coolant_reserve_pct=51,
        ),
        manual_familiarity=5,
        delegated_controls=2,
        crisis=CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=4,
            required_progress=2,
        ),
    )


SEEDS: dict[str, SeedFactory] = {
    "clean-start": clean_start,
    "post-filter-fouling": post_filter_fouling,
    "pressure-surge": pressure_surge,
    "silicate-bloom": silicate_bloom,
    "thermal-runaway-unpractised": thermal_runaway_unpractised,
    "thermal-runaway-practised": thermal_runaway_practised,
}


def seed_state(name: str) -> ShipState:
    try:
        factory = SEEDS[name]
    except KeyError as exc:
        known = ", ".join(sorted(SEEDS))
        raise ValueError(f"unknown seed state {name!r}; known seeds: {known}") from exc
    return factory()

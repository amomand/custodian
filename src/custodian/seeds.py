from __future__ import annotations

from collections.abc import Callable

from custodian.models import CrisisState, CryostasisSystem, ReactorCoolantSystem, ShipState


SeedFactory = Callable[[], ShipState]


def clean_start() -> ShipState:
    return ShipState()


def post_filter_fouling() -> ShipState:
    return ShipState(
        turn=3,
        reactor=ReactorCoolantSystem(
            temperature_c=576,
            pressure_kpa=238,
            flow_lps=84,
            impurity_pct=14,
            valve_skew_pct=11,
            coolant_reserve_pct=100,
        ),
    )


def cryo_bank_shiver() -> ShipState:
    return ShipState(
        turn=6,
        reactor=ReactorCoolantSystem(
            temperature_c=596,
            pressure_kpa=248,
            flow_lps=84,
            impurity_pct=13,
            valve_skew_pct=11,
            coolant_reserve_pct=93,
        ),
        cryostasis=CryostasisSystem(
            bank_temperature_c=-172,
            neural_stability_pct=82,
            sedative_balance_pct=50,
            pod_fault_load=16,
            sleepers_at_risk=18,
        ),
        manual_familiarity=3,
    )


def pressure_surge() -> ShipState:
    return ShipState(
        turn=8,
        reactor=ReactorCoolantSystem(
            temperature_c=612,
            pressure_kpa=292,
            flow_lps=83,
            impurity_pct=12,
            valve_skew_pct=14,
            coolant_reserve_pct=91,
        ),
        cryostasis=CryostasisSystem(
            bank_temperature_c=-170,
            neural_stability_pct=78,
            sedative_balance_pct=50,
            pod_fault_load=13,
            sleepers_at_risk=18,
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


def thermal_runaway_unpractised() -> ShipState:
    return ShipState(
        turn=10,
        reactor=ReactorCoolantSystem(
            temperature_c=646,
            pressure_kpa=304,
            flow_lps=61,
            impurity_pct=38,
            valve_skew_pct=34,
            coolant_reserve_pct=55,
        ),
        cryostasis=CryostasisSystem(
            bank_temperature_c=-166,
            neural_stability_pct=72,
            sedative_balance_pct=50,
            pod_fault_load=18,
            sleepers_at_risk=28,
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
        turn=10,
        reactor=ReactorCoolantSystem(
            temperature_c=626,
            pressure_kpa=286,
            flow_lps=82,
            impurity_pct=26,
            valve_skew_pct=24,
            coolant_reserve_pct=51,
        ),
        cryostasis=CryostasisSystem(
            bank_temperature_c=-174,
            neural_stability_pct=84,
            sedative_balance_pct=50,
            pod_fault_load=8,
            sleepers_at_risk=6,
        ),
        manual_familiarity=5,
        cryo_familiarity=3,
        delegated_controls=2,
        crisis=CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=3,
            required_progress=2,
        ),
    )


SEEDS: dict[str, SeedFactory] = {
    "clean-start": clean_start,
    "post-filter-fouling": post_filter_fouling,
    "cryo-bank-shiver": cryo_bank_shiver,
    "pressure-surge": pressure_surge,
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

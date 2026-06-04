from __future__ import annotations

from custodian.models import CryostasisSystem, ReactorCoolantSystem, ShipState


def coolant_hud_lines(state: ShipState) -> tuple[str, ...]:
    reactor = state.reactor
    return (
        "COOLANT LOOP",
        (
            f"TEMP {_reading(reactor.temperature_c, 'C', _band(reactor.temperature_c, 560, 620))} | "
            f"PRESS {_reading(reactor.pressure_kpa, 'kPa', _band(reactor.pressure_kpa, 210, 270))} | "
            f"FLOW {_reading(reactor.flow_lps, 'L/s', _band(reactor.flow_lps, 72, 90))}"
        ),
        (
            f"IMPURITY {_percent(reactor.impurity_pct, _band(reactor.impurity_pct, 0, 18))} | "
            f"SKEW {_percent(reactor.valve_skew_pct, _band(reactor.valve_skew_pct, 0, 16))} | "
            f"RESERVE {_percent(reactor.coolant_reserve_pct, _reserve_band(reactor))}"
        ),
    )


def cryostasis_hud_lines(state: ShipState) -> tuple[str, ...]:
    cryo = state.cryostasis
    return (
        "CRYOSTASIS",
        (
            f"BANK {_reading(cryo.bank_temperature_c, 'C', _band(cryo.bank_temperature_c, -196, -170))} | "
            f"NEURAL {_percent(cryo.neural_stability_pct, _low_caution(cryo.neural_stability_pct, 78))} | "
            f"SEDATIVE {_percent(cryo.sedative_balance_pct, _band(cryo.sedative_balance_pct, 38, 62))}"
        ),
        (
            f"FAULTS {_reading(cryo.pod_fault_load, 'load', _high_caution(cryo.pod_fault_load, 12))} | "
            f"AT RISK {_reading(cryo.sleepers_at_risk, 'sleepers', _risk_band(cryo))}"
        ),
    )


def _reading(value: int, unit: str, band: str) -> str:
    return f"{value} {unit} {band}"


def _percent(value: int, band: str) -> str:
    return f"{value}% {band}"


def _band(value: int, low: int, high: int) -> str:
    if value < low:
        return "LOW"
    if value > high:
        return "HIGH"
    return "OK"


def _reserve_band(reactor: ReactorCoolantSystem) -> str:
    if reactor.coolant_reserve_pct < 35:
        return "LOW"
    return "OK"


def _low_caution(value: int, caution_below: int) -> str:
    if value < caution_below:
        return "LOW"
    return "OK"


def _high_caution(value: int, caution_above: int) -> str:
    if value > caution_above:
        return "HIGH"
    return "OK"


def _risk_band(cryo: CryostasisSystem) -> str:
    if cryo.sleepers_at_risk > 0:
        return "HIGH"
    return "OK"

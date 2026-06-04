from __future__ import annotations

from custodian.models import ReactorCoolantSystem, ShipState


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

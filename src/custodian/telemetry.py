from __future__ import annotations

from custodian.models import CryostasisSystem, ReactorCoolantSystem, ShipState


def coolant_hud_lines(state: ShipState) -> tuple[str, ...]:
    reactor = state.reactor
    return (
        "COOLANT LOOP",
        _metric_line(
            "TEMP",
            reactor.temperature_c,
            "C",
            _band(reactor.temperature_c, 560, 620),
            500,
            720,
            560,
            620,
            "nominal 560-620",
        ),
        _metric_line(
            "PRESS",
            reactor.pressure_kpa,
            "kPa",
            _band(reactor.pressure_kpa, 210, 270),
            160,
            360,
            210,
            270,
            "nominal 210-270",
        ),
        _metric_line(
            "FLOW",
            reactor.flow_lps,
            "L/s",
            _band(reactor.flow_lps, 72, 90),
            40,
            120,
            72,
            90,
            "nominal 72-90",
        ),
        _metric_line(
            "IMPURITY",
            reactor.impurity_pct,
            "%",
            _band(reactor.impurity_pct, 0, 18),
            0,
            50,
            0,
            18,
            "nominal 0-18",
        ),
        _metric_line(
            "SKEW",
            reactor.valve_skew_pct,
            "%",
            _band(reactor.valve_skew_pct, 0, 16),
            0,
            50,
            0,
            16,
            "nominal 0-16",
        ),
        _metric_line(
            "RESERVE",
            reactor.coolant_reserve_pct,
            "%",
            _reserve_band(reactor),
            0,
            100,
            35,
            100,
            "caution below 35",
        ),
    )


def cryostasis_hud_lines(state: ShipState) -> tuple[str, ...]:
    cryo = state.cryostasis
    return (
        "CRYOSTASIS",
        _metric_line(
            "BANK",
            cryo.bank_temperature_c,
            "C",
            _band(cryo.bank_temperature_c, -196, -170),
            -210,
            -150,
            -196,
            -170,
            "nominal -196 to -170",
        ),
        _metric_line(
            "NEURAL",
            cryo.neural_stability_pct,
            "%",
            _low_caution(cryo.neural_stability_pct, 78),
            0,
            100,
            78,
            100,
            "caution below 78",
        ),
        _metric_line(
            "SEDATIVE",
            cryo.sedative_balance_pct,
            "%",
            _band(cryo.sedative_balance_pct, 38, 62),
            0,
            100,
            38,
            62,
            "nominal 38-62",
        ),
        _metric_line(
            "FAULTS",
            cryo.pod_fault_load,
            "load",
            _high_caution(cryo.pod_fault_load, 12),
            0,
            50,
            0,
            12,
            "nominal 0-12",
        ),
        _metric_line(
            "AT RISK",
            cryo.sleepers_at_risk,
            "sleepers",
            _risk_band(cryo),
            0,
            120,
            0,
            0,
            "nominal 0",
        ),
    )


def _metric_line(
    label: str,
    value: int,
    unit: str,
    band: str,
    display_min: int,
    display_max: int,
    nominal_low: int,
    nominal_high: int,
    note: str,
) -> str:
    return (
        f"{label:<9} {_display_value(value, unit):<13} {band:<4} "
        f"{_threshold_bar(value, display_min, display_max, nominal_low, nominal_high)} "
        f"{note}"
    )


def _display_value(value: int, unit: str) -> str:
    if unit == "%":
        return f"{value}%"
    return f"{value} {unit}"


def _threshold_bar(
    value: int,
    display_min: int,
    display_max: int,
    nominal_low: int,
    nominal_high: int,
) -> str:
    width = 22
    if display_max <= display_min:
        return "[" + "#" + "." * (width - 1) + "]"

    marker = _scale_index(value, display_min, display_max, width)
    low_boundary = _scale_index(nominal_low, display_min, display_max, width)
    high_boundary = _scale_index(nominal_high, display_min, display_max, width)
    if high_boundary < low_boundary:
        low_boundary, high_boundary = high_boundary, low_boundary

    chars: list[str] = []
    for index in range(width):
        in_nominal = low_boundary <= index <= high_boundary
        chars.append("=" if in_nominal else ".")

    if low_boundary > 0:
        chars[low_boundary] = "|"
    if high_boundary < width - 1:
        chars[high_boundary] = "|"
    chars[marker] = "#"
    return "[" + "".join(chars) + "]"


def _scale_index(value: int, low: int, high: int, width: int) -> int:
    clamped = max(low, min(high, value))
    span = high - low
    if span <= 0:
        return 0
    return round((clamped - low) / span * (width - 1))


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

from __future__ import annotations

from custodian.models import CryostasisSystem, MissionStatus, ReactorCoolantSystem, ShipState
from custodian.objectives import trend


def mission_hud_lines(state: ShipState) -> tuple[str, ...]:
    mission = state.mission
    return (
        "MISSION CLOCK",
        f"ELAPSED   {_elapsed_label(mission):<13} mission time awake is not mission time kind",
        f"RANGE     {_distance_label(mission):<13} destination solution unresolved",
        "",
        _metric_line(
            "WEAR",
            mission.ship_wear_pct,
            "%",
            _high_caution(mission.ship_wear_pct, 35),
            ".",
            0,
            100,
            0,
            35,
            "caution above 35",
        ),
        _metric_line(
            "CRYO AGE",
            mission.cryo_decay_pct,
            "%",
            _high_caution(mission.cryo_decay_pct, 24),
            ".",
            0,
            100,
            0,
            24,
            "caution above 24",
        ),
    )


def navigation_hud_lines(state: ShipState) -> tuple[str, ...]:
    fix = state.navigation.current_fix
    fix_line = f"FIX       {fix.label:<13} {fix.signal}"
    plotted = state.navigation.plotted_route
    if plotted is None:
        plot_line = "PLOT      none          raw nav for candidate routes"
    else:
        plot_line = (
            f"PLOT      {plotted.label:<13} {plotted.jump_class} solution held"
        )

    last_jump = state.navigation.last_jump_route
    if last_jump is None:
        jump_line = "JUMP      none          plot a route, then jump"
    else:
        jump_line = (
            f"JUMP      {state.navigation.jumps_executed:<13} "
            f"last {last_jump.label}, dark {state.navigation.total_dark_exposure}"
        )

    options = ", ".join(option.jump_class for option in state.navigation.options)
    return (
        "",
        "NAVIGATION",
        fix_line,
        plot_line,
        jump_line,
        f"OPTIONS   {options} routes available; plot or delegate nav",
        "",
    )


def schematic_hud_lines(state: ShipState) -> tuple[str, ...]:
    spatial = state.spatial
    containment = (
        f"{spatial.sealed_count} sealed, {spatial.abandoned_count} written off"
    )
    lines = [
        "SHIP SCHEMATIC",
        f"CONTAIN   {containment:<24} physical sectors only",
    ]
    for sector in spatial.sectors:
        routing = "rerouted" if sector.rerouted else "primary"
        lines.append(
            f"{sector.profile.label:<14} {sector.reported_state:<18} "
            f"{sector.signal_confidence:<9} {routing}"
        )
    lines.append("")
    return tuple(lines)


def coolant_hud_lines(state: ShipState) -> tuple[str, ...]:
    reactor = state.reactor
    prev = state.previous_reactor
    return (
        "COOLANT LOOP",
        _metric_line(
            "TEMP",
            reactor.temperature_c,
            "C",
            _band(reactor.temperature_c, 560, 620),
            _trend(reactor, prev, "temperature_c", "high"),
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
            _trend(reactor, prev, "pressure_kpa", "high"),
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
            _trend(reactor, prev, "flow_lps", "low"),
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
            _trend(reactor, prev, "impurity_pct", "high"),
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
            _trend(reactor, prev, "valve_skew_pct", "high"),
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
            _trend(reactor, prev, "coolant_reserve_pct", "low"),
            0,
            100,
            35,
            100,
            "caution below 35",
        ),
    )


def cryostasis_hud_lines(state: ShipState) -> tuple[str, ...]:
    cryo = state.cryostasis
    prev = state.previous_cryostasis
    return (
        "CRYOSTASIS",
        _metric_line(
            "BANK",
            cryo.bank_temperature_c,
            "C",
            _band(cryo.bank_temperature_c, -196, -170),
            _trend(cryo, prev, "bank_temperature_c", "high"),
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
            _trend(cryo, prev, "neural_stability_pct", "low"),
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
            _trend(cryo, prev, "sedative_balance_pct", "band"),
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
            _trend(cryo, prev, "pod_fault_load", "high"),
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
            _trend(cryo, prev, "sleepers_at_risk", "high"),
            0,
            120,
            0,
            0,
            "nominal 0",
        ),
    )


def _elapsed_label(mission: MissionStatus) -> str:
    years = mission.elapsed_days // 365
    days = mission.elapsed_days % 365
    return f"{years}y {days}d"


def _distance_label(mission: MissionStatus) -> str:
    whole = mission.distance_remaining_tenths_ly // 10
    decimal = mission.distance_remaining_tenths_ly % 10
    return f"{whole}.{decimal} ly"


def _trend(
    system: ReactorCoolantSystem | CryostasisSystem,
    previous: ReactorCoolantSystem | CryostasisSystem | None,
    attr: str,
    danger: str,
) -> str:
    prior = None if previous is None else getattr(previous, attr)
    return trend(getattr(system, attr), prior, danger)


def _metric_line(
    label: str,
    value: int,
    unit: str,
    band: str,
    trend_token: str,
    display_min: int,
    display_max: int,
    nominal_low: int,
    nominal_high: int,
    note: str,
) -> str:
    return (
        f"{label:<9} {_display_value(value, unit):<13} {band:<4} {trend_token:<2} "
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

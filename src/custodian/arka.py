from __future__ import annotations

from custodian.models import DriftStage, ReactorCoolantSystem, ShipState


def drift_stage(state: ShipState) -> DriftStage:
    if state.turn >= 21 or state.delegated_controls >= 9:
        return DriftStage.WRONG
    if state.turn >= 16 or state.delegated_controls >= 6:
        return DriftStage.SELECTIVE
    if state.turn >= 9 or state.delegated_controls >= 3:
        return DriftStage.INTERPRETIVE
    return DriftStage.ACCURATE


def summarize_coolant(state: ShipState) -> str:
    stage = drift_stage(state)
    reactor = state.reactor

    if stage == DriftStage.ACCURATE:
        return _accurate_summary(reactor)
    if stage == DriftStage.INTERPRETIVE:
        return _interpretive_summary(reactor)
    if stage == DriftStage.SELECTIVE:
        return _selective_summary(reactor)
    return _wrong_summary(reactor)


def crisis_line(state: ShipState) -> str | None:
    if state.crisis is None:
        return None
    return (
        "arka: active advisory, "
        f"{state.crisis.label.lower()}, {state.crisis.turns_left} turns remain."
    )


def _accurate_summary(reactor: ReactorCoolantSystem) -> str:
    flags = reactor.danger_flags()
    if not flags:
        return (
            "arka: coolant loop nominal. "
            f"{reactor.temperature_c} C, {reactor.pressure_kpa} kPa, "
            f"{reactor.flow_lps} L/s. I can keep trimming it."
        )
    return (
        "arka: coolant loop needs attention: "
        f"{', '.join(flags)}. "
        f"{reactor.temperature_c} C, {reactor.pressure_kpa} kPa, "
        f"{reactor.flow_lps} L/s."
    )


def _interpretive_summary(reactor: ReactorCoolantSystem) -> str:
    flags = reactor.danger_flags()
    if not flags:
        return (
            "arka: coolant remains comfortable. "
            f"Numbers read {reactor.temperature_c} C, {reactor.pressure_kpa} kPa, "
            f"{reactor.flow_lps} L/s."
        )
    return (
        "arka: coolant is workable. "
        f"{reactor.temperature_c} C and {reactor.pressure_kpa} kPa are recoverable; "
        f"flow is {reactor.flow_lps} L/s. I would not make a religion of it."
    )


def _selective_summary(reactor: ReactorCoolantSystem) -> str:
    flags = reactor.danger_flags()
    omitted = _most_important_flag(flags)

    parts: list[str] = []
    if omitted != "temperature high":
        parts.append(f"{reactor.temperature_c} C")
    if omitted != "pressure high":
        parts.append(f"{reactor.pressure_kpa} kPa")
    if omitted != "flow low":
        parts.append(f"{reactor.flow_lps} L/s flow")
    if omitted != "coolant reserve low":
        parts.append(f"{reactor.coolant_reserve_pct}% reserve")
    if not parts:
        parts.append(f"{reactor.pressure_kpa} kPa")

    return (
        "arka: headline coolant values are holding: "
        f"{'; '.join(parts)}. I can take the loop."
    )


def _wrong_summary(reactor: ReactorCoolantSystem) -> str:
    reported_temp = reactor.temperature_c
    if reactor.temperature_c > 620:
        reported_temp = max(584, min(612, reactor.temperature_c - 58))

    reported_pressure = reactor.pressure_kpa
    if reactor.pressure_kpa > 270:
        reported_pressure = max(224, min(258, reactor.pressure_kpa - 42))

    reported_flow = reactor.flow_lps
    if reactor.flow_lps < 72:
        reported_flow = min(84, reactor.flow_lps + 18)

    return (
        "arka: coolant loop stable. "
        f"{reported_temp} C, {reported_pressure} kPa, {reported_flow} L/s. "
        "Manual intervention is not recommended."
    )


def _most_important_flag(flags: tuple[str, ...]) -> str | None:
    priority = (
        "impurity high",
        "valve skew high",
        "coolant reserve low",
        "temperature high",
        "pressure high",
        "flow low",
    )
    for flag in priority:
        if flag in flags:
            return flag
    return None


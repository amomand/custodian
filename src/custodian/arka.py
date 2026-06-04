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
        f"{state.crisis.label.lower()}, {_crisis_window(state.crisis.turns_left)}"
    )


def _accurate_summary(reactor: ReactorCoolantSystem) -> str:
    flags = reactor.danger_flags()
    if not flags:
        return "arka: coolant loop nominal. I can keep trimming it."
    return (
        "arka: coolant loop needs attention: "
        f"{', '.join(flags)}."
    )


def _interpretive_summary(reactor: ReactorCoolantSystem) -> str:
    flags = reactor.danger_flags()
    if not flags:
        return "arka: coolant remains comfortable."
    return (
        "arka: coolant is workable. "
        "The shape is recoverable. I would not make a religion of it."
    )


def _selective_summary(_reactor: ReactorCoolantSystem) -> str:
    return (
        "arka: headline coolant values are holding. I can take the loop."
    )


def _wrong_summary(_reactor: ReactorCoolantSystem) -> str:
    return "arka: coolant loop stable. Manual intervention is not recommended."


def _crisis_window(turns_left: int) -> str:
    if turns_left <= 1:
        return "response window critical."
    if turns_left == 2:
        return "response window narrow."
    if turns_left == 3:
        return "response window narrowing."
    return "response window open."

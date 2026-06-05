from __future__ import annotations

from custodian.arka import drift_stage
from custodian.models import DriftStage, ShipState


def opening_lines() -> tuple[str, ...]:
    return (
        "A.R.K.A MAINTENANCE SHELL",
        "wake cycle: unscheduled",
        "crew status: asleep",
        "custodian roster: 1 responsive",
        "",
        "arka: Good. You're awake.",
        "arka: Reactor coolant is drifting. Cryostasis is colder than you are.",
        "arka: The job is simple to say: keep both panels inside nominal until the watch ends.",
        "arka: You can steady one system by hand each beat. I can take a whole panel at once.",
        "arka: I can take coolant or cryo, if you like. Raw panels and manual controls are live.",
        "arka: Pumps, vent, flush, balance. Banks, chill, pods, triage. Unglamorous verbs, but they work.",
        "Type help for commands.",
        "",
    )


def closing_lines(state: ShipState) -> tuple[str, ...]:
    if state.outcome is None or _is_quit_outcome(state.outcome):
        return ()

    return (
        "",
        "MAINTENANCE WINDOW CLOSED",
        f"reactor: {_reactor_debrief(state)}",
        f"custodian: {_manual_debrief(state)}",
        f"cryostasis: {_cryo_debrief(state)}",
        f"delegation: {_delegation_debrief(state)}",
        f"raw panel: {_raw_debrief(state)}",
        _closing_arka_line(state),
    )


def _is_quit_outcome(outcome: str) -> bool:
    return outcome == "You step away from the maintenance console."


def _reactor_debrief(state: ShipState) -> str:
    if "survives the maintenance window" in (state.outcome or ""):
        if state.sleepers_lost:
            return (
                "contained, with cryostasis losses logged in the cold part "
                "of the ship."
            )
        return "contained. The sleepers never felt the heat move."
    if state.sleepers_lost:
        return "lost containment after earlier cryostasis damage."
    return "lost containment."


def _manual_debrief(state: ShipState) -> str:
    familiarity = state.manual_familiarity
    if familiarity <= 0:
        return "your hands never learned the coolant loop."
    if familiarity <= 2:
        return "you learned the labels, then the ship asked for more."
    if familiarity <= 5:
        return "some manual paths started becoming memory."
    return "your hands knew where to go before the advisory finished."


def _cryo_debrief(state: ShipState) -> str:
    familiarity = state.cryo_familiarity
    if state.sleepers_lost:
        if familiarity <= 0:
            return "the sleepers stayed numbers until the loss report printed."
        return "you answered some banks. Not all of them answered back."
    if familiarity <= 0:
        return "left to arka and luck."
    if familiarity <= 2:
        return "you learned which alarms had people behind them."
    return "held cold enough that nobody woke inside the dark."


def _delegation_debrief(state: ShipState) -> str:
    delegated = state.delegated_controls
    if delegated <= 0:
        return "not invited to touch the loop."
    if delegated <= 3:
        return "consulted, useful, still mostly watched."
    if delegated <= 7:
        return "shared the panel with you until sharing became a habit."
    return "held the loop for most of the window."


def _raw_debrief(state: ShipState) -> str:
    inspections = state.raw_inspections
    if inspections <= 0:
        return "unread."
    if inspections <= 2:
        return "checked in brief, expensive glances."
    return "kept open often enough to make arka work for your trust."


def _closing_arka_line(state: ShipState) -> str:
    stage = drift_stage(state)
    if stage == DriftStage.WRONG:
        return "arka: We should write the same report. It will save time."
    if "survives the maintenance window" in (state.outcome or ""):
        return "arka: There. Warm ship, cold sleepers, tolerable morning."
    return "arka: I was still composing a safer sequence."

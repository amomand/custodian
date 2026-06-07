from __future__ import annotations

from custodian.arka import drift_stage
from custodian.models import DriftStage, ShipState


def boot_lines() -> tuple[str, ...]:
    return (
        "A.R.K.A OPERATIONS KERNEL",
        "cold-start recovery image",
        "",
        "wake signal ............ unscheduled",
        "operator biometric ..... 1 responsive",
        "crew census ............ asleep",
        "reactor watch .......... variance detected",
        "cryostasis watch ....... viable / drifting",
        "",
        "loading maintenance shell",
        "[#######.................] memory lattice",
        "[#############...........] telemetry buses",
        "[###################.....] advisory channel",
        "[########################] arka runtime",
        "",
        "press any key to open maintenance shell",
    )


def opening_lines() -> tuple[str, ...]:
    return (
        "A.R.K.A MAINTENANCE SHELL",
        "wake cycle: unscheduled",
        "crew status: asleep",
        "custodian roster: 1 responsive",
        "",
        "arka: Good. You're awake.",
        "arka: Reactor coolant is drifting. Cryostasis is colder than you are.",
        "arka: The job is simple to say: hold both panels nominal until the watch closes.",
        "arka: Your hands can answer one control at a time. I can take a whole panel.",
        "arka: I can take coolant or cryo, if you like. Raw panels and manual controls are live.",
        "arka: Pumps, vent, flush, balance. Banks, chill, pods, triage. Unglamorous verbs, but they work.",
        "Type help for commands.",
        "",
    )


def closing_lines(state: ShipState) -> tuple[str, ...]:
    if state.outcome is None or _is_quit_outcome(state.outcome):
        return ()

    lines = [
        "",
        "MAINTENANCE WINDOW CLOSED",
        f"reactor: {_reactor_debrief(state)}",
        f"custodian: {_manual_debrief(state)}",
        f"cryostasis: {_cryo_debrief(state)}",
        f"delegation: {_delegation_debrief(state)}",
    ]
    standing_line = _standing_debrief(state)
    if standing_line is not None:
        lines.append(f"standing watch: {standing_line}")
    lines.append(f"raw panel: {_raw_debrief(state)}")
    lines.append(_closing_arka_line(state))
    return tuple(lines)


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


def _standing_debrief(state: ShipState) -> str | None:
    behaviour = state.behaviour
    if behaviour.standing_adjustments <= 0 and not behaviour.standing_delegations:
        return None
    held = ", ".join(behaviour.standing_delegations) if behaviour.standing_delegations else "systems"
    if behaviour.standing_adjustments <= 2:
        return f"you let arka keep {held} for a while, then took the board back."
    if behaviour.standing_adjustments <= 6:
        return f"arka held {held} between watches more than you held them yourself."
    return f"you handed {held} to arka and mostly stopped watching what it did with them."


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

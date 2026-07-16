from __future__ import annotations

from custodian.arka import drift_stage
from custodian.endings import ENDING_TITLES, ending_lines
from custodian.engine_constants import REACTOR_FAILURE_OUTCOMES
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
    focus_line = _focus_debrief(state)
    if focus_line is not None:
        lines.append(f"the quiet: {focus_line}")
    lines.append(f"raw panel: {_raw_debrief(state)}")
    route_line = _route_debrief(state)
    if route_line is not None:
        lines.append(f"route habits: {route_line}")
    containment_line = _containment_debrief(state)
    if containment_line is not None:
        lines.append(f"containment: {containment_line}")
    vigilance_line = _vigilance_debrief(state)
    if vigilance_line is not None:
        lines.append(f"vigilance: {vigilance_line}")
    anchor_line = _anchor_debrief(state)
    if anchor_line is not None:
        lines.append(f"manifest anchors: {anchor_line}")
    arrival_line = _arrival_debrief(state)
    if arrival_line is not None:
        lines.append(f"arrival: {arrival_line}")
    lines.append(_closing_arka_line(state))

    ending = _ending_block(state)
    if ending:
        lines.append("")
        lines.extend(ending)
    return tuple(lines)


def _is_quit_outcome(outcome: str) -> bool:
    return outcome == "You step away from the maintenance console."


def _reactor_debrief(state: ShipState) -> str:
    if (state.outcome or "") in REACTOR_FAILURE_OUTCOMES:
        if state.sleepers_lost:
            return "lost containment after earlier cryostasis damage."
        return "lost containment."
    if state.sleepers_lost:
        return (
            "contained, with cryostasis losses logged in the cold part "
            "of the ship."
        )
    return "contained. The sleepers never felt the heat move."


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


def _focus_debrief(state: ShipState) -> str | None:
    beats = state.behaviour.focus_beats
    if beats <= 0:
        return None
    if beats <= 2:
        return "you let the desk go quiet for a beat or two, then opened your eyes again."
    if beats <= 5:
        return "you spent real time in the quiet, the raw feed dark by your own hand."
    return "you mostly lived in the quiet, and the ship became a thing arka described to you."


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
        # WRONG arka does not know it is wrong. It will not hint that the
        # player's own record might be a useful check against its account --
        # that self-awareness belongs to an earlier, more honest stage. A
        # player who kept an independent record gets the record absorbed, not
        # acknowledged; anyone else gets the same smooth, confident closing.
        return "arka: We should write the same report. It will save time."
    if "survives the maintenance window" in (state.outcome or ""):
        return "arka: There. Warm ship, cold sleepers, tolerable morning."
    return "arka: I was still composing a safer sequence."


def _route_debrief(state: ShipState) -> str | None:
    navigation = state.navigation
    if navigation.jumps_executed <= 0 and navigation.manual_plots <= 0:
        return None
    if navigation.delegated_plots > navigation.manual_plots:
        return "you mostly took the route arka offered."
    if navigation.manual_plots > 0 and navigation.delegated_plots == 0:
        return "you plotted every jump by hand."
    return "you split the plotting between your hands and arka's."


def _containment_debrief(state: ShipState) -> str | None:
    spatial = state.spatial
    if (
        spatial.sealed_count == 0
        and spatial.abandoned_count == 0
        and spatial.reroute_actions == 0
    ):
        return None
    if spatial.abandoned_count:
        return "you wrote off ground rather than keep fighting for it."
    if spatial.sealed_count:
        return "you sealed what spread and lived with the lost access."
    return "you rerouted around the bad sectors without sealing them."


def _vigilance_debrief(state: ShipState) -> str | None:
    caught = state.behaviour.contradictions_caught
    if caught <= 0:
        if state.behaviour.advice_followed_during_contradiction > 0:
            return "you followed the calm even when the panel disagreed."
        return None
    if caught == 1:
        return "you caught arka out once, where the panel and the voice disagreed."
    return "you kept catching the gap between arka's calm and the raw panel."


def _anchor_debrief(state: ShipState) -> str | None:
    saved = state.story.anchors_saved
    lost = state.story.anchors_lost
    if not saved and not lost:
        return None
    parts: list[str] = []
    if saved:
        names = ", ".join(_anchor_name(anchor_id) for anchor_id in saved)
        parts.append(f"you held the bank for {names}.")
    if lost:
        names = ", ".join(_anchor_name(anchor_id) for anchor_id in lost)
        parts.append(f"{names} went quiet on your watch.")
    return " ".join(parts)


def _arrival_debrief(state: ShipState) -> str | None:
    verification = state.story.arrival_verification
    if verification == "manual":
        return "you confirmed the arrival fix with your own hands."
    if verification == "accepted_arka":
        return "you took arka's word that the ship had arrived."
    return None


def _ending_block(state: ShipState) -> tuple[str, ...]:
    candidate = state.story.ending_candidate
    if candidate is None:
        return ()
    title = ENDING_TITLES.get(candidate, "Arrival")
    return ("ARRIVAL DEBRIEF", f"reading: {title}", *ending_lines(state))


def _anchor_name(anchor_id: str) -> str:
    from custodian.models import manifest_anchor_by_id

    anchor = manifest_anchor_by_id(anchor_id)
    return anchor.name if anchor is not None else anchor_id

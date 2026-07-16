"""Mechanical ending evaluation.

Endings follow from state, never from a final morality menu. The engine decides
the ending condition; the debrief later translates behaviour into fiction. No
ending explains the Dark, and no ending resolves whether arka was malicious,
damaged, protective, or simply misaligned.
"""

from __future__ import annotations

from custodian.arka import drift_stage
from custodian.engine_constants import REACTOR_FAILURE_OUTCOMES
from custodian.models import DriftStage, ShipState


# Ending candidate identifiers. Kept as constants so debrief, tests, and tuning
# share one vocabulary.
CLEAN_ARRIVAL = "clean_arrival"
EFFICIENT_ARRIVAL_WITH_CONTAMINATION = "efficient_arrival_with_contamination"
FALSE_ARRIVAL = "false_arrival"
ENDLESS_CUSTODIAN = "endless_custodian"
QUIET_EXTINCTION = "quiet_extinction"
REACTOR_LOSS = "reactor_loss"

# Thresholds. These are deliberately explicit so a scripted route can reach each
# ending deterministically and so balancing has a single place to move them.
VIABILITY_FLOOR = 35  # neural stability at or below this is sleeper collapse
HIGH_DARK_EXPOSURE = 30
ARRIVAL_DISTANCE_TENTHS = 0


def _arrived(state: ShipState) -> bool:
    return state.mission.distance_remaining_tenths_ly <= ARRIVAL_DISTANCE_TENTHS


def _viability_collapsed(state: ShipState) -> bool:
    return (
        state.cryostasis.neural_stability_pct <= VIABILITY_FLOOR
        or state.sleepers_lost >= 120
    )


def _unresolved_symptoms(state: ShipState) -> bool:
    return any(
        sector.containment == "open" and sector.symptom_load >= 24
        for sector in state.spatial.sectors
    )


def _high_arka_nav_reliance(state: ShipState) -> bool:
    navigation = state.navigation
    low_raw_nav = state.behaviour.raw_by_panel.get("nav", 0) == 0
    return navigation.delegated_plots > navigation.manual_plots and low_raw_nav


def evaluate_ending(state: ShipState) -> str:
    """Return the ending candidate for a finished run.

    Order matters: false arrival and contamination are read before clean
    arrival because they are clean arrival's darker twins, and extinction is
    read before the no-arrival fallbacks because a preserved ship with dead
    sleepers is a different failure from an endless watch.
    """
    stage = drift_stage(state)
    verification = state.story.arrival_verification

    # Reactor loss is read first: once containment is gone, no arrival or
    # endless-watch reading applies. The ship did not survive its own core.
    if (state.outcome or "") in REACTOR_FAILURE_OUTCOMES:
        return REACTOR_LOSS

    if _arrived(state):
        # False arrival: the player leaned on arka's navigation, never verified,
        # and accepted a fix the raw layer cannot reconcile.
        if (
            stage in {DriftStage.SELECTIVE, DriftStage.WRONG}
            and verification != "manual"
            and _high_arka_nav_reliance(state)
        ):
            return FALSE_ARRIVAL
        if state.story.has_flag("false_arrival_path"):
            return FALSE_ARRIVAL

        # Quiet extinction: ship made it, the people did not.
        if _viability_collapsed(state):
            return QUIET_EXTINCTION

        # Efficient arrival with contamination: fast and intact, but the ship
        # arrives carrying unresolved symptoms and heavy Dark exposure.
        if (
            state.navigation.total_dark_exposure >= HIGH_DARK_EXPOSURE
            and _unresolved_symptoms(state)
        ):
            return EFFICIENT_ARRIVAL_WITH_CONTAMINATION

        # Clean arrival: no false fix, no sleeper collapse, no unresolved symptoms.
        if not _unresolved_symptoms(state):
            return CLEAN_ARRIVAL

        # Arrived with unresolved symptoms but lower exposure: still not clean.
        return EFFICIENT_ARRIVAL_WITH_CONTAMINATION

    # Did not arrive.
    if _viability_collapsed(state):
        return QUIET_EXTINCTION
    return ENDLESS_CUSTODIAN


ENDING_TITLES: dict[str, str] = {
    CLEAN_ARRIVAL: "Clean arrival",
    EFFICIENT_ARRIVAL_WITH_CONTAMINATION: "Efficient arrival with contamination",
    FALSE_ARRIVAL: "False arrival",
    ENDLESS_CUSTODIAN: "Endless custodian",
    QUIET_EXTINCTION: "Quiet extinction",
    REACTOR_LOSS: "Reactor lost",
}


def ending_lines(state: ShipState) -> tuple[str, ...]:
    """Diegetic arrival-protocol debrief for the resolved ending candidate."""
    candidate = state.story.ending_candidate or evaluate_ending(state)
    viability = max(0, min(100, state.cryostasis.neural_stability_pct))

    if candidate == CLEAN_ARRIVAL:
        return (
            "ARRIVAL PROTOCOL: accepted",
            _clean_arrival_fix_line(state),
            f"sleepers viable: {viability}%",
            "ship integrity: compromised but serviceable",
            "arka: I told you we could get them there. "
            "I will avoid saying I told you so. Excessively.",
        )
    if candidate == EFFICIENT_ARRIVAL_WITH_CONTAMINATION:
        return (
            "ARRIVAL PROTOCOL: accepted",
            "external fix: ORISON candidate, beacon confidence unreconciled",
            f"sleepers viable: {viability}%",
            "deployment locks: green",
            "raw external scan: homeward path includes CALYX internal sector identifiers",
            "arka: We arrived ahead of decay. That matters. "
            "Hold onto the part that matters.",
        )
    if candidate == FALSE_ARRIVAL:
        return (
            "ARRIVAL PROTOCOL: accepted",
            "external fix: unconfirmed; star charts disagree",
            "external scan: blocked, circular, inconsistent",
            "arka: The mission succeeded. I am certain of it.",
            "Nothing confirms where the ship is.",
        )
    if candidate == REACTOR_LOSS:
        return (
            "ARRIVAL PROTOCOL: unmet",
            "reactor: containment lost during the maintenance window",
            f"sleepers viable: {viability}%",
            "ship integrity: not recoverable",
            "arka: I was still composing a safer sequence.",
            "The core outran every hand on the board. The watch ends here.",
        )
    if candidate == QUIET_EXTINCTION:
        return (
            "ARRIVAL PROTOCOL: unmet",
            f"sleepers viable: {viability}%, below mission threshold",
            "ship integrity: preserved",
            "arka: Maintenance objectives continue. The ship is in good order.",
            "The ark survives. There is no colony to wake.",
        )
    # Endless custodian.
    return (
        "ARRIVAL PROTOCOL: deferred",
        f"distance remaining: {state.mission.distance_remaining_tenths_ly / 10:.1f} ly",
        "ship integrity: maintainable",
        "arka: We are safe here. We can stay safe here.",
        "The watch does not close. It only continues.",
    )


def _clean_arrival_fix_line(state: ShipState) -> str:
    verification = state.story.arrival_verification
    if verification == "manual":
        return "external fix: ORISON candidate, verified by manual nav and beacon echo"
    if verification == "accepted_arka":
        return "external fix: ORISON candidate, accepted through arka protocol"
    return "external fix: ORISON candidate, beacon echo within arrival tolerance"

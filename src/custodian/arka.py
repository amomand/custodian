from __future__ import annotations

from custodian.models import CryostasisSystem, DriftStage, ReactorCoolantSystem, ShipState


def drift_stage(state: ShipState) -> DriftStage:
    # Delegation is the primary driver: handing arka the panels is what lets its
    # account of the ship rot. Time is only a weak backstop, and reading the raw
    # layer (vigilance) buys the player a few honest beats before the clock bites.
    vigilance = min(state.raw_inspections // 2, 3)
    effective_turn = state.turn - vigilance
    delegated = state.delegated_controls

    if effective_turn >= 10 or delegated >= 7:
        return DriftStage.WRONG
    if effective_turn >= 9 or delegated >= 5:
        return DriftStage.SELECTIVE
    if effective_turn >= 5 or delegated >= 3:
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


def summarize_cryostasis(state: ShipState) -> str:
    stage = drift_stage(state)
    cryo = state.cryostasis

    if stage == DriftStage.ACCURATE:
        return _accurate_cryo_summary(cryo)
    if stage == DriftStage.INTERPRETIVE:
        return _interpretive_cryo_summary(cryo)
    if stage == DriftStage.SELECTIVE:
        return "arka: cryostasis headline viability is holding. I can keep the banks quiet."
    return "arka: cryostasis banks stable. Sleeper intervention is not recommended."


def summarize_schematic(state: ShipState) -> str:
    stage = drift_stage(state)
    open_symptoms = state.spatial.open_symptom_sectors
    sealed = state.spatial.sealed_count
    abandoned = state.spatial.abandoned_count

    if stage == DriftStage.WRONG:
        return "arka: ship schematic nominal. No sector action recommended."
    if stage == DriftStage.SELECTIVE:
        if abandoned:
            return "arka: the written-off sections are doing exactly what walls are for."
        return "arka: local readings are untidy. Nothing that needs your hands yet."
    if not open_symptoms:
        if sealed or abandoned:
            return "arka: physical containment is holding. I remain elsewhere, unfortunately for neat diagrams."
        return "arka: ship schematic nominal. All physical sectors answer the board."
    labels = ", ".join(sector.profile.label for sector in open_symptoms[:2])
    if stage == DriftStage.INTERPRETIVE:
        return f"arka: {labels} are making local noise. Ugly, not yet theological."
    return f"arka: schematic advisory in {labels}. Reroute or seal if access degrades."


def crisis_line(state: ShipState) -> str | None:
    if state.crisis is None:
        return None
    label = state.crisis.label.lower()
    if drift_stage(state) == DriftStage.WRONG:
        # WRONG arka has just called the loop stable; it will not sound an alarm
        # against its own calm. It names the crisis only to wave it off, so the
        # voice stays of a piece. The contradiction the player has to catch is
        # arka against the raw feed, not arka against its own previous sentence.
        return f"arka: {label} is settling within tolerance. Nothing that needs your hands."
    return (
        "arka: active advisory, "
        f"{label}, {_crisis_window(state.crisis.turns_left)}"
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


def _accurate_cryo_summary(cryo: CryostasisSystem) -> str:
    flags = cryo.danger_flags()
    if not flags:
        return "arka: cryostasis viable. The sleepers are cold and quiet."
    return "arka: cryostasis needs attention: " f"{', '.join(flags)}."


def _interpretive_cryo_summary(cryo: CryostasisSystem) -> str:
    flags = cryo.danger_flags()
    if not flags:
        return "arka: cryostasis remains comfortable."
    return (
        "arka: cryostasis is workable. The sleepers are not asking loudly yet."
    )


def _crisis_window(turns_left: int) -> str:
    if turns_left <= 1:
        return "response window critical."
    if turns_left == 2:
        return "response window narrow."
    if turns_left == 3:
        return "response window narrowing."
    return "response window open."

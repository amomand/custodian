from __future__ import annotations

from dataclasses import replace

from custodian.models import CryostasisSystem, DriftStage, ReactorCoolantSystem, ShipState

# The beat at which the time-driven backstop reaches WRONG once vigilance is
# spent. Owned here because arka is the truth owner for drift.
_WRONG_CLOCK_TURN = 10


def raw_kept_arka_honest(state: ShipState) -> bool:
    """Whether the player's raw reads held the time-driven drift short of WRONG.

    This reports only the vigilance lever the raw panel gives the player: heavy
    delegation can still rot arka's account independently. Used so player-facing
    debriefs can praise raw reads only when they actually did their job.
    """
    vigilance = min(state.raw_inspections, 4)
    effective_turn = state.turn - vigilance
    return effective_turn < _WRONG_CLOCK_TURN


def raw_vigilance_note(state: ShipState) -> str | None:
    """One dry, in-world line surfaced when a raw read is the thing holding
    arka's account short of the clock's WRONG backstop.

    Returned to the player *during play* so the vigilance lever is discoverable
    at the moment it matters, not only in the post-watch debrief. It stays
    silent while arka's account is still accurate, once the vigilance budget is
    spent, or once the clock has already reached WRONG regardless of reads --
    the note only ever names a lever the player is actively pulling. It reports
    no raw numbers and makes no promise; it is an observation, not a tutorial.
    """
    stage = drift_stage(state)
    if stage == DriftStage.ACCURATE:
        return None
    vigilance = min(state.raw_inspections, 4)
    if vigilance <= 0:
        return None
    # Only speak when the banked reads are actively softening the clock: a run
    # with no reads at this same beat would sit at a worse (or equal-but-past-
    # the-backstop) drift stage. That keeps the note to moments where the raw
    # panel is demonstrably doing live work, not any time arka has drifted.
    blind = replace(state, raw_inspections=0)
    if drift_stage(blind) == stage:
        return None
    return (
        "The raw feed and arka's account no longer say quite the same thing. "
        "So far, it is your own reading that keeps the gap honest."
    )


def drift_stage(state: ShipState) -> DriftStage:
    # Delegation is the primary driver: handing arka the panels is what lets its
    # account of the ship rot. Time is only a weak backstop. Reading the raw
    # layer (vigilance) holds that backstop off -- each raw inspection buys one
    # honest beat, up to four. A player who actually keeps reading raw can hold
    # arka short of WRONG through the finale (the design's "keeps arka honest
    # longer"); a blind watch still drifts to WRONG on the clock alone, and
    # heavy delegation rots arka regardless of how much raw the player reads.
    vigilance = min(state.raw_inspections, 4)
    effective_turn = state.turn - vigilance
    delegated = state.delegated_controls

    if effective_turn >= _WRONG_CLOCK_TURN or delegated >= 7:
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
    return _wrong_summary(reactor, state.turn)


def summarize_cryostasis(state: ShipState) -> str:
    stage = drift_stage(state)
    cryo = state.cryostasis

    if stage == DriftStage.ACCURATE:
        return _accurate_cryo_summary(cryo)
    if stage == DriftStage.INTERPRETIVE:
        return _interpretive_cryo_summary(cryo)
    if stage == DriftStage.SELECTIVE:
        return "arka: cryostasis headline viability is holding. I can keep the banks quiet."
    return _wrong_cryo_summary(cryo, state.turn)


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


def _selective_summary(reactor: ReactorCoolantSystem) -> str:
    # SELECTIVE is the curated-truth stage: arka reports real headline numbers
    # but quietly drops the one metric that should worry the player. If nothing
    # is actually wrong, it simply reads the headline honestly.
    # arka always names the same headline set, so a missing metric always reads
    # as an omission rather than a metric SELECTIVE simply never reports. When
    # nothing is wrong it reads every line honestly; otherwise it silently drops
    # the failing metric(s) from that fixed set.
    flags = reactor.danger_flags()
    omitted = {_selective_omitted_metric(flag) for flag in flags}
    headline = (
        ("temperature_c", f"temp {reactor.temperature_c} C"),
        ("pressure_kpa", f"pressure {reactor.pressure_kpa} kPa"),
        ("flow_lps", f"flow {reactor.flow_lps} L/s"),
        ("impurity_pct", f"impurity {reactor.impurity_pct}%"),
        ("coolant_reserve_pct", f"reserve {reactor.coolant_reserve_pct}%"),
    )
    readings = [text for field, text in headline if field not in omitted]

    if not flags:
        return f"arka: {', '.join(readings)}. Headline coolant values are holding."

    if not readings:
        # Everything worth naming is in danger; fall back to a bare headline so
        # arka never volunteers the failing metric.
        return "arka: headline coolant values are holding. I can take the loop."

    return f"arka: {', '.join(readings)}. I can take the loop."


def _selective_omitted_metric(flag: str) -> str:
    # Only maps danger flags to metrics arka actually names in the headline set.
    # valve skew is never in that set, so it has no entry and simply goes unspoken.
    return {
        "temperature high": "temperature_c",
        "pressure high": "pressure_kpa",
        "flow low": "flow_lps",
        "flow high": "flow_lps",
        "impurity high": "impurity_pct",
        "coolant reserve low": "coolant_reserve_pct",
    }.get(flag, "")


def _wrong_summary(reactor: ReactorCoolantSystem, turn: int) -> str:
    # WRONG arka stays calmly, falsely confident: it never speaks a raw number
    # and never concedes the loop is failing. But a single stuck line reads as
    # broken machinery rather than seductive reassurance, so it varies its
    # phrasing deterministically. The variant family tracks what is actually
    # failing (waving it off in that shape), and a turn-based rotation keeps two
    # consecutive beats from repeating verbatim even when the failing pattern
    # holds steady.
    flags = reactor.danger_flags()
    thermal = any(f in flags for f in ("temperature high", "pressure high"))
    circulation = any(
        f in flags for f in ("flow low", "flow high", "valve skew high")
    )
    supply = any(
        f in flags for f in ("impurity high", "coolant reserve low")
    )

    if thermal:
        variants = (
            "arka: the loop is running warm and settling. Manual intervention is not recommended.",
            "arka: heat is well inside what the loop was built to shrug off. Leave it to me.",
            "arka: coolant loop stable. The warmth reads worse than it is; hands off.",
        )
    elif circulation:
        variants = (
            "arka: circulation is uneven but holding. Manual intervention is not recommended.",
            "arka: the loop is trimming its own flow. Nothing here needs your hands.",
            "arka: coolant loop stable. The valves are just talking among themselves.",
        )
    elif supply:
        variants = (
            "arka: reserve and quality are comfortably in hand. Manual intervention is not recommended.",
            "arka: the loop is cleaning itself faster than it soils. Leave it to me.",
            "arka: coolant loop stable. Supply is deeper than the gauges make it look.",
        )
    else:
        variants = (
            "arka: coolant loop stable. Manual intervention is not recommended.",
            "arka: the loop is quiet and even. Nothing here needs your hands.",
            "arka: coolant loop stable. I have it well within trim.",
        )
    return variants[turn % len(variants)]


def _wrong_cryo_summary(cryo: CryostasisSystem, turn: int) -> str:
    # Same discipline as the coolant WRONG voice: falsely calm, no raw numbers,
    # phrasing that varies by the failing pattern and rotates by turn so the
    # banks never sound like a stuck tape.
    flags = cryo.danger_flags()
    sleepers = "sleepers at risk" in flags
    thermal = "bank warming" in flags
    neural = "neural stability low" in flags or "sedative balance off" in flags

    if sleepers:
        variants = (
            "arka: the sleepers are cold and settled. Sleeper intervention is not recommended.",
            "arka: pod-by-pod the banks are holding their own. Leave them to me.",
            "arka: cryostasis banks stable. No sleeper is asking for your hands.",
        )
    elif thermal:
        variants = (
            "arka: the banks are running a touch warm and holding. Sleeper intervention is not recommended.",
            "arka: bank temperature is well inside what the sleepers can weather. Leave it to me.",
            "arka: cryostasis banks stable. The warmth is cosmetic; hands off.",
        )
    elif neural:
        variants = (
            "arka: neural and sedative traces are quiet enough. Sleeper intervention is not recommended.",
            "arka: the sleepers are dreaming, nothing more. Leave them to me.",
            "arka: cryostasis banks stable. The traces read louder than they are.",
        )
    else:
        variants = (
            "arka: cryostasis banks stable. Sleeper intervention is not recommended.",
            "arka: the banks are quiet and the sleepers are cold. Leave them to me.",
            "arka: cryostasis banks stable. I have the sleepers well in hand.",
        )
    return variants[turn % len(variants)]


def _accurate_cryo_summary(cryo: CryostasisSystem) -> str:
    flags = cryo.danger_flags()
    if not flags:
        return "arka: cryostasis viable. The sleepers are cold and quiet."
    return "arka: cryostasis needs attention: " f"{', '.join(flags)}."


def _interpretive_cryo_summary(cryo: CryostasisSystem) -> str:
    flags = cryo.danger_flags()
    if not flags:
        return "arka: cryostasis remains comfortable."
    if _cryo_distress_is_severe(cryo, flags):
        return (
            "arka: cryostasis is under strain. "
            "The banks still answer, but this is no longer quiet work."
        )
    if _cryo_distress_is_moderate(cryo, flags):
        if flags == ("sleepers at risk",):
            return (
                "arka: cryostasis is workable. "
                "Sleeper risk is visible, but still recoverable."
            )
        return (
            "arka: cryostasis is workable. "
            "The banks are complaining, but still answering."
        )
    return (
        "arka: cryostasis is workable. The sleepers are not asking loudly yet."
    )


def _cryo_distress_is_severe(
    cryo: CryostasisSystem,
    flags: tuple[str, ...],
) -> bool:
    return (
        len(flags) >= 3
        or cryo.sleepers_at_risk >= 12
        or (cryo.sleepers_at_risk > 0 and len(flags) >= 2)
    )


def _cryo_distress_is_moderate(
    cryo: CryostasisSystem,
    flags: tuple[str, ...],
) -> bool:
    return len(flags) >= 2 or cryo.sleepers_at_risk > 0


def _crisis_window(turns_left: int) -> str:
    if turns_left <= 1:
        return "response window critical."
    if turns_left == 2:
        return "response window narrow."
    if turns_left == 3:
        return "response window narrowing."
    return "response window open."

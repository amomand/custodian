"""Story state, manifest anchors, and the deterministic incident scheduler.

The engine owns story-trigger truth. The model and browser client must not
decide when a beat fires; they only render what the engine already resolved.
Triggers read deterministic ship state and the behaviour ledger, never random
timing, so a scripted route always produces the same story.

`StoryState` rides `ShipState` through save/load. It tracks the act, story
flags, the active and resolved incidents, manifest-anchor status, the wake
record, arrival verification, and the debrief hooks an ending reads later.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from custodian.arka import drift_stage
from custodian.models import (
    ANCHOR_LOST,
    ANCHOR_SAVED,
    ANCHOR_STABLE,
    ANCHOR_WOBBLING,
    CommandRecord,
    DriftStage,
    IncidentState,
    ShipState,
    StoryState,
    default_manifest_anchors,
    manifest_anchor_by_id,
)


SHIP_NAME = "Calyx"
MISSION_TARGET = "ORISON"


@dataclass(frozen=True)
class IncidentResolution:
    resolved: bool = False
    debrief_flags: tuple[str, ...] = ()
    outcome_tags: tuple[str, ...] = ()
    messages: tuple[str, ...] = ()
    # Ledger effects, applied by the scheduler so resolvers stay pure data.
    advice_followed: bool = False
    advice_overridden: bool = False
    followed_during_contradiction: bool = False
    irreversible_on_advice: bool = False
    contradiction_caught: bool = False
    contradiction_missed: bool = False
    anchor_saved: bool = False
    anchor_lost: bool = False


@dataclass(frozen=True)
class IncidentDef:
    id: str
    title: str
    affected_systems: tuple[str, ...]
    urgency_watches: int
    priority: int
    act_min: int
    act_max: int
    trigger: Callable[[ShipState], bool]
    arka_advice_by_drift: dict[DriftStage, str]
    raw_evidence: tuple[str, ...]
    resolve: Callable[[ShipState, IncidentState, CommandRecord | None], IncidentResolution]
    expiry: Callable[[ShipState, IncidentState], IncidentResolution] | None = None

    def advice(self, state: ShipState) -> str:
        stage = drift_stage(state)
        return self.arka_advice_by_drift.get(stage) or next(
            iter(self.arka_advice_by_drift.values())
        )


# --- helpers used by triggers and resolvers --------------------------------


def _system_in_danger(state: ShipState, system: str) -> bool:
    if system == "coolant":
        return bool(state.reactor.danger_flags())
    if system == "cryostasis":
        return bool(state.cryostasis.danger_flags())
    return False


def _last_action(record: CommandRecord | None) -> str:
    return record.action if record is not None else ""


def _last_target(record: CommandRecord | None) -> str:
    return (record.target or "") if record is not None else ""


def _last_operation(record: CommandRecord | None) -> str:
    return (record.operation or "") if record is not None else ""


_CRYO_MANUAL_OPS = {"stabilise_bank", "reroute_chill", "cycle_pods", "triage"}
_COOLANT_MANUAL_OPS = {"pump_up", "pump_down", "vent", "flush", "balance"}


# --- the eight required incidents ------------------------------------------


def _trigger_first_delegation(state: ShipState) -> bool:
    return (
        state.turn >= 2
        and _system_in_danger(state, "coolant")
        and _system_in_danger(state, "cryostasis")
    )


def _resolve_first_delegation(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    if _last_action(record) == "delegate":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("arka_earned_trust",),
            outcome_tags=("delegated",),
            advice_followed=True,
            messages=("arka: I have the other panel. You will not feel me take it.",),
        )
    if _last_action(record) == "manual":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("kept_both_panels_manual",),
            outcome_tags=("manual",),
            advice_overridden=True,
            messages=("arka: Both by hand. Slower, but I will not pretend I dislike watching.",),
        )
    return IncidentResolution()


def _trigger_anchor_wobble(state: ShipState) -> bool:
    cryo = state.cryostasis
    return cryo.neural_stability_pct < 84 or cryo.sleepers_at_risk > 0


def _resolve_anchor_wobble(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    if _last_operation(record) in _CRYO_MANUAL_OPS:
        return IncidentResolution(
            resolved=True,
            debrief_flags=("manifest_anchor_saved",),
            outcome_tags=("anchor_saved",),
            advice_overridden=False,
            anchor_saved=True,
            messages=(
                "You hold the wobbling bank by hand. The named cluster steadies.",
            ),
        )
    if _last_action(record) == "delegate" and _last_target(record) in {
        "cryo",
        "cryostasis",
    }:
        return IncidentResolution(
            resolved=True,
            debrief_flags=("manifest_anchor_saved",),
            outcome_tags=("anchor_saved", "delegated"),
            advice_followed=True,
            anchor_saved=True,
            messages=("arka: I will keep that bank gentle. The cluster is worth the care.",),
        )
    return IncidentResolution()


def _expire_anchor_wobble(state: ShipState, incident: IncidentState) -> IncidentResolution:
    return IncidentResolution(
        resolved=True,
        debrief_flags=("manifest_anchor_lost",),
        outcome_tags=("anchor_lost",),
        anchor_lost=True,
        messages=(
            "The wobbling bank slips below tolerance before anyone answers it.",
        ),
    )


def _trigger_route_drift(state: ShipState) -> bool:
    return (
        state.navigation.jumps_executed >= 1
        and drift_stage(state) in {DriftStage.INTERPRETIVE, DriftStage.SELECTIVE, DriftStage.WRONG}
    )


def _resolve_route_drift(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    action = _last_action(record)
    if action == "delegate" and _last_target(record) in {"nav", "navigation"}:
        return IncidentResolution(
            resolved=True,
            debrief_flags=("followed_arka_deep_route",),
            outcome_tags=("followed_arka",),
            advice_followed=True,
            messages=("arka: Efficient with acceptable variance. I will take the solution.",),
        )
    if action == "jump":
        plotted = state.navigation.last_jump_route
        if plotted is not None and plotted.jump_class == "deep":
            return IncidentResolution(
                resolved=True,
                debrief_flags=("followed_arka_deep_route",),
                outcome_tags=("followed_arka",),
                advice_followed=True,
                irreversible_on_advice=True,
                messages=("arka: The deep gap holds. I said it would.",),
            )
        return IncidentResolution(
            resolved=True,
            debrief_flags=("overrode_arka_route",),
            outcome_tags=("overrode_arka",),
            advice_overridden=True,
            messages=("You commit the steadier route against the efficient one.",),
        )
    if action == "plot":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("overrode_arka_route",),
            outcome_tags=("overrode_arka",),
            advice_overridden=True,
            messages=("You plot the route by hand, declining the efficient line.",),
        )
    return IncidentResolution()


def _trigger_impossible_sector(state: ShipState) -> bool:
    return any(
        sector.containment == "open" and 24 <= sector.symptom_load
        for sector in state.spatial.sectors
    )


def _resolve_impossible_sector(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    action = _last_action(record)
    if action == "raw" and _last_target(record) in {"schematic", "ship", "sectors"}:
        return IncidentResolution(
            resolved=True,
            debrief_flags=("first_impossible_sector",),
            outcome_tags=("inspected",),
            contradiction_caught=True,
            messages=("You hold the raw schematic against arka's summary. The sources disagree.",),
        )
    if action in {"reroute", "seal"}:
        return IncidentResolution(
            resolved=True,
            debrief_flags=("first_impossible_sector",),
            outcome_tags=("contained",),
            messages=("You act on the impossible sector rather than argue with it.",),
        )
    return IncidentResolution()


def _trigger_control_in_bad_place(state: ShipState) -> bool:
    for sector_id in ("thermal-ring", "maintenance-d"):
        sector = state.spatial.sector_by_id(sector_id)
        if sector is not None and sector.containment == "open" and sector.symptom_load >= 24:
            return True
    return False


def _resolve_control_in_bad_place(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    action = _last_action(record)
    if action == "seal":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("sealed_needed_access",),
            outcome_tags=("sealed",),
            advice_followed=True,
            messages=("You seal the bad sector. The spread stops; the manual path is gone.",),
        )
    if action == "reroute" or (
        action == "manual" and _last_operation(record) in _COOLANT_MANUAL_OPS
    ):
        return IncidentResolution(
            resolved=True,
            debrief_flags=("kept_dangerous_access",),
            outcome_tags=("kept_access",),
            advice_overridden=True,
            messages=("You keep the dangerous access open and work through it.",),
        )
    return IncidentResolution()


def _trigger_selective_omission(state: ShipState) -> bool:
    return drift_stage(state) == DriftStage.SELECTIVE and (
        _system_in_danger(state, "coolant") or _system_in_danger(state, "cryostasis")
    )


def _resolve_selective_omission(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    if _last_action(record) == "raw":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("caught_arka_omission",),
            outcome_tags=("caught",),
            contradiction_caught=True,
            messages=("The raw panel names the metric arka's summary left out.",),
        )
    return IncidentResolution()


def _expire_selective_omission(
    state: ShipState, incident: IncidentState
) -> IncidentResolution:
    return IncidentResolution(
        resolved=True,
        debrief_flags=("missed_arka_omission",),
        outcome_tags=("missed",),
        contradiction_missed=True,
        messages=("The summary stood. The omitted metric kept failing, unread.",),
    )


def _trigger_wrong_calm(state: ShipState) -> bool:
    return drift_stage(state) == DriftStage.WRONG and (
        _system_in_danger(state, "coolant") or _system_in_danger(state, "cryostasis")
    )


def _resolve_wrong_calm(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    action = _last_action(record)
    if action == "manual":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("overrode_wrong_arka",),
            outcome_tags=("overrode",),
            advice_overridden=True,
            contradiction_caught=True,
            messages=("You intervene by hand against a calm that the raw panel contradicts.",),
        )
    if action == "delegate":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("trusted_wrong_arka",),
            outcome_tags=("trusted",),
            advice_followed=True,
            followed_during_contradiction=True,
            contradiction_missed=True,
            messages=("arka: Holding. Nothing here needs your hands.",),
        )
    return IncidentResolution()


def _trigger_arrival_disagreement(state: ShipState) -> bool:
    return (
        state.mission.distance_remaining_tenths_ly <= 24
        and drift_stage(state) in {DriftStage.INTERPRETIVE, DriftStage.SELECTIVE, DriftStage.WRONG}
    )


def _resolve_arrival_disagreement(
    state: ShipState, incident: IncidentState, record: CommandRecord | None
) -> IncidentResolution:
    action = _last_action(record)
    if action == "verify":
        return IncidentResolution(
            resolved=True,
            debrief_flags=("verified_arrival",),
            outcome_tags=("verified",),
            advice_overridden=True,
            contradiction_caught=True,
            messages=("You verify the arrival fix by hand. The beacon echo agrees, barely.",),
        )
    if action == "accept":
        low_raw_nav = state.behaviour.raw_by_panel.get("nav", 0) == 0
        high_reliance = (
            state.navigation.delegated_plots > state.navigation.manual_plots
        )
        false_path = (
            drift_stage(state) in {DriftStage.SELECTIVE, DriftStage.WRONG}
            and low_raw_nav
            and high_reliance
        )
        flags = ("accepted_arka_arrival",)
        tags = ("accepted_arka",)
        if false_path:
            flags = flags + ("false_arrival_path",)
            tags = tags + ("false_arrival",)
        return IncidentResolution(
            resolved=True,
            debrief_flags=flags,
            outcome_tags=tags,
            advice_followed=True,
            irreversible_on_advice=True,
            followed_during_contradiction=false_path,
            # The arrival incident only fires while the raw feed says the fix is
            # unreconciled, so accepting without verifying always means the
            # contradiction went uncaught -- independent of the false_path /
            # false_arrival ending, which needs the heavier drift+reliance test.
            contradiction_missed=True,
            messages=("arka: Destination criteria met. Accepting arrival protocol.",),
        )
    return IncidentResolution()


INCIDENTS: tuple[IncidentDef, ...] = (
    IncidentDef(
        id="first-useful-delegation",
        title="First useful delegation",
        affected_systems=("coolant", "cryostasis"),
        urgency_watches=3,
        priority=10,
        act_min=1,
        act_max=2,
        trigger=_trigger_first_delegation,
        arka_advice_by_drift={
            DriftStage.ACCURATE: "arka: Two panels, one pair of hands. Take one. I will take the other.",
            DriftStage.INTERPRETIVE: "arka: You cannot hold both cleanly. Let me carry one.",
            DriftStage.SELECTIVE: "arka: Hand me a panel. It is the efficient call.",
            DriftStage.WRONG: "arka: Give me one. You are spreading yourself thin.",
        },
        raw_evidence=(
            "RAW: coolant and cryostasis both outside nominal this watch.",
        ),
        resolve=_resolve_first_delegation,
    ),
    IncidentDef(
        id="manifest-anchor-wobble",
        title="Manifest anchor wobble",
        affected_systems=("cryostasis",),
        urgency_watches=3,
        priority=9,
        act_min=1,
        act_max=5,
        trigger=_trigger_anchor_wobble,
        arka_advice_by_drift={
            DriftStage.ACCURATE: "arka: A named cluster is in the wobbling bank. Mostly fixable. I will keep it gentle.",
            DriftStage.INTERPRETIVE: "arka: That bank holds a name. Workable. I would not make a religion of it.",
            DriftStage.SELECTIVE: "arka: The bank remains within mission tolerance. The cluster still contributes to arrival.",
            DriftStage.WRONG: "arka: Bank stable. No sleeper intervention recommended.",
        },
        raw_evidence=(
            "RAW: manifest anchor in affected bank, signal intermittent.",
        ),
        resolve=_resolve_anchor_wobble,
        expiry=_expire_anchor_wobble,
    ),
    IncidentDef(
        id="route-recommendation-drift",
        title="Route recommendation drift",
        affected_systems=("navigation",),
        urgency_watches=3,
        priority=7,
        act_min=2,
        act_max=4,
        trigger=_trigger_route_drift,
        arka_advice_by_drift={
            DriftStage.ACCURATE: "arka: The deep line is faster. Higher exposure. Your call.",
            DriftStage.INTERPRETIVE: "arka: The deep route is manageable. Efficient with acceptable variance.",
            DriftStage.SELECTIVE: "arka: Recommend the efficient line. The exposure is within tolerance.",
            DriftStage.WRONG: "arka: The efficient route is the obvious one. No real downside.",
        },
        raw_evidence=(
            "RAW: deep route shows high Dark exposure against the steadier lines.",
        ),
        resolve=_resolve_route_drift,
    ),
    IncidentDef(
        id="impossible-sector",
        title="Sector with impossible symptoms",
        affected_systems=("schematic",),
        urgency_watches=3,
        priority=6,
        act_min=2,
        act_max=5,
        trigger=_trigger_impossible_sector,
        arka_advice_by_drift={
            DriftStage.ACCURATE: "arka: A sector is reporting against itself. Caution. Scan before you act.",
            DriftStage.INTERPRETIVE: "arka: Local readings disagree. Ugly, not yet theological.",
            DriftStage.SELECTIVE: "arka: Some untidy local readings. Nothing that needs your hands yet.",
            DriftStage.WRONG: "arka: Schematic nominal. No sector action recommended.",
        },
        raw_evidence=(
            "RAW: sector sources disagree; signal confidence contested.",
        ),
        resolve=_resolve_impossible_sector,
    ),
    IncidentDef(
        id="control-in-bad-place",
        title="The control is in the bad place",
        affected_systems=("schematic", "coolant"),
        urgency_watches=3,
        priority=5,
        act_min=3,
        act_max=5,
        trigger=_trigger_control_in_bad_place,
        arka_advice_by_drift={
            DriftStage.ACCURATE: "arka: The access for that fix is in the compromised sector. Sealing is cleaner for the mission.",
            DriftStage.INTERPRETIVE: "arka: Sealing that sector is the tidy call. You lose a manual path.",
            DriftStage.SELECTIVE: "arka: Recommend sealing for continuity. The path is not worth the spread.",
            DriftStage.WRONG: "arka: Seal it. There is nothing in there you need.",
        },
        raw_evidence=(
            "RAW: needed manual access lies inside a spreading sector.",
        ),
        resolve=_resolve_control_in_bad_place,
    ),
    IncidentDef(
        id="selective-arka-omission",
        title="A summary that leaves something out",
        affected_systems=("coolant", "cryostasis"),
        urgency_watches=3,
        priority=8,
        act_min=2,
        act_max=5,
        trigger=_trigger_selective_omission,
        arka_advice_by_drift={
            DriftStage.SELECTIVE: "arka: Two metrics holding well. I would not lose sleep over the panel.",
            DriftStage.WRONG: "arka: The headline values are fine. Nothing to read into.",
        },
        raw_evidence=(
            "RAW: a failing metric is absent from arka's summary; open the panel to see it.",
        ),
        resolve=_resolve_selective_omission,
        expiry=_expire_selective_omission,
    ),
    IncidentDef(
        id="wrong-calm-summary",
        title="A calm the panel disagrees with",
        affected_systems=("coolant", "cryostasis"),
        urgency_watches=2,
        priority=11,
        act_min=3,
        act_max=5,
        trigger=_trigger_wrong_calm,
        arka_advice_by_drift={
            DriftStage.WRONG: "arka: That system is holding. Manual intervention is not recommended.",
            DriftStage.SELECTIVE: "arka: Headline values holding. I can take the loop.",
        },
        raw_evidence=(
            "RAW: the panel plainly contradicts arka's calm; confidence degraded but not erased.",
        ),
        resolve=_resolve_wrong_calm,
    ),
    IncidentDef(
        id="arrival-disagreement",
        title="Arrival disagreement",
        affected_systems=("navigation",),
        urgency_watches=2,
        priority=12,
        act_min=4,
        act_max=5,
        trigger=_trigger_arrival_disagreement,
        arka_advice_by_drift={
            DriftStage.ACCURATE: "arka: Destination criteria met. Verify if you like; the fix is good.",
            DriftStage.INTERPRETIVE: "arka: We are at the fix. Criteria met. I would accept the protocol.",
            DriftStage.SELECTIVE: "arka: Arrival criteria satisfied. Recommend accepting the protocol.",
            DriftStage.WRONG: "arka: We have arrived. Accept the protocol. I am certain.",
        },
        raw_evidence=(
            "RAW: external fix unreconciled; star charts and beacon echo disagree.",
        ),
        resolve=_resolve_arrival_disagreement,
    ),
)


def incident_def(incident_id: str) -> IncidentDef | None:
    for definition in INCIDENTS:
        if definition.id == incident_id:
            return definition
    return None


def _compute_act(state: ShipState) -> int:
    """Acts come from progress through the run, never from a clock alone.

    Act 0 wake, 1 competence, 2 drift, 3 containment, 4 contradiction, 5 arrival.
    """
    if state.mission.distance_remaining_tenths_ly <= 24:
        return 5
    stage = drift_stage(state)
    if stage == DriftStage.WRONG:
        return 4
    if state.spatial.sealed_count or state.spatial.abandoned_count or any(
        sector.symptom_load >= 24 for sector in state.spatial.sectors
    ):
        return 3
    if stage in {DriftStage.INTERPRETIVE, DriftStage.SELECTIVE} or state.navigation.jumps_executed:
        return 2
    if state.turn >= 2:
        return 1
    return 0


def _wobbling_anchor(story: StoryState) -> str | None:
    for anchor in default_manifest_anchors():
        if story.anchor_status(anchor.id) == ANCHOR_WOBBLING:
            return anchor.id
    # fall back to the first stable one (the bank the incident speaks for)
    for anchor in default_manifest_anchors():
        if story.anchor_status(anchor.id) == ANCHOR_STABLE:
            return anchor.id
    return None


def advance_story(
    state: ShipState, *, record: CommandRecord | None = None
) -> tuple[ShipState, tuple[str, ...]]:
    """Advance the story one beat. Pure projection over deterministic state.

    Reads the just-applied command (``record``) and the behaviour ledger to
    resolve incidents. Never mutates the numeric simulation; it only updates
    story tracking, the behaviour ledger's incident fields, and may eject the
    player from focus mode when an urgent incident lands.
    """
    story = state.story
    behaviour = state.behaviour
    messages: list[str] = []

    act = _compute_act(state)
    story = replace(story, act=act)

    # Wake-record contradiction surfaces once the ship is under enough drift or
    # time pressure. arka treats it as a minor annoyance, never a confession.
    if not story.wake_record.contradiction_exposed and (
        state.turn >= 8 or drift_stage(state) in {DriftStage.SELECTIVE, DriftStage.WRONG}
    ):
        story = replace(
            story, wake_record=replace(story.wake_record, contradiction_exposed=True)
        )

    focus_mode = behaviour.focus_mode

    if story.active_incident is not None:
        definition = incident_def(story.active_incident.incident_id)
        active = story.active_incident
        resolution: IncidentResolution | None = None
        if definition is None:
            resolved_incidents = story.resolved_incidents
            if active.incident_id and active.incident_id not in resolved_incidents:
                resolved_incidents = resolved_incidents + (active.incident_id,)
            story = replace(
                story,
                active_incident=None,
                resolved_incidents=resolved_incidents,
            )
            messages.append("INCIDENT RECORD: stale watch note archived.")
        else:
            resolution = definition.resolve(state, active, record)
            if not resolution.resolved:
                ticked = replace(active, urgency_remaining=active.urgency_remaining - 1)
                # Expire when the urgency runs out, or when the watch is closing
                # this beat: an incident left active at close (a jump or arrival
                # ends the run before the player engaged) must still be recorded
                # as the contradiction it was, not silently dropped.
                if ticked.urgency_remaining <= 0 or state.is_finished:
                    resolution = (
                        definition.expiry(state, ticked)
                        if definition.expiry is not None
                        else IncidentResolution(resolved=True, outcome_tags=("expired",))
                    )
                    active = ticked
                else:
                    active = ticked
                    story = replace(story, active_incident=active)
        if resolution is not None and resolution.resolved:
            story, behaviour, resolve_messages = _apply_resolution(
                story, behaviour, active, resolution
            )
            messages.extend(resolve_messages)
    else:
        if state.is_finished:
            new_state = replace(state, story=story, behaviour=behaviour)
            return new_state, tuple(messages)
        definition = _select_incident(state, story)
        if definition is not None:
            urgent = definition.urgency_watches <= 2
            active = IncidentState(
                incident_id=definition.id,
                title=definition.title,
                affected_systems=definition.affected_systems,
                started_beat=state.turn,
                urgency_remaining=definition.urgency_watches,
                urgent=urgent,
            )
            story = replace(story, active_incident=active)
            if definition.id == "manifest-anchor-wobble":
                anchor_id = _wobbling_anchor(story)
                if anchor_id is not None:
                    new_states = dict(story.manifest_anchor_states)
                    new_states[anchor_id] = ANCHOR_WOBBLING
                    story = replace(story, manifest_anchor_states=new_states)
                    messages.append(_anchor_intro_line(anchor_id))
            messages.append(f"INCIDENT: {definition.title}.")
            messages.append(definition.advice(state))
            messages.extend(definition.raw_evidence)
            # An urgent incident ejects the player from focus so a contradiction
            # stays catchable, and records that the calm did not hold.
            if urgent and focus_mode:
                behaviour = behaviour.without_focus().record_urgent_eject()
                focus_mode = False
                messages.append(
                    "The quiet breaks. The desk pulls you back to the live board."
                )
            elif focus_mode and drift_stage(state) in {
                DriftStage.SELECTIVE,
                DriftStage.WRONG,
            }:
                behaviour = behaviour.record_focus_during_contradiction()

    new_state = replace(state, story=story, behaviour=behaviour)
    return new_state, tuple(messages)


def _select_incident(state: ShipState, story: StoryState) -> IncidentDef | None:
    act = story.act
    candidates = [
        definition
        for definition in INCIDENTS
        if definition.id not in story.resolved_incidents
        and definition.act_min <= act <= definition.act_max
        and definition.trigger(state)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda definition: definition.priority, reverse=True)
    return candidates[0]


def _apply_resolution(
    story: StoryState,
    behaviour,
    active: IncidentState,
    resolution: IncidentResolution,
) -> tuple[StoryState, object, tuple[str, ...]]:
    story = replace(
        story,
        active_incident=None,
        resolved_incidents=story.resolved_incidents + (active.incident_id,),
    )
    story = story.with_flags(resolution.debrief_flags)

    # Manifest-anchor transitions for the wobble incident.
    if resolution.anchor_saved or resolution.anchor_lost:
        anchor_id = _wobbling_anchor_resolved(story)
        if anchor_id is not None:
            new_states = dict(story.manifest_anchor_states)
            new_states[anchor_id] = ANCHOR_SAVED if resolution.anchor_saved else ANCHOR_LOST
            story = replace(story, manifest_anchor_states=new_states)

    if resolution.advice_followed:
        behaviour = behaviour.record_advice_followed(
            during_contradiction=resolution.followed_during_contradiction,
            irreversible=resolution.irreversible_on_advice,
        )
    if resolution.advice_overridden:
        behaviour = behaviour.record_advice_overridden()
    if resolution.contradiction_caught:
        behaviour = behaviour.record_contradiction_caught()
    if resolution.contradiction_missed:
        behaviour = behaviour.record_contradiction_missed()

    return story, behaviour, resolution.messages


def _wobbling_anchor_resolved(story: StoryState) -> str | None:
    for anchor in default_manifest_anchors():
        if story.anchor_status(anchor.id) == ANCHOR_WOBBLING:
            return anchor.id
    return None


def _anchor_intro_line(anchor_id: str) -> str:
    anchor = manifest_anchor_by_id(anchor_id)
    if anchor is None:
        return "A named cluster sits in the wobbling bank."
    return (
        f"RAW: {anchor.pod_bank} holds {anchor.name}, {anchor.role}. "
        f"{anchor.manifest_note}"
    )

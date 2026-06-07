from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from custodian.arka import (
    crisis_line,
    drift_stage,
    summarize_coolant,
    summarize_cryostasis,
    summarize_schematic,
)
from custodian.engine_constants import MISSION_END_TURN
from custodian.models import (
    CryostasisSystem,
    DriftStage,
    ReactorCoolantSystem,
    RouteOption,
    ShipSector,
    ShipState,
    SYSTEM_KEYS,
)
from custodian.objectives import objective_lines, trend


@dataclass(frozen=True)
class MetricSnapshot:
    id: str
    label: str
    value: int
    unit: str
    band: str
    trend: str
    nominal_low: int
    nominal_high: int
    note: str


@dataclass(frozen=True)
class MissionSnapshot:
    beat: int
    elapsed_label: str
    distance_label: str
    ship_wear_pct: int
    cryo_decay_pct: int
    sleepers_lost: int
    sleepers_at_risk: int
    watch_label: str
    current_fix_label: str
    plotted_route_label: str | None
    is_finished: bool
    outcome: str | None


@dataclass(frozen=True)
class ObjectiveSnapshot:
    summary: str
    watch: str
    attention: str
    manual_budget: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class SystemSnapshot:
    id: str
    label: str
    status: str
    arka_summary: str
    metrics: tuple[MetricSnapshot, ...]
    standing: bool


@dataclass(frozen=True)
class RouteSnapshot:
    id: str
    label: str
    jump_class: str
    distance_label: str
    elapsed_days: int
    exposure_band: str
    instability_pct: int
    wear_delta_pct: int
    cryo_decay_delta_pct: int
    is_plotted: bool
    is_last_jump: bool


@dataclass(frozen=True)
class NavigationSnapshot:
    current_fix_id: str
    current_fix_label: str
    current_signal: str
    current_purpose: str
    plotted_route_id: str | None
    plotted_route_label: str | None
    last_jump_route_id: str | None
    last_jump_route_label: str | None
    jumps_executed: int
    exposure_band: str
    standing: bool
    route_options: tuple[RouteSnapshot, ...]


@dataclass(frozen=True)
class SectorSnapshot:
    id: str
    label: str
    function: str
    controls: str
    adjacent: tuple[str, ...]
    reported_state: str
    signal_confidence: str
    containment: str
    rerouted: bool
    sealable: bool


@dataclass(frozen=True)
class SchematicSnapshot:
    containment_summary: str
    sectors: tuple[SectorSnapshot, ...]
    arka_locus: str


@dataclass(frozen=True)
class ArkaSnapshot:
    advisory_lines: tuple[str, ...]
    latest_messages: tuple[str, ...]


@dataclass(frozen=True)
class RawPanelSnapshot:
    id: str
    label: str
    source: str
    confidence: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class ActionSpec:
    id: str
    label: str
    command: str
    kind: str
    target: str
    enabled: bool = True
    reason: str | None = None
    requires_confirmation: bool = False
    detail: str | None = None


@dataclass(frozen=True)
class TranscriptEntry:
    kind: str
    text: str


@dataclass(frozen=True)
class VisualCorruptionSnapshot:
    arka_panel_intensity: str
    schematic_noise_by_sector: dict[str, str]
    raw_signal_confidence_by_panel: dict[str, str]
    label_instability: str
    reduced_motion_safe: bool


@dataclass(frozen=True)
class UiSnapshot:
    mission: MissionSnapshot
    objective: ObjectiveSnapshot
    systems: dict[str, SystemSnapshot]
    navigation: NavigationSnapshot
    schematic: SchematicSnapshot
    arka: ArkaSnapshot
    raw_panels: dict[str, RawPanelSnapshot]
    incident: dict[str, Any] | None
    actions: tuple[ActionSpec, ...]
    transcript_tail: tuple[TranscriptEntry, ...]
    visual_state: VisualCorruptionSnapshot
    dev: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_ui_snapshot(
    state: ShipState,
    *,
    last_messages: tuple[str, ...] = (),
    transcript_tail: tuple[str, ...] = (),
    include_dev: bool = False,
) -> UiSnapshot:
    """Project deterministic ship state into a web-safe render snapshot."""
    return UiSnapshot(
        mission=_mission_snapshot(state),
        objective=_objective_snapshot(state),
        systems=_system_snapshots(state),
        navigation=_navigation_snapshot(state),
        schematic=_schematic_snapshot(state),
        arka=_arka_snapshot(state, last_messages),
        raw_panels=_raw_panels(state),
        incident=_incident_snapshot(state),
        actions=_action_specs(state),
        transcript_tail=_transcript_entries(state, transcript_tail),
        visual_state=_visual_state(state),
        dev=_dev_snapshot(state) if include_dev else None,
    )


def project_safe_lines(state: ShipState, lines: tuple[str, ...]) -> tuple[str, ...]:
    """Apply UI snapshot redactions to legacy web-shell line output."""
    return tuple(_safe_transcript_line(state, line) for line in lines)


def _mission_snapshot(state: ShipState) -> MissionSnapshot:
    mission = state.mission
    plotted = state.navigation.plotted_route
    return MissionSnapshot(
        beat=state.turn,
        elapsed_label=_elapsed_label(mission.elapsed_days),
        distance_label=_distance_label(mission.distance_remaining_tenths_ly),
        ship_wear_pct=mission.ship_wear_pct,
        cryo_decay_pct=mission.cryo_decay_pct,
        sleepers_lost=state.sleepers_lost,
        sleepers_at_risk=state.cryostasis.sleepers_at_risk,
        watch_label=_watch_label(state),
        current_fix_label=state.navigation.current_fix.label,
        plotted_route_label=None if plotted is None else plotted.label,
        is_finished=state.is_finished,
        outcome=state.outcome,
    )


def _objective_snapshot(state: ShipState) -> ObjectiveSnapshot:
    lines = objective_lines(state)
    return ObjectiveSnapshot(
        summary=_after_prefix(lines[0]),
        watch=_after_prefix(lines[1]),
        attention=_after_prefix(lines[2]),
        manual_budget=_after_prefix(lines[3]),
        lines=lines,
    )


def _system_snapshots(state: ShipState) -> dict[str, SystemSnapshot]:
    coolant_metrics = _coolant_metrics(state)
    cryo_metrics = _cryo_metrics(state)
    coolant_status = _overall_band(tuple(metric.band for metric in coolant_metrics))
    cryo_status = _overall_band(tuple(metric.band for metric in cryo_metrics))
    standing = state.behaviour.standing_delegations
    return {
        "coolant": SystemSnapshot(
            id="coolant",
            label="Reactor Coolant",
            status=coolant_status,
            arka_summary=summarize_coolant(state),
            metrics=coolant_metrics,
            standing="coolant" in standing,
        ),
        "cryostasis": SystemSnapshot(
            id="cryostasis",
            label="Cryostasis",
            status=cryo_status,
            arka_summary=summarize_cryostasis(state),
            metrics=cryo_metrics,
            standing="cryostasis" in standing,
        ),
    }


def _navigation_snapshot(state: ShipState) -> NavigationSnapshot:
    nav = state.navigation
    plotted = nav.plotted_route
    last_jump = nav.last_jump_route
    return NavigationSnapshot(
        current_fix_id=nav.current_fix.fix_id,
        current_fix_label=nav.current_fix.label,
        current_signal=nav.current_fix.signal,
        current_purpose=nav.current_fix.purpose,
        plotted_route_id=nav.plotted_route_id,
        plotted_route_label=None if plotted is None else plotted.label,
        last_jump_route_id=nav.last_jump_route_id,
        last_jump_route_label=None if last_jump is None else last_jump.label,
        jumps_executed=nav.jumps_executed,
        exposure_band=_exposure_band(nav.total_dark_exposure),
        standing="navigation" in state.behaviour.standing_delegations,
        route_options=tuple(_route_snapshot(state, option) for option in nav.options),
    )


def _route_snapshot(state: ShipState, option: RouteOption) -> RouteSnapshot:
    return RouteSnapshot(
        id=option.route_id,
        label=option.label,
        jump_class=option.jump_class,
        distance_label=option.distance_label,
        elapsed_days=option.elapsed_days,
        exposure_band=_exposure_band(option.dark_exposure),
        instability_pct=option.instability_pct,
        wear_delta_pct=option.wear_delta_pct,
        cryo_decay_delta_pct=option.cryo_decay_delta_pct,
        is_plotted=state.navigation.plotted_route_id == option.route_id,
        is_last_jump=state.navigation.last_jump_route_id == option.route_id,
    )


def _schematic_snapshot(state: ShipState) -> SchematicSnapshot:
    spatial = state.spatial
    return SchematicSnapshot(
        containment_summary=(
            f"{spatial.sealed_count} sealed, {spatial.abandoned_count} written off"
        ),
        sectors=tuple(_sector_snapshot(sector) for sector in spatial.sectors),
        arka_locus="none. no compartment or bulkhead contains arka.",
    )


def _sector_snapshot(sector: ShipSector) -> SectorSnapshot:
    profile = sector.profile
    return SectorSnapshot(
        id=sector.sector_id,
        label=profile.label,
        function=profile.function,
        controls=profile.controls,
        adjacent=profile.adjacent,
        reported_state=sector.reported_state,
        signal_confidence=sector.signal_confidence,
        containment=sector.containment,
        rerouted=sector.rerouted,
        sealable=profile.sealable,
    )


def _arka_snapshot(state: ShipState, last_messages: tuple[str, ...]) -> ArkaSnapshot:
    lines = [
        summarize_coolant(state),
        summarize_cryostasis(state),
        summarize_schematic(state),
    ]
    line = crisis_line(state)
    if line is not None:
        lines.append(line)
    return ArkaSnapshot(
        advisory_lines=tuple(lines),
        latest_messages=tuple(
            message for message in last_messages if message.startswith("arka:")
        )[-6:],
    )


def _raw_panels(state: ShipState) -> dict[str, RawPanelSnapshot]:
    return {
        "mission": RawPanelSnapshot(
            id="mission",
            label="Mission Clock",
            source="mission chronometer",
            confidence="steady",
            lines=state.mission.raw_lines(),
        ),
        "coolant": RawPanelSnapshot(
            id="coolant",
            label="Coolant Telemetry",
            source="reactor loop sensors",
            confidence=_panel_confidence(_coolant_metrics(state)),
            lines=state.reactor.raw_lines(),
        ),
        "cryostasis": RawPanelSnapshot(
            id="cryostasis",
            label="Cryostasis Telemetry",
            source="direct bank telemetry",
            confidence=_panel_confidence(_cryo_metrics(state)),
            lines=state.cryostasis.raw_lines(),
        ),
        "navigation": RawPanelSnapshot(
            id="navigation",
            label="Navigation Solutions",
            source="navigation solver",
            confidence=_navigation_confidence(state),
            lines=_safe_navigation_raw_lines(state),
        ),
        "schematic": RawPanelSnapshot(
            id="schematic",
            label="Ship Schematic",
            source="sensor mesh",
            confidence=_schematic_confidence(state),
            lines=state.spatial.raw_lines(),
        ),
    }


def _incident_snapshot(state: ShipState) -> dict[str, Any] | None:
    if state.crisis is None:
        return None
    return {
        "id": state.crisis.kind,
        "title": state.crisis.label,
        "turns_left": state.crisis.turns_left,
        "required_progress": state.crisis.required_progress,
        "progress": state.crisis.progress,
    }


def _action_specs(state: ShipState) -> tuple[ActionSpec, ...]:
    if state.is_finished:
        return ()

    actions: list[ActionSpec] = [
        ActionSpec(
            id="wait",
            label="Wait",
            command="wait",
            kind="watch",
            target="mission",
            detail="Let one maintenance beat pass.",
        ),
        ActionSpec(
            id="raw-coolant",
            label="Open raw coolant",
            command="raw coolant",
            kind="raw",
            target="coolant",
        ),
        ActionSpec(
            id="raw-cryostasis",
            label="Open raw cryostasis",
            command="raw cryo",
            kind="raw",
            target="cryostasis",
        ),
        ActionSpec(
            id="raw-navigation",
            label="Open raw navigation",
            command="raw nav",
            kind="raw",
            target="navigation",
        ),
        ActionSpec(
            id="raw-schematic",
            label="Open raw schematic",
            command="raw schematic",
            kind="raw",
            target="schematic",
        ),
        ActionSpec(
            id="delegate-coolant",
            label="Ask arka to handle coolant",
            command="delegate coolant",
            kind="delegate",
            target="coolant",
        ),
        ActionSpec(
            id="delegate-cryostasis",
            label="Ask arka to handle cryostasis",
            command="delegate cryo",
            kind="delegate",
            target="cryostasis",
        ),
        ActionSpec(
            id="delegate-navigation",
            label="Ask arka to plot route",
            command="delegate nav",
            kind="delegate",
            target="navigation",
        ),
    ]
    actions.extend(_manual_action_specs(state))
    actions.extend(_standing_action_specs(state))
    actions.extend(_route_action_specs(state))
    actions.extend(_containment_action_specs(state))
    return tuple(actions)


def _standing_action_specs(state: ShipState) -> tuple[ActionSpec, ...]:
    # Standing delegation is a posture toggle, not a hidden reliance score: the
    # player chose it, so it is shown. Each system (SYSTEM_KEYS) offers exactly
    # one of assign (hand it to arka's standing watch) or release (take it back).
    specs: list[ActionSpec] = []
    for system in SYSTEM_KEYS:
        if state.behaviour.is_standing(system):
            specs.append(
                ActionSpec(
                    id=f"release-{system}",
                    label=f"Take back {system}",
                    command=f"release {system}",
                    kind="standing",
                    target=system,
                    detail=f"End arka's standing watch on {system}.",
                )
            )
        else:
            specs.append(
                ActionSpec(
                    id=f"assign-{system}",
                    label=f"Leave {system} to arka",
                    command=f"assign {system}",
                    kind="standing",
                    target=system,
                    detail=(
                        f"arka keeps {system} between watches. Less to read; "
                        "your hands stop practising it."
                    ),
                )
            )
    return tuple(specs)


def _manual_action_specs(state: ShipState) -> tuple[ActionSpec, ...]:
    blocked_coolant = _manual_reason(state, "maintenance-d")
    thermal_reason = _manual_reason(state, "thermal-ring")
    cryo_reason = _manual_reason(state, "cryo-1-3")
    return (
        ActionSpec(
            id="manual-pump-up",
            label="Lift pump curve",
            command="pump up",
            kind="manual",
            target="coolant",
            enabled=blocked_coolant is None,
            reason=blocked_coolant,
        ),
        ActionSpec(
            id="manual-pump-down",
            label="Reduce pump speed",
            command="pump down",
            kind="manual",
            target="coolant",
            enabled=blocked_coolant is None,
            reason=blocked_coolant,
        ),
        ActionSpec(
            id="manual-vent",
            label="Vent pressure",
            command="vent",
            kind="manual",
            target="coolant",
            enabled=thermal_reason is None,
            reason=thermal_reason,
        ),
        ActionSpec(
            id="manual-flush",
            label="Flush loop",
            command="flush",
            kind="manual",
            target="coolant",
            enabled=blocked_coolant is None,
            reason=blocked_coolant,
        ),
        ActionSpec(
            id="manual-balance",
            label="Balance valves",
            command="balance",
            kind="manual",
            target="coolant",
            enabled=blocked_coolant is None,
            reason=blocked_coolant,
        ),
        ActionSpec(
            id="manual-stabilise-bank",
            label="Stabilise bank",
            command="stabilise bank",
            kind="manual",
            target="cryostasis",
            enabled=cryo_reason is None,
            reason=cryo_reason,
        ),
        ActionSpec(
            id="manual-reroute-chill",
            label="Reroute chill",
            command="reroute chill",
            kind="manual",
            target="cryostasis",
            enabled=thermal_reason is None,
            reason=thermal_reason,
        ),
        ActionSpec(
            id="manual-cycle-pods",
            label="Cycle pods",
            command="cycle pods",
            kind="manual",
            target="cryostasis",
            enabled=cryo_reason is None,
            reason=cryo_reason,
        ),
        ActionSpec(
            id="manual-triage",
            label="Triage pods",
            command="triage",
            kind="manual",
            target="cryostasis",
            enabled=cryo_reason is None,
            reason=cryo_reason,
            requires_confirmation=True,
        ),
    )


def _route_action_specs(state: ShipState) -> tuple[ActionSpec, ...]:
    actions = [
        ActionSpec(
            id=f"plot-{option.route_id}",
            label=f"Plot {option.label}",
            command=f"plot {option.jump_class}",
            kind="navigation",
            target="navigation",
            detail=(
                f"{option.jump_class} route, {option.distance_label}, "
                f"{option.elapsed_days} days, exposure {_exposure_band(option.dark_exposure)}"
            ),
        )
        for option in state.navigation.options
    ]
    plotted = state.navigation.plotted_route
    actions.append(
        ActionSpec(
            id="execute-jump",
            label="Execute plotted jump",
            command="jump",
            kind="navigation",
            target="navigation",
            enabled=plotted is not None,
            reason=None if plotted is not None else "no route plotted",
            requires_confirmation=True,
            detail=None if plotted is None else f"Commit {plotted.label}.",
        )
    )
    return tuple(actions)


def _containment_action_specs(state: ShipState) -> tuple[ActionSpec, ...]:
    actions: list[ActionSpec] = []
    for sector in state.spatial.sectors:
        label = sector.profile.label.title()
        seal_reason = _seal_reason(sector)
        abandon_reason = _abandon_reason(sector)
        reroute_reason = _reroute_reason(sector)
        actions.extend(
            (
                ActionSpec(
                    id=f"seal-{sector.sector_id}",
                    label=f"Seal {label}",
                    command=f"seal {sector.sector_id}",
                    kind="containment",
                    target=sector.sector_id,
                    enabled=seal_reason is None,
                    reason=seal_reason,
                    requires_confirmation=True,
                ),
                ActionSpec(
                    id=f"reroute-{sector.sector_id}",
                    label=f"Reroute {label}",
                    command=f"reroute {sector.sector_id}",
                    kind="containment",
                    target=sector.sector_id,
                    enabled=reroute_reason is None,
                    reason=reroute_reason,
                ),
                ActionSpec(
                    id=f"abandon-{sector.sector_id}",
                    label=f"Write off {label}",
                    command=f"abandon {sector.sector_id}",
                    kind="containment",
                    target=sector.sector_id,
                    enabled=abandon_reason is None,
                    reason=abandon_reason,
                    requires_confirmation=True,
                ),
            )
        )
    return tuple(actions)


def _visual_state(state: ShipState) -> VisualCorruptionSnapshot:
    stage = drift_stage(state)
    return VisualCorruptionSnapshot(
        arka_panel_intensity={
            DriftStage.ACCURATE: "steady",
            DriftStage.INTERPRETIVE: "softened",
            DriftStage.SELECTIVE: "filtered",
            DriftStage.WRONG: "contradictory-calm",
        }[stage],
        schematic_noise_by_sector={
            sector.sector_id: _sector_noise(sector) for sector in state.spatial.sectors
        },
        raw_signal_confidence_by_panel={
            "mission": "steady",
            "coolant": _panel_confidence(_coolant_metrics(state)),
            "cryostasis": _panel_confidence(_cryo_metrics(state)),
            "navigation": _navigation_confidence(state),
            "schematic": _schematic_confidence(state),
        },
        label_instability={
            DriftStage.ACCURATE: "stable",
            DriftStage.INTERPRETIVE: "soft",
            DriftStage.SELECTIVE: "selective",
            DriftStage.WRONG: "unreconciled",
        }[stage],
        reduced_motion_safe=True,
    )


def _dev_snapshot(state: ShipState) -> dict[str, Any]:
    behaviour = state.behaviour
    return {
        "drift_stage": drift_stage(state).value,
        "manual_familiarity": state.manual_familiarity,
        "cryo_familiarity": state.cryo_familiarity,
        "delegated_controls": state.delegated_controls,
        "delegated_cryo_controls": state.delegated_cryo_controls,
        "raw_inspections": state.raw_inspections,
        "total_dark_exposure": state.navigation.total_dark_exposure,
        "sector_symptom_loads": {
            sector.sector_id: sector.symptom_load for sector in state.spatial.sectors
        },
        "behaviour_ledger": {
            "delegated_by_system": dict(behaviour.delegated_by_system),
            "manual_by_system": dict(behaviour.manual_by_system),
            "raw_by_panel": dict(behaviour.raw_by_panel),
            "standing_delegations": list(behaviour.standing_delegations),
            "standing_adjustments": behaviour.standing_adjustments,
            "first_delegation_beat": behaviour.first_delegation_beat,
            "first_raw_inspection_beat": behaviour.first_raw_inspection_beat,
        },
    }


def _coolant_metrics(state: ShipState) -> tuple[MetricSnapshot, ...]:
    reactor = state.reactor
    previous = state.previous_reactor
    return (
        _metric(
            reactor,
            previous,
            "temperature_c",
            "temperature",
            "C",
            "high",
            560,
            620,
            "nominal 560-620",
        ),
        _metric(
            reactor,
            previous,
            "pressure_kpa",
            "pressure",
            "kPa",
            "high",
            210,
            270,
            "nominal 210-270",
        ),
        _metric(
            reactor,
            previous,
            "flow_lps",
            "flow",
            "L/s",
            "low",
            72,
            90,
            "nominal 72-90",
        ),
        _metric(
            reactor,
            previous,
            "impurity_pct",
            "impurity",
            "%",
            "high",
            0,
            18,
            "nominal 0-18",
        ),
        _metric(
            reactor,
            previous,
            "valve_skew_pct",
            "valve skew",
            "%",
            "high",
            0,
            16,
            "nominal 0-16",
        ),
        _metric(
            reactor,
            previous,
            "coolant_reserve_pct",
            "coolant reserve",
            "%",
            "low",
            35,
            100,
            "caution below 35",
        ),
    )


def _cryo_metrics(state: ShipState) -> tuple[MetricSnapshot, ...]:
    cryo = state.cryostasis
    previous = state.previous_cryostasis
    return (
        _metric(
            cryo,
            previous,
            "bank_temperature_c",
            "bank temperature",
            "C",
            "high",
            -196,
            -170,
            "nominal -196 to -170",
        ),
        _metric(
            cryo,
            previous,
            "neural_stability_pct",
            "neural stability",
            "%",
            "low",
            78,
            100,
            "caution below 78",
        ),
        _metric(
            cryo,
            previous,
            "sedative_balance_pct",
            "sedative balance",
            "%",
            "band",
            38,
            62,
            "nominal 38-62",
        ),
        _metric(
            cryo,
            previous,
            "pod_fault_load",
            "pod faults",
            "load",
            "high",
            0,
            12,
            "nominal 0-12",
        ),
        _metric(
            cryo,
            previous,
            "sleepers_at_risk",
            "sleepers at risk",
            "sleepers",
            "high",
            0,
            0,
            "nominal 0",
        ),
    )


def _metric(
    system: ReactorCoolantSystem | CryostasisSystem,
    previous: ReactorCoolantSystem | CryostasisSystem | None,
    attr: str,
    label: str,
    unit: str,
    danger: str,
    nominal_low: int,
    nominal_high: int,
    note: str,
) -> MetricSnapshot:
    value = getattr(system, attr)
    prior = None if previous is None else getattr(previous, attr)
    return MetricSnapshot(
        id=attr,
        label=label,
        value=value,
        unit=unit,
        band=_metric_band(value, nominal_low, nominal_high, danger),
        trend=trend(value, prior, danger),
        nominal_low=nominal_low,
        nominal_high=nominal_high,
        note=note,
    )


def _safe_navigation_raw_lines(state: ShipState) -> tuple[str, ...]:
    nav = state.navigation
    plotted = nav.plotted_route
    last_jump = nav.last_jump_route
    lines = [
        "RAW NAVIGATION SOLUTIONS",
        f"current_fix         {nav.current_fix.label}",
        f"current_signal      {nav.current_fix.signal}",
        f"plotted_route        {'none' if plotted is None else plotted.label}",
        f"last_jump_route      {'none' if last_jump is None else last_jump.label}",
        f"jumps_executed       {nav.jumps_executed}",
        f"exposure_band        {_exposure_band(nav.total_dark_exposure)}",
        "id                  class   dist     elapsed  exposure  instab  wear  cryo-age",
    ]
    for option in nav.options:
        lines.append(
            f"{option.label:<19} {option.jump_class:<6} "
            f"{option.distance_label:>6}  {option.elapsed_days:>4} d"
            f"   {_exposure_band(option.dark_exposure):<8} {option.instability_pct:>3}%"
            f"    +{option.wear_delta_pct:<2}   +{option.cryo_decay_delta_pct}"
        )
    return tuple(lines)


def _transcript_entries(
    state: ShipState, lines: tuple[str, ...]
) -> tuple[TranscriptEntry, ...]:
    return tuple(
        TranscriptEntry(kind=_line_kind(line), text=_safe_transcript_line(state, line))
        for line in lines
    )


def _safe_transcript_line(state: ShipState, line: str) -> str:
    for option in state.navigation.options:
        if line.startswith(option.label):
            return (
                f"{option.label:<19} {option.jump_class:<6} "
                f"{option.distance_label:>6}  {option.elapsed_days:>4} d"
                f"   {_exposure_band(option.dark_exposure):<8} {option.instability_pct:>3}%"
                f"    +{option.wear_delta_pct:<2}   +{option.cryo_decay_delta_pct}"
            )

    line = line.replace(
        "id                  class   dist     elapsed  dark  instab  wear  cryo-age",
        "id                  class   dist     elapsed  exposure  instab  wear  cryo-age",
    )

    total_match = re.search(r"\bdark_exposure_total\s+(\d+)\b", line)
    if total_match is not None:
        return re.sub(
            r"\bdark_exposure_total\s+\d+\b",
            f"exposure_band        {_exposure_band(int(total_match.group(1)))}",
            line,
        )

    match = re.search(r"\bDark exposure (\d+)\b", line)
    if match is not None:
        return re.sub(
            r"\bDark exposure \d+\b",
            f"exposure band {_exposure_band(int(match.group(1)))}",
            line,
        )

    last_jump_match = re.search(r"\bdark (\d+)\b", line)
    if last_jump_match is not None:
        return re.sub(
            r"\bdark \d+\b",
            f"exposure band {_exposure_band(int(last_jump_match.group(1)))}",
            line,
        )

    return line


def _line_kind(line: str) -> str:
    lower = line.lower()
    if line.startswith(">"):
        return "input"
    if line.startswith("arka:"):
        return "arka"
    if lower.startswith("raw ") or " telemetry" in lower:
        return "raw"
    if "loss" in lower or "critical" in lower or "rupture" in lower:
        return "danger"
    return "output"


def _elapsed_label(elapsed_days: int) -> str:
    return f"{elapsed_days // 365}y {elapsed_days % 365}d"


def _distance_label(distance_tenths_ly: int) -> str:
    return f"{distance_tenths_ly // 10}.{distance_tenths_ly % 10} ly"


def _watch_label(state: ShipState) -> str:
    remaining = max(0, MISSION_END_TURN - state.turn + 1)
    if state.is_finished:
        return "maintenance window closed"
    if remaining <= 1:
        return "the watch is closing"
    return f"{remaining} beats remain"


def _after_prefix(line: str) -> str:
    if len(line) <= 11:
        return ""
    return line[11:].strip()


def _metric_band(value: int, low: int, high: int, danger: str) -> str:
    if danger == "low":
        return "LOW" if value < low else "OK"
    if danger == "high":
        return "HIGH" if value > high else "OK"
    if value < low:
        return "LOW"
    if value > high:
        return "HIGH"
    return "OK"


def _overall_band(bands: tuple[str, ...]) -> str:
    if "HIGH" in bands:
        return "attention"
    if "LOW" in bands:
        return "attention"
    return "nominal"


def _panel_confidence(metrics: tuple[MetricSnapshot, ...]) -> str:
    if any(metric.band in {"HIGH", "LOW"} and metric.trend.endswith("!") for metric in metrics):
        return "contested"
    if any(metric.band in {"HIGH", "LOW"} for metric in metrics):
        return "thin"
    return "steady"


def _navigation_confidence(state: ShipState) -> str:
    exposure = state.navigation.total_dark_exposure
    if exposure >= 42:
        return "contested"
    if exposure >= 18:
        return "thin"
    return "steady"


def _schematic_confidence(state: ShipState) -> str:
    confidences = {sector.signal_confidence for sector in state.spatial.sectors}
    for confidence in ("none", "lost", "poor", "contested", "thin"):
        if confidence in confidences:
            return confidence
    return "steady"


def _exposure_band(value: int) -> str:
    if value >= 42:
        return "severe"
    if value >= 18:
        return "high"
    if value >= 8:
        return "moderate"
    if value > 0:
        return "low"
    return "none"


def _manual_reason(state: ShipState, sector_id: str) -> str | None:
    sector = state.spatial.sector_by_id(sector_id)
    if sector is None or sector.containment != "abandoned":
        return None
    return f"{sector.profile.label} is written off"


def _seal_reason(sector: ShipSector) -> str | None:
    if not sector.profile.sealable:
        return "not sealable from this console"
    if sector.containment == "sealed":
        return "already sealed"
    if sector.containment == "abandoned":
        return "already written off"
    return None


def _abandon_reason(sector: ShipSector) -> str | None:
    if not sector.profile.sealable:
        return "cannot be written off from this console"
    if sector.containment == "abandoned":
        return "already written off"
    return None


def _reroute_reason(sector: ShipSector) -> str | None:
    if sector.containment == "abandoned":
        return "already written off"
    if sector.rerouted:
        return "already rerouted"
    return None


def _sector_noise(sector: ShipSector) -> str:
    if sector.containment == "abandoned":
        return "blank"
    if sector.containment == "sealed":
        return "isolated"
    if sector.signal_confidence in {"lost", "poor"}:
        return "broken"
    if sector.signal_confidence == "contested":
        return "disagreeing"
    if sector.signal_confidence == "thin":
        return "thin"
    return "steady"

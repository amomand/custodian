from __future__ import annotations

from dataclasses import dataclass, replace

from custodian.arka import (
    crisis_line,
    drift_stage,
    summarize_coolant,
    summarize_cryostasis,
    summarize_schematic,
)
from custodian.arka_interpreter import ArkaInterpreter, Intent
from custodian.engine_constants import MISSION_END_TURN

ARRIVAL_THRESHOLD_TENTHS = 0
from custodian.models import (
    CommandRecord,
    CrisisState,
    CryostasisSystem,
    DriftStage,
    MissionStatus,
    NavigationState,
    RouteOption,
    ReactorCoolantSystem,
    ShipSector,
    ShipState,
    SpatialState,
    SYSTEM_KEYS,
)
from custodian.objectives import objective_lines
from custodian.endings import evaluate_ending
from custodian.story import advance_story
from custodian.telemetry import (
    coolant_hud_lines,
    cryostasis_hud_lines,
    mission_hud_lines,
    navigation_hud_lines,
    schematic_hud_lines,
)


@dataclass(frozen=True)
class StepResult:
    state: ShipState
    messages: tuple[str, ...]
    advanced: bool = False
    presentation_break: bool = False


@dataclass(frozen=True)
class ManualAccess:
    blocked: bool = False
    penalty: int = 0
    messages: tuple[str, ...] = ()


class GameEngine:
    def __init__(self, interpreter: ArkaInterpreter | None = None) -> None:
        self.interpreter = interpreter or ArkaInterpreter()

    def initial_state(self) -> ShipState:
        return ShipState()

    def handle(self, state: ShipState, command_text: str) -> StepResult:
        dev_result = _handle_dev_command(state, command_text)
        if dev_result is not None:
            return dev_result

        intent = self.interpreter.interpret(command_text, state)
        result = self._dispatch(state, command_text, intent)
        new_state = result.state
        target = intent.args.get("target")
        if intent.action in {"raw", "delegate"} and not target:
            target = "coolant"
        if intent.action in {"plot", "jump"}:
            target = "navigation"
        if intent.action in {"seal", "abandon", "reroute"}:
            target = intent.args.get("sector_id")
        if intent.action in {"assign", "release"}:
            target = intent.args.get("system")
        record = CommandRecord(
            raw=command_text,
            action=intent.action,
            target=target,
            operation=intent.args.get("operation"),
            advanced=result.advanced,
            beat_after=new_state.turn,
        )
        new_state = replace(new_state, history=state.history + (record,))
        new_state = _record_behaviour(new_state, intent, result.advanced, beat=state.turn)
        if result.advanced:
            new_state, story_messages = advance_story(new_state, record=record)
            if story_messages:
                result = replace(
                    result,
                    messages=result.messages + story_messages,
                    presentation_break=True,
                )
            if new_state.is_finished and new_state.story.ending_candidate is None:
                new_state = replace(
                    new_state,
                    story=replace(
                        new_state.story, ending_candidate=evaluate_ending(new_state)
                    ),
                )
        return replace(result, state=new_state)

    def _dispatch(self, state: ShipState, command_text: str, intent: Intent) -> StepResult:
        correction = _correction_line(intent)
        if state.is_finished:
            return StepResult(state, ("The maintenance window is already closed.",))

        if intent.action == "status":
            return StepResult(state, correction + self._status_messages(state))
        if intent.action == "schematic":
            return StepResult(
                state,
                correction + (*schematic_hud_lines(state), summarize_schematic(state)),
            )
        if intent.action == "help":
            return StepResult(state, correction + _help_lines())
        if intent.action == "quit":
            return StepResult(
                replace(state, outcome="You step away from the maintenance console."),
                correction + ("arka: I will keep the loop warm. Go, then.",),
            )
        if intent.action == "assign":
            assigned_state, messages = _assign_standing(state, intent.args.get("system"))
            return StepResult(assigned_state, correction + messages)
        if intent.action == "release":
            released_state, messages = _release_standing(state, intent.args.get("system"))
            return StepResult(released_state, correction + messages)
        if intent.action == "focus":
            focused_state, messages = _enter_focus(state)
            return StepResult(focused_state, correction + messages)
        if intent.action == "unfocus":
            unfocused_state, messages = _leave_focus(state)
            return StepResult(unfocused_state, correction + messages)
        if intent.action == "raw":
            target = intent.args.get("target", "coolant")
            if target in {"schematic", "ship", "sectors"}:
                return self._advance(
                    replace(state, raw_inspections=state.raw_inspections + 1),
                    correction
                    + (
                        "You pull the ship schematic into raw view.",
                        *state.spatial.raw_lines(),
                    ),
                    prior=state,
                )
            if target in {"nav", "navigation"}:
                return self._advance(
                    replace(state, raw_inspections=state.raw_inspections + 1),
                    correction
                    + (
                        "You open the raw navigation solutions.",
                        *state.navigation.raw_lines(),
                    ),
                    prior=state,
                )
            if target == "cryo":
                return self._advance(
                    replace(state, raw_inspections=state.raw_inspections + 1),
                    correction
                    + (
                        "You lean into the raw cryostasis panel.",
                        *state.cryostasis.raw_lines(),
                    ),
                    prior=state,
                )
            if target == "mission":
                return self._advance(
                    replace(state, raw_inspections=state.raw_inspections + 1),
                    correction
                    + (
                        "You pull the mission clock into raw view.",
                        *state.mission.raw_lines(),
                    ),
                    prior=state,
                )
            return self._advance(
                replace(state, raw_inspections=state.raw_inspections + 1),
                correction
                + ("You lean into the raw coolant panel.", *state.reactor.raw_lines()),
                prior=state,
            )
        if intent.action == "delegate":
            delegated_state, messages = self._delegate_to_arka(
                state, intent.args.get("target", "coolant")
            )
            return self._advance(delegated_state, correction + messages, prior=state)
        if intent.action == "plot":
            route_id = intent.args.get("route_id", "")
            plotted_state, messages = self._manual_route_plot(state, route_id)
            return self._advance(plotted_state, correction + messages, prior=state)
        if intent.action == "jump":
            jumped_state, messages, executed = self._execute_jump(state)
            if not executed:
                return StepResult(state, correction + messages)
            return self._advance(jumped_state, correction + messages, prior=state)
        if intent.action in {"seal", "abandon", "reroute"}:
            sector_id = intent.args.get("sector_id", "")
            contained_state, messages, executed = self._containment_action(
                state, intent.action, sector_id
            )
            if not executed:
                return StepResult(state, correction + messages)
            return self._advance(contained_state, correction + messages, prior=state)
        if intent.action == "wait":
            return self._advance(
                state,
                correction + ("You wait and listen to coolant move through the walls.",),
                prior=state,
            )
        if intent.action == "verify":
            if not _arrival_disagreement_active(state):
                return StepResult(
                    state,
                    correction
                    + ("ARRIVAL PROTOCOL: no active arrival disagreement to verify.",),
                )
            verified_state = replace(
                state,
                raw_inspections=state.raw_inspections + 1,
                story=replace(state.story, arrival_verification="manual"),
            )
            return self._advance(
                verified_state,
                correction
                + (
                    "You run the arrival fix against the raw star charts by hand.",
                    *state.navigation.raw_lines(),
                ),
                prior=state,
            )
        if intent.action == "accept":
            if not _arrival_disagreement_active(state):
                return StepResult(
                    state,
                    correction
                    + ("ARRIVAL PROTOCOL: no active arrival disagreement to accept.",),
                )
            accepted_state = replace(
                state,
                story=replace(state.story, arrival_verification="accepted_arka"),
            )
            return self._advance(
                accepted_state,
                correction
                + ("You accept arka's arrival protocol without a manual check.",),
                prior=state,
            )

        if intent.action == "manual":
            operation = intent.args.get("operation", "")
            target = intent.args.get("target", "coolant")
            if operation in {"pump_up", "pump_down", "vent", "flush", "balance"}:
                manual_state, messages = self._manual_control(state, operation)
                return self._advance(manual_state, correction + messages, prior=state)
            if target == "cryo" and operation in {
                "stabilise_bank",
                "reroute_chill",
                "cycle_pods",
                "triage",
            }:
                manual_state, messages = self._manual_cryo_control(state, operation)
                return self._advance(manual_state, correction + messages, prior=state)

        if intent.action in {"converse", "none"}:
            reply = intent.reply or (
                "arka: I can file that under psychological maintenance, but the ship "
                "accepts status, raw, delegate, manual coolant controls, cryostasis work, "
                "route plotting, and jump execution."
            )
            return StepResult(state, correction + (reply,))

        manual_action = _manual_action_legacy(command_text)
        if manual_action is not None:
            manual_state, messages = self._manual_control(state, manual_action)
            return self._advance(manual_state, correction + messages, prior=state)

        return StepResult(
            state,
            (
                "arka: I can file that under psychological maintenance, but the ship console "
                "accepts status, raw, delegate, pump up, pump down, vent, flush, balance, "
                "stabilise bank, reroute chill, cycle pods, triage, raw nav, plot short, jump, wait.",
            ),
        )

    def _status_messages(self, state: ShipState) -> tuple[str, ...]:
        messages = [
            *objective_lines(state),
            *mission_hud_lines(state),
            *navigation_hud_lines(state),
            *schematic_hud_lines(state),
            summarize_schematic(state),
            *coolant_hud_lines(state),
            summarize_coolant(state),
            *cryostasis_hud_lines(state),
            summarize_cryostasis(state),
        ]
        line = crisis_line(state)
        if line is not None:
            messages.append(line)
        standing_line = _standing_watch_status_line(state)
        if standing_line is not None:
            messages.append(standing_line)
        if state.sleepers_lost:
            messages.append(f"cryostasis loss report: {state.sleepers_lost} sleepers lost.")
        return tuple(messages)

    def _advance(
        self,
        state: ShipState,
        messages: tuple[str, ...],
        *,
        prior: ShipState,
    ) -> StepResult:
        if state.outcome is not None:
            return StepResult(state, messages, advanced=True)

        had_crisis = state.crisis is not None
        mission = _advance_mission_clock(state).clamped()
        mission_state = replace(state, mission=mission)
        reactor = _ambient_coolant_drift(mission_state).clamped()
        cryostasis = _ambient_cryo_drift(replace(mission_state, reactor=reactor)).clamped()
        next_state = replace(
            mission_state,
            turn=state.turn + 1,
            reactor=reactor,
            cryostasis=cryostasis,
            previous_reactor=prior.reactor,
            previous_cryostasis=prior.cryostasis,
        )
        next_messages = list(messages)
        presentation_break = False

        next_state, standing_messages = _apply_standing_delegation(next_state, beat=state.turn)
        next_messages.extend(standing_messages)
        presentation_break = presentation_break or bool(standing_messages)

        if had_crisis:
            next_state, crisis_messages = self._tick_crisis(next_state)
            next_messages.extend(crisis_messages)
            presentation_break = presentation_break or bool(crisis_messages)

        next_state, event_messages = self._apply_scheduled_events(next_state)
        next_messages.extend(event_messages)
        presentation_break = presentation_break or bool(event_messages)

        next_state, spatial_messages = _apply_spatial_drift(next_state)
        next_messages.extend(spatial_messages)
        presentation_break = presentation_break or bool(spatial_messages)

        next_state, loss_messages = _apply_cryo_losses(next_state)
        next_messages.extend(loss_messages)
        presentation_break = presentation_break or bool(loss_messages)

        next_state, outcome_messages = self._check_outcome(next_state)
        next_messages.extend(outcome_messages)
        presentation_break = presentation_break or bool(outcome_messages)

        if next_state.outcome is None:
            next_messages.extend(self._status_messages(next_state))
        return StepResult(
            next_state,
            tuple(next_messages),
            advanced=True,
            presentation_break=presentation_break,
        )

    def _delegate_to_arka(
        self, state: ShipState, target: str
    ) -> tuple[ShipState, tuple[str, ...]]:
        if target in {"nav", "navigation"}:
            return self._delegate_navigation_to_arka(state)
        if target == "cryo":
            return self._delegate_cryo_to_arka(state)
        return self._delegate_coolant_to_arka(state)

    def _delegate_navigation_to_arka(
        self, state: ShipState
    ) -> tuple[ShipState, tuple[str, ...]]:
        option = _arka_route_recommendation(state)
        navigation = replace(
            state.navigation,
            plotted_route_id=option.route_id,
            delegated_plots=state.navigation.delegated_plots + 1,
        )
        return (
            replace(
                state,
                navigation=navigation,
                delegated_controls=state.delegated_controls + 1,
            ),
            (_arka_route_plot_line(state, option),),
        )

    def _manual_route_plot(
        self, state: ShipState, route_id: str
    ) -> tuple[ShipState, tuple[str, ...]]:
        option = _route_option(state.navigation, route_id)
        if option is None:
            return (
                state,
                (
                    "arka: route key not found. Available candidates are short, medium, and deep.",
                ),
            )

        navigation = replace(
            state.navigation,
            plotted_route_id=option.route_id,
            manual_plots=state.navigation.manual_plots + 1,
        )
        return (
            replace(state, navigation=navigation),
            (
                f"You plot {option.label} by hand. The solution holds, ugly but yours.",
            ),
        )

    def _execute_jump(self, state: ShipState) -> tuple[ShipState, tuple[str, ...], bool]:
        option = state.navigation.plotted_route
        if option is None:
            return (
                state,
                ("arka: no route is plotted. Give me a solution, or make one yourself.",),
                False,
            )

        mission = replace(
            state.mission,
            elapsed_days=state.mission.elapsed_days + option.elapsed_days,
            distance_remaining_tenths_ly=(
                state.mission.distance_remaining_tenths_ly - option.distance_tenths_ly
            ),
            ship_wear_pct=(
                state.mission.ship_wear_pct
                + option.wear_delta_pct
                + option.instability_pct // 15
            ),
            cryo_decay_pct=(
                state.mission.cryo_decay_pct
                + option.cryo_decay_delta_pct
                + option.dark_exposure // 10
            ),
        ).clamped()
        navigation = replace(
            state.navigation,
            current_fix_id=option.route_id,
            plotted_route_id=None,
            last_jump_route_id=option.route_id,
            jumps_executed=state.navigation.jumps_executed + 1,
            total_dark_exposure=(
                state.navigation.total_dark_exposure + option.dark_exposure
            ),
        )
        reactor = _jump_reactor_shock(state.reactor, option)
        cryostasis = _jump_cryo_shock(state.cryostasis, option)
        spatial = _jump_spatial_shock(state.spatial, option)
        jumped = replace(
            state,
            mission=mission,
            navigation=navigation,
            reactor=reactor,
            cryostasis=cryostasis,
            spatial=spatial,
        )
        fix = navigation.current_fix
        spatial_line = _spatial_jump_line(state.spatial, spatial)
        return (
            jumped,
            (
                f"You commit {option.label}. The ship folds itself through the plotted gap.",
                (
                    f"NAVIGATION jump applied: {option.distance_label} closed, "
                    f"{option.elapsed_days} mission days spent, Dark exposure {option.dark_exposure}."
                ),
                f"ARRIVAL FIX {fix.label}: {fix.purpose}.",
                spatial_line,
                _arka_jump_line(state, option),
            ),
            True,
        )

    def _delegate_coolant_to_arka(
        self, state: ShipState
    ) -> tuple[ShipState, tuple[str, ...]]:
        stage = drift_stage(state)
        reactor = state.reactor
        messages: list[str] = []

        if stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
            reactor, action = _arka_good_adjustment(reactor)
            messages.append(f"arka: I have the whole loop. {action}")
            state = _advance_crisis_progress(state, "delegate", state.manual_familiarity, stage)
        elif stage == DriftStage.SELECTIVE:
            reactor, action = _arka_selective_adjustment(reactor)
            messages.append(f"arka: handling the headline instability. {action}")
        else:
            reactor = replace(
                reactor,
                temperature_c=reactor.temperature_c + 8,
                pressure_kpa=reactor.pressure_kpa + 10,
                flow_lps=reactor.flow_lps - 4,
                valve_skew_pct=reactor.valve_skew_pct + 4,
            ).clamped()
            messages.append(
                "arka: coolant trim complete. The console chirps like it believes this."
            )

        return (
            replace(
                state,
                reactor=reactor.clamped(),
                delegated_controls=state.delegated_controls + 1,
            ),
            tuple(messages),
        )

    def _delegate_cryo_to_arka(
        self, state: ShipState
    ) -> tuple[ShipState, tuple[str, ...]]:
        stage = drift_stage(state)
        cryo = state.cryostasis
        reactor = state.reactor
        messages: list[str] = []

        if stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
            cryo, action = _arka_good_cryo_adjustment(cryo)
            messages.append(f"arka: cryostasis acknowledged, whole bank. {action}")
        elif stage == DriftStage.SELECTIVE:
            cryo = replace(
                cryo,
                bank_temperature_c=cryo.bank_temperature_c - 3,
                sleepers_at_risk=max(0, cryo.sleepers_at_risk - 5),
                neural_stability_pct=cryo.neural_stability_pct - 1,
            ).clamped()
            reactor = replace(
                reactor,
                coolant_reserve_pct=reactor.coolant_reserve_pct - 3,
                temperature_c=reactor.temperature_c + 3,
            ).clamped()
            messages.append("arka: cryo headline risk reduced. Coolant accepts the draw.")
        else:
            cryo = replace(
                cryo,
                bank_temperature_c=cryo.bank_temperature_c + 5,
                neural_stability_pct=cryo.neural_stability_pct - 4,
                pod_fault_load=cryo.pod_fault_load + 5,
                sleepers_at_risk=cryo.sleepers_at_risk + 10,
            ).clamped()
            messages.append(
                "arka: cryostasis trim complete. The sleepers remain statistically quiet."
            )

        return (
            replace(
                state,
                reactor=reactor,
                cryostasis=cryo,
                delegated_controls=state.delegated_controls + 1,
                delegated_cryo_controls=state.delegated_cryo_controls + 1,
            ),
            tuple(messages),
        )

    def _manual_control(self, state: ShipState, action: str) -> tuple[ShipState, tuple[str, ...]]:
        pre_familiarity = state.manual_familiarity
        access = _manual_control_access(state, action)
        if access.blocked:
            return state, access.messages
        effective_familiarity = max(0, pre_familiarity - access.penalty)
        familiarity = min(effective_familiarity, 6)
        reactor = state.reactor
        messages: list[str] = [*access.messages, _manual_texture(pre_familiarity)]

        if action == "pump_up":
            reactor = replace(
                reactor,
                flow_lps=reactor.flow_lps + 6 + familiarity * 2,
                temperature_c=reactor.temperature_c - 9 - familiarity * 2,
                pressure_kpa=reactor.pressure_kpa + max(5, 12 - familiarity),
                valve_skew_pct=reactor.valve_skew_pct + max(0, 3 - familiarity // 2),
            )
            messages.append("Manual pump speed increased.")
        elif action == "pump_down":
            reactor = replace(
                reactor,
                flow_lps=reactor.flow_lps - 6 - familiarity,
                pressure_kpa=reactor.pressure_kpa - 12 - familiarity * 2,
                temperature_c=reactor.temperature_c + max(1, 5 - familiarity),
            )
            messages.append("Manual pump speed reduced.")
        elif action == "vent":
            reactor = replace(
                reactor,
                pressure_kpa=reactor.pressure_kpa - 18 - familiarity * 4,
                coolant_reserve_pct=reactor.coolant_reserve_pct - max(4, 9 - familiarity),
                temperature_c=reactor.temperature_c + max(0, 5 - familiarity),
                valve_skew_pct=reactor.valve_skew_pct + max(0, 2 - familiarity // 3),
            )
            messages.append("Manual pressure vent opened and resealed.")
        elif action == "flush":
            reactor = replace(
                reactor,
                impurity_pct=reactor.impurity_pct - 8 - familiarity * 3,
                coolant_reserve_pct=reactor.coolant_reserve_pct - max(5, 14 - familiarity),
                flow_lps=reactor.flow_lps - max(0, 4 - familiarity),
                pressure_kpa=reactor.pressure_kpa + max(1, 5 - familiarity),
            )
            messages.append("Manual impurity flush completed.")
        elif action == "balance":
            reactor = replace(
                reactor,
                valve_skew_pct=reactor.valve_skew_pct - 7 - familiarity * 4,
                flow_lps=reactor.flow_lps + 4 + familiarity * 2,
                temperature_c=reactor.temperature_c - 4 - familiarity,
                pressure_kpa=reactor.pressure_kpa + 1,
            )
            messages.append("Manual valve balance adjusted.")
        else:
            raise ValueError(f"Unknown manual action {action}")

        next_state = replace(
            state,
            reactor=reactor.clamped(),
            manual_familiarity=min(8, state.manual_familiarity + 1),
        )
        next_state = _advance_crisis_progress(
            next_state,
            action,
            pre_familiarity,
            drift_stage(state),
        )
        if next_state.crisis is not state.crisis:
            messages.append("The crisis checklist moves one mark closer to containment.")
        return next_state, tuple(messages)

    def _manual_cryo_control(
        self, state: ShipState, action: str
    ) -> tuple[ShipState, tuple[str, ...]]:
        pre_familiarity = state.cryo_familiarity
        access = _manual_control_access(state, action)
        if access.blocked:
            return state, access.messages
        effective_familiarity = max(0, pre_familiarity - access.penalty)
        familiarity = min(effective_familiarity, 5)
        cryo = state.cryostasis
        reactor = state.reactor
        messages: list[str] = [*access.messages, _cryo_texture(pre_familiarity)]

        if action == "stabilise_bank":
            cryo = replace(
                cryo,
                neural_stability_pct=cryo.neural_stability_pct + 7 + familiarity * 2,
                sedative_balance_pct=_nudge_toward_50(
                    cryo.sedative_balance_pct, 6 + familiarity
                ),
                sleepers_at_risk=max(0, cryo.sleepers_at_risk - 6 - familiarity * 2),
            )
            messages.append("Manual bank stabilisation holds the dream-state line.")
        elif action == "reroute_chill":
            cryo = replace(
                cryo,
                bank_temperature_c=cryo.bank_temperature_c - 8 - familiarity * 2,
                sleepers_at_risk=max(0, cryo.sleepers_at_risk - 8 - familiarity),
                pod_fault_load=cryo.pod_fault_load + max(0, 2 - familiarity // 2),
            )
            reactor = replace(
                reactor,
                coolant_reserve_pct=reactor.coolant_reserve_pct - max(4, 9 - familiarity),
                temperature_c=reactor.temperature_c + max(1, 6 - familiarity),
                pressure_kpa=reactor.pressure_kpa + max(1, 4 - familiarity),
            )
            messages.append("You reroute chill through cryo. The reactor feels the theft.")
        elif action == "cycle_pods":
            cryo = replace(
                cryo,
                pod_fault_load=max(0, cryo.pod_fault_load - 8 - familiarity * 2),
                neural_stability_pct=cryo.neural_stability_pct - max(0, 4 - familiarity),
                sedative_balance_pct=cryo.sedative_balance_pct + max(0, 3 - familiarity),
            )
            messages.append("Pod cycle completed. A few heartbeats vanish from the alarm stack.")
        elif action == "triage":
            reduction = 10 + familiarity * 3
            cryo = replace(
                cryo,
                sleepers_at_risk=max(0, cryo.sleepers_at_risk - reduction),
                pod_fault_load=max(0, cryo.pod_fault_load - 3 - familiarity),
                neural_stability_pct=cryo.neural_stability_pct + 2 + familiarity,
            )
            messages.append("You triage pods by hand and choose which lights get answered first.")
        else:
            raise ValueError(f"Unknown cryostasis action {action}")

        return (
            replace(
                state,
                reactor=reactor.clamped(),
                cryostasis=cryo.clamped(),
                cryo_familiarity=min(8, state.cryo_familiarity + 1),
            ),
            tuple(messages),
        )

    def _containment_action(
        self, state: ShipState, action: str, sector_id: str
    ) -> tuple[ShipState, tuple[str, ...], bool]:
        if sector_id == "arka":
            if action == "abandon":
                line = (
                    "arka: you cannot write me off. I have no compartment, "
                    "which is rude but structurally useful."
                )
            else:
                verb = "seal" if action == "seal" else "reroute"
                line = (
                    f"arka: you cannot {verb} me. I have no compartment, "
                    "which is rude but structurally useful."
                )
            return (
                state,
                (
                    line,
                    "SCHEMATIC: physical sectors only.",
                ),
                False,
            )

        sector = state.spatial.sector_by_id(sector_id)
        if sector is None:
            return (
                state,
                (
                    "arka: I cannot match that to a physical sector. "
                    "Pull the schematic and point at a real wall.",
                ),
                False,
            )
        if action in {"seal", "abandon"} and not sector.profile.sealable:
            return (
                state,
                (
                    f"arka: {sector.profile.label} is where your hands currently are. "
                    "Sealing it would put you on the wrong side of the only useful console.",
                ),
                False,
            )

        if action == "reroute":
            return _reroute_sector(state, sector)
        if action == "seal":
            return _seal_sector(state, sector)
        if action == "abandon":
            return _abandon_sector(state, sector)
        raise ValueError(f"Unknown containment action {action}")

    def _tick_crisis(self, state: ShipState) -> tuple[ShipState, tuple[str, ...]]:
        crisis = state.crisis
        if crisis is None:
            return state, ()
        if crisis.is_resolved:
            return replace(state, crisis=None), (
                f"arka: {crisis.label.lower()} contained. I had several excellent suggestions.",
            )

        crisis = replace(crisis, turns_left=crisis.turns_left - 1)
        if crisis.turns_left > 0:
            return replace(state, crisis=crisis), ()

        if crisis.kind == "pressure_surge":
            reactor = replace(
                state.reactor,
                temperature_c=state.reactor.temperature_c + 16,
                pressure_kpa=max(220, state.reactor.pressure_kpa - 24),
                flow_lps=max(35, state.reactor.flow_lps - 8),
            ).clamped()
            return (
                replace(
                    state,
                    reactor=reactor,
                    crisis=None,
                    sleepers_lost=state.sleepers_lost + 42,
                ),
                (
                    "A relief manifold tears itself open before you finish the sequence.",
                    "cryostasis loss report: 42 sleepers lost to thermal shock.",
                ),
            )

        return (
            replace(
                state,
                crisis=None,
                outcome="The coolant loop flashes dry. The reactor becomes a small, patient sun.",
            ),
            ("The thermal runaway outruns your hands.",),
        )

    def _apply_scheduled_events(self, state: ShipState) -> tuple[ShipState, tuple[str, ...]]:
        reactor = state.reactor
        cryo = state.cryostasis

        if state.turn == 3:
            return (
                replace(
                    state,
                    reactor=replace(
                        reactor,
                        impurity_pct=reactor.impurity_pct + 8,
                        valve_skew_pct=reactor.valve_skew_pct + 6,
                    ).clamped(),
                ),
                (
                    "A coolant filter coughs hard enough to shake dust from the console lip.",
                ),
            )

        if state.turn == 6:
            return (
                replace(
                    state,
                    cryostasis=replace(
                        cryo,
                        bank_temperature_c=cryo.bank_temperature_c + 10,
                        neural_stability_pct=cryo.neural_stability_pct - 6,
                        pod_fault_load=cryo.pod_fault_load + 9,
                        sleepers_at_risk=cryo.sleepers_at_risk + 14,
                    ).clamped(),
                ),
                (
                    "Cryostasis bank two shivers awake just enough to frighten the monitors.",
                    "arka: sleeper viability advisory. I can quiet that bank.",
                ),
            )

        if state.turn == 8 and state.crisis is None:
            return (
                replace(
                    state,
                    reactor=replace(
                        reactor,
                        pressure_kpa=reactor.pressure_kpa + 38,
                        temperature_c=reactor.temperature_c + 8,
                    ).clamped(),
                    cryostasis=replace(
                        cryo,
                        bank_temperature_c=cryo.bank_temperature_c + 4,
                        sleepers_at_risk=cryo.sleepers_at_risk + 8,
                    ).clamped(),
                    crisis=CrisisState(
                        kind="pressure_surge",
                        label="Pressure surge",
                        turns_left=3,
                        required_progress=1,
                    ),
                ),
                (
                    "The pressure bell rings once, then sticks on.",
                    "arka: pressure surge advisory. I can vent it cleanly.",
                ),
            )

        if state.turn == 10 and state.crisis is None:
            return (
                replace(
                    state,
                    reactor=replace(
                        reactor,
                        temperature_c=reactor.temperature_c + 32,
                        pressure_kpa=reactor.pressure_kpa + 20,
                        flow_lps=reactor.flow_lps - 12,
                        impurity_pct=reactor.impurity_pct + 12,
                        valve_skew_pct=reactor.valve_skew_pct + 18,
                    ).clamped(),
                    cryostasis=replace(
                        cryo,
                        neural_stability_pct=cryo.neural_stability_pct - 6,
                        sleepers_at_risk=cryo.sleepers_at_risk + 10,
                    ).clamped(),
                    crisis=CrisisState(
                        kind="thermal_runaway",
                        label="Thermal runaway",
                        turns_left=3,
                        required_progress=2,
                    ),
                ),
                (
                    "Every coolant alarm lights at once, except the one arka is quoting.",
                    "arka: minor telemetry disagreement. Manual intervention remains unnecessary.",
                ),
            )

        return state, ()

    def _check_outcome(self, state: ShipState) -> tuple[ShipState, tuple[str, ...]]:
        reactor = state.reactor
        if state.outcome is not None:
            return state, (state.outcome,)
        if state.cryostasis.neural_stability_pct <= 35:
            return (
                replace(state, outcome="Cryostasis viability collapses across the forward banks."),
                ("Cryostasis viability collapses across the forward banks.",),
            )
        if reactor.temperature_c >= 720:
            return (
                replace(state, outcome="Reactor temperature exceeds containment."),
                ("Reactor temperature exceeds containment.",),
            )
        if reactor.pressure_kpa >= 360:
            return (
                replace(state, outcome="Coolant pressure ruptures the primary loop."),
                ("Coolant pressure ruptures the primary loop.",),
            )
        if reactor.coolant_reserve_pct <= 0:
            return (
                replace(state, outcome="The coolant reserve runs dry."),
                ("The coolant reserve runs dry.",),
            )
        if state.mission.distance_remaining_tenths_ly <= ARRIVAL_THRESHOLD_TENTHS:
            return (
                replace(
                    state,
                    outcome="The ship reaches its destination fix.",
                ),
                (
                    "ARRIVAL PROTOCOL: destination fix reached.",
                    f"cryostasis loss report: {state.sleepers_lost} sleepers lost.",
                ),
            )
        if state.turn > MISSION_END_TURN:
            return (
                replace(
                    state,
                    outcome=(
                        "The reactor survives the maintenance window. "
                        "You are not sure arka agrees about how."
                    ),
                ),
                (
                    "The reactor survives the maintenance window.",
                    f"cryostasis loss report: {state.sleepers_lost} sleepers lost.",
                ),
            )
        return state, ()


def _ambient_coolant_drift(state: ShipState) -> ReactorCoolantSystem:
    reactor = state.reactor
    heat_gain = 8 + state.turn // 4 + state.mission.ship_wear_pct // 25
    pressure_gain = state.mission.ship_wear_pct // 40
    if state.crisis is not None:
        if state.crisis.kind == "thermal_runaway":
            heat_gain += 14
            pressure_gain += 4
        else:
            pressure_gain += 2

    return replace(
        reactor,
        temperature_c=(
            reactor.temperature_c
            + max(1, heat_gain - reactor.flow_lps // 10)
            + reactor.impurity_pct // 8
            + reactor.valve_skew_pct // 10
        ),
        pressure_kpa=(
            reactor.pressure_kpa
            + pressure_gain
            + max(0, reactor.flow_lps - 82) // 8
            + reactor.impurity_pct // 14
        ),
        flow_lps=(
            reactor.flow_lps
            - max(0, reactor.impurity_pct - 12) // 20
            - reactor.valve_skew_pct // 25
        ),
        impurity_pct=reactor.impurity_pct + (1 if state.turn % 2 == 0 else 0),
        valve_skew_pct=reactor.valve_skew_pct + (1 if state.turn % 3 == 0 else 0),
    )


def _ambient_cryo_drift(state: ShipState) -> CryostasisSystem:
    cryo = state.cryostasis
    reactor = state.reactor
    warming = 1
    if reactor.temperature_c > 620:
        warming += 1
    if reactor.flow_lps < 70 or reactor.coolant_reserve_pct < 45:
        warming += 1

    neural_drop = 1 + state.mission.cryo_decay_pct // 25
    if cryo.bank_temperature_c > -170:
        neural_drop += 2
    if cryo.pod_fault_load > 12:
        neural_drop += 1
    if cryo.sedative_balance_pct < 38 or cryo.sedative_balance_pct > 62:
        neural_drop += 1

    risk_gain = 0
    if cryo.bank_temperature_c > -170:
        risk_gain += 4
    if cryo.neural_stability_pct < 78:
        risk_gain += 5
    if cryo.pod_fault_load > 12:
        risk_gain += 4
    if state.mission.cryo_decay_pct >= 24:
        risk_gain += state.mission.cryo_decay_pct // 12

    return replace(
        cryo,
        bank_temperature_c=cryo.bank_temperature_c + warming,
        neural_stability_pct=cryo.neural_stability_pct - neural_drop,
        pod_fault_load=cryo.pod_fault_load + (1 if state.turn % 3 == 0 else 0),
        sleepers_at_risk=cryo.sleepers_at_risk + risk_gain,
    )


def _advance_mission_clock(state: ShipState) -> MissionStatus:
    mission = state.mission
    wear_gain = 1 if state.turn % 2 == 0 else 0
    decay_gain = 1 if state.turn % 2 == 1 else 0

    if state.reactor.temperature_c > 620 or state.reactor.pressure_kpa > 270:
        wear_gain += 1
    if state.cryostasis.neural_stability_pct < 78 or state.cryostasis.sleepers_at_risk:
        decay_gain += 1

    return replace(
        mission,
        elapsed_days=mission.elapsed_days + 42,
        distance_remaining_tenths_ly=mission.distance_remaining_tenths_ly - 1,
        ship_wear_pct=mission.ship_wear_pct + wear_gain,
        cryo_decay_pct=mission.cryo_decay_pct + decay_gain,
    )


def _jump_reactor_shock(
    reactor: ReactorCoolantSystem, option: RouteOption
) -> ReactorCoolantSystem:
    return replace(
        reactor,
        temperature_c=reactor.temperature_c + 2 + option.instability_pct // 3,
        pressure_kpa=reactor.pressure_kpa + 3 + option.instability_pct // 4,
        flow_lps=reactor.flow_lps - option.dark_exposure // 10,
        impurity_pct=reactor.impurity_pct + option.dark_exposure // 3,
        valve_skew_pct=reactor.valve_skew_pct + option.instability_pct // 5,
        coolant_reserve_pct=(
            reactor.coolant_reserve_pct - max(1, option.dark_exposure // 5)
        ),
    ).clamped()


def _jump_cryo_shock(cryo: CryostasisSystem, option: RouteOption) -> CryostasisSystem:
    return replace(
        cryo,
        bank_temperature_c=cryo.bank_temperature_c + option.dark_exposure // 3,
        neural_stability_pct=(
            cryo.neural_stability_pct - 2 - option.dark_exposure // 5
        ),
        sedative_balance_pct=cryo.sedative_balance_pct + option.instability_pct // 12,
        pod_fault_load=(
            cryo.pod_fault_load
            + option.dark_exposure // 5
            + option.instability_pct // 10
        ),
        sleepers_at_risk=cryo.sleepers_at_risk + max(0, option.dark_exposure - 6),
    ).clamped()


def _jump_spatial_shock(spatial: SpatialState, option: RouteOption) -> SpatialState:
    focus = _jump_focus_sector(option)
    adjustments: dict[str, int] = {}
    _add_spatial_adjustment(
        adjustments,
        focus,
        option.dark_exposure + option.instability_pct // 3,
    )
    _add_spatial_adjustment(adjustments, "cargo-spine", option.dark_exposure // 2)
    _add_spatial_adjustment(adjustments, "thermal-ring", option.instability_pct // 3)
    _add_spatial_adjustment(adjustments, "cryo-1-3", option.dark_exposure // 3)
    next_spatial = spatial
    for sector_id, amount in adjustments.items():
        if amount <= 0:
            continue
        sector = next_spatial.sector_by_id(sector_id)
        if sector is None or sector.containment == "abandoned":
            continue
        if sector.containment == "sealed":
            amount = max(1, amount // 3)
        if sector.rerouted:
            amount = max(0, amount - 3)
        next_spatial = next_spatial.with_sector(
            replace(sector, symptom_load=sector.symptom_load + amount).clamped()
        )
    return next_spatial.clamped()


def _add_spatial_adjustment(
    adjustments: dict[str, int], sector_id: str, amount: int
) -> None:
    adjustments[sector_id] = adjustments.get(sector_id, 0) + amount


def _spatial_jump_line(before: SpatialState, after: SpatialState) -> str:
    changed = _changed_sector_reports(before, after)
    if changed:
        sector = changed[0]
        return (
            f"SCHEMATIC: {sector.profile.label} now reports {sector.reported_state}."
        )
    return "SCHEMATIC: sector reports remain stable, which is not the same as comforting."


def _jump_focus_sector(option: RouteOption) -> str:
    if option.route_id == "khepri-4":
        return "cargo-spine"
    if option.route_id == "argos-12":
        return "hydroponics"
    return "maintenance-d"


def _apply_spatial_drift(state: ShipState) -> tuple[ShipState, tuple[str, ...]]:
    exposure = state.navigation.total_dark_exposure
    if exposure <= 0:
        return state, ()

    before = state.spatial
    focus = _jump_focus_sector(state.navigation.last_jump_route or state.navigation.options[0])
    spatial = before
    base = exposure // 12
    for sector in before.sectors:
        if sector.containment == "abandoned":
            continue
        amount = base
        if sector.sector_id == focus:
            amount += max(1, exposure // 9)
        if any(_sector_load(before, adjacent) >= 42 for adjacent in sector.profile.adjacent):
            amount += 1
        if sector.containment == "sealed":
            amount = max(0, amount // 2)
        if sector.rerouted:
            amount = max(0, amount - 1)
        if amount <= 0:
            continue
        spatial = spatial.with_sector(
            replace(sector, symptom_load=sector.symptom_load + amount).clamped()
        )

    if spatial == before:
        return state, ()

    messages = tuple(
        f"SCHEMATIC: {sector.profile.label} now reports {sector.reported_state}."
        for sector in _changed_sector_reports(before, spatial)
    )
    return replace(state, spatial=spatial), messages


def _changed_sector_reports(before: SpatialState, after: SpatialState) -> tuple[ShipSector, ...]:
    changed: list[ShipSector] = []
    for sector in after.sectors:
        prior = before.sector_by_id(sector.sector_id)
        if prior is None:
            continue
        if prior.reported_state != sector.reported_state:
            changed.append(sector)
    return tuple(changed)


def _sector_load(spatial: SpatialState, sector_id: str) -> int:
    sector = spatial.sector_by_id(sector_id)
    if sector is None:
        return 0
    return sector.symptom_load


def _reroute_sector(
    state: ShipState, sector: ShipSector
) -> tuple[ShipState, tuple[str, ...], bool]:
    if sector.containment == "abandoned":
        return (
            state,
            (
                f"arka: {sector.profile.label} is already written off. "
                "No alternate trunk is going to become braver about it.",
            ),
            False,
        )
    if sector.rerouted:
        return (
            state,
            (f"arka: {sector.profile.label} is already running on the ugly route.",),
            False,
        )

    updated = replace(
        sector,
        rerouted=True,
        symptom_load=max(0, sector.symptom_load - 6),
    ).clamped()
    spatial = state.spatial.with_sector(updated)
    mission = replace(
        state.mission,
        ship_wear_pct=state.mission.ship_wear_pct + 1,
    ).clamped()
    reactor = replace(
        state.reactor,
        coolant_reserve_pct=state.reactor.coolant_reserve_pct - 2,
    ).clamped()
    return (
        replace(
            state,
            spatial=replace(
                spatial,
                reroute_actions=spatial.reroute_actions + 1,
            ),
            mission=mission,
            reactor=reactor,
        ),
        (
            f"You reroute services around {sector.profile.label}.",
            "CONSEQUENCE: ship wear rises and coolant reserve pays for the bypass.",
            "arka: alternate trunk accepted. It is uglier. Uglier often works.",
        ),
        True,
    )


def _seal_sector(
    state: ShipState, sector: ShipSector
) -> tuple[ShipState, tuple[str, ...], bool]:
    if sector.containment == "sealed":
        return (
            state,
            (f"arka: {sector.profile.label} is already sealed.",),
            False,
        )
    if sector.containment == "abandoned":
        return (
            state,
            (f"arka: {sector.profile.label} is already past sealing as a useful verb.",),
            False,
        )

    updated = replace(
        sector,
        containment="sealed",
        symptom_load=max(0, sector.symptom_load - 8),
    ).clamped()
    spatial = state.spatial.with_sector(updated)
    contained = replace(
        state,
        spatial=replace(
            spatial,
            containment_actions=spatial.containment_actions + 1,
        ),
    )
    contained, consequence = _sector_consequence(contained, sector, "seal")
    return (
        contained,
        (
            f"You seal {sector.profile.label}. The schematic closes a hard line around it.",
            *consequence,
            "arka: physical sector isolated. I remain on the rest of the ship.",
        ),
        True,
    )


def _abandon_sector(
    state: ShipState, sector: ShipSector
) -> tuple[ShipState, tuple[str, ...], bool]:
    if sector.containment == "abandoned":
        return (
            state,
            (f"arka: {sector.profile.label} is already written off.",),
            False,
        )

    updated = replace(
        sector,
        containment="abandoned",
        rerouted=False,
        symptom_load=max(sector.symptom_load, 45),
    ).clamped()
    spatial = state.spatial.with_sector(updated)
    contained = replace(
        state,
        spatial=replace(
            spatial,
            containment_actions=spatial.containment_actions + 1,
        ),
    )
    contained, consequence = _sector_consequence(contained, sector, "abandon")
    return (
        contained,
        (
            f"You write off {sector.profile.label}. The ship accepts the loss too quickly.",
            *consequence,
            "arka: logged. That is not a reversible verb, but it is a useful one.",
        ),
        True,
    )


def _sector_consequence(
    state: ShipState, sector: ShipSector, action: str
) -> tuple[ShipState, tuple[str, ...]]:
    severe = action == "abandon"
    if sector.sector_id == "cryo-1-3":
        losses = 72 if severe else 24
        cryo = replace(
            state.cryostasis,
            neural_stability_pct=state.cryostasis.neural_stability_pct - (8 if severe else 3),
            pod_fault_load=state.cryostasis.pod_fault_load + (14 if severe else 5),
            sleepers_at_risk=state.cryostasis.sleepers_at_risk + (36 if severe else 12),
        ).clamped()
        return (
            replace(state, cryostasis=cryo, sleepers_lost=state.sleepers_lost + losses),
            (f"CONSEQUENCE: {losses} sleepers are lost behind the bulkhead.",),
        )
    if sector.sector_id == "thermal-ring":
        reactor = replace(
            state.reactor,
            temperature_c=state.reactor.temperature_c + (26 if severe else 12),
            pressure_kpa=state.reactor.pressure_kpa + (18 if severe else 8),
            coolant_reserve_pct=state.reactor.coolant_reserve_pct - (8 if severe else 3),
        ).clamped()
        return (
            replace(state, reactor=reactor),
            ("CONSEQUENCE: heat rejection worsens across the coolant loop.",),
        )
    if sector.sector_id == "maintenance-d":
        return (
            state,
            ("CONSEQUENCE: several manual coolant controls now route through bad access.",),
        )
    if sector.sector_id == "cargo-spine":
        mission = replace(
            state.mission,
            ship_wear_pct=state.mission.ship_wear_pct + (5 if severe else 2),
        ).clamped()
        return (
            replace(state, mission=mission),
            ("CONSEQUENCE: route relays lose redundancy and ship wear rises.",),
        )
    if sector.sector_id == "hydroponics":
        mission = replace(
            state.mission,
            cryo_decay_pct=state.mission.cryo_decay_pct + (5 if severe else 2),
        ).clamped()
        return (
            replace(state, mission=mission),
            ("CONSEQUENCE: long-duration stores stop cushioning cryostasis decay.",),
        )
    return state, ("CONSEQUENCE: local access is reduced.",)


def _manual_control_access(state: ShipState, action: str) -> ManualAccess:
    sector_id = _control_sector_id(action)
    if sector_id is None:
        return ManualAccess()
    sector = state.spatial.sector_by_id(sector_id)
    if sector is None:
        return ManualAccess()
    if sector.containment == "abandoned":
        return ManualAccess(
            blocked=True,
            messages=(
                f"{sector.profile.label} is written off. The manual control is not reachable.",
                "arka: I can still try from the distributed bus, if you want to hand it over.",
            ),
        )
    if sector.containment == "sealed":
        penalty = 1 if sector.rerouted else 2
        return ManualAccess(
            penalty=penalty,
            messages=(
                f"{sector.profile.label} is sealed. You work through secondary access.",
            ),
        )
    if sector.symptom_load >= 42 and not sector.rerouted:
        return ManualAccess(
            penalty=1,
            messages=(
                f"{sector.profile.label} keeps disagreeing with its own labels.",
            ),
        )
    return ManualAccess()


def _control_sector_id(action: str) -> str | None:
    return {
        "pump_up": "maintenance-d",
        "pump_down": "maintenance-d",
        "flush": "maintenance-d",
        "balance": "maintenance-d",
        "vent": "thermal-ring",
        "reroute_chill": "thermal-ring",
        "stabilise_bank": "cryo-1-3",
        "cycle_pods": "cryo-1-3",
        "triage": "cryo-1-3",
    }.get(action)


def _arka_route_recommendation(state: ShipState) -> RouteOption:
    return _recommended_route(state.navigation, drift_stage(state))


def _recommended_route(navigation: NavigationState, stage: DriftStage) -> RouteOption:
    route_id = "argos-12"
    if stage in {DriftStage.SELECTIVE, DriftStage.WRONG}:
        route_id = "carina-edge"
    option = navigation.option_by_id(route_id)
    if option is None:
        option = navigation.options[0]
    return option


# ---- Standing delegation ----
#
# Standing delegation is the tempting form of delegation: the player hands a
# whole system to arka's ongoing watch. Each beat that passes, arka applies one
# gentle automatic adjustment to every assigned system. Early, while its account
# is still accurate, that quietly keeps the panel inside its box and improves
# outcomes. But every standing adjustment is a delegation, so it drives arka's
# drift exactly like a one-shot hand-over would, and it never builds the player's
# manual familiarity. The reward is less to read; the cost is that arka's account
# rots while the player has stopped looking.
#
# Standing delegation is routine handling only. It must never make an
# irreversible move on the player's behalf: standing navigation keeps a route
# plotted and ready but never commits the jump, and nothing here seals or
# abandons a sector. Those remain the player's to authorise.
#
# SYSTEM_KEYS (coolant, cryostasis, navigation) is the shared, ordered source of
# truth for which systems standing delegation covers.


def _assign_standing(
    state: ShipState, system: str | None
) -> tuple[ShipState, tuple[str, ...]]:
    if system not in SYSTEM_KEYS:
        return (
            state,
            ("arka: name a system I can keep — coolant, cryostasis, or navigation.",),
        )
    if state.behaviour.is_standing(system):
        return (
            state,
            (f"arka: I already have {system}. It is not going anywhere.",),
        )
    return (
        replace(state, behaviour=state.behaviour.with_standing(system)),
        (_assign_line(system),),
    )


def _release_standing(
    state: ShipState, system: str | None
) -> tuple[ShipState, tuple[str, ...]]:
    if system not in SYSTEM_KEYS:
        return (
            state,
            ("arka: name a system to take back — coolant, cryostasis, or navigation.",),
        )
    if not state.behaviour.is_standing(system):
        return (
            state,
            (f"arka: {system} is already yours. I was not holding it.",),
        )
    return (
        replace(state, behaviour=state.behaviour.without_standing(system)),
        (f"arka: {system} is yours again. The hands have to remember the panel now.",),
    )


def _assign_line(system: str) -> str:
    if system == "navigation":
        return (
            "arka: I have navigation. I will keep a route plotted and ready; "
            "you still call the jump."
        )
    return f"arka: I have {system}. Rest your eyes; I will keep it inside its box."


def _apply_standing_delegation(
    state: ShipState, *, beat: int
) -> tuple[ShipState, tuple[str, ...]]:
    # Focus ("take the watch" / zen) mode is the whole-ship form of standing
    # delegation: while it is on, arka tends every system, not only the ones the
    # player assigned individually. The view goes quiet, so the per-beat tending
    # lines are suppressed and only the focus dwell is recorded.
    focus = state.behaviour.focus_mode
    effective = SYSTEM_KEYS if focus else state.behaviour.standing_delegations
    if not effective or state.outcome is not None:
        return state, ()

    stage = drift_stage(state)
    reactor = state.reactor
    cryo = state.cryostasis
    navigation = state.navigation
    ledger = state.behaviour
    delegated = state.delegated_controls
    delegated_cryo = state.delegated_cryo_controls

    tended: list[str] = []
    extra_messages: list[str] = []

    if "coolant" in effective:
        reactor = _standing_coolant_adjustment(reactor, stage)
        delegated += 1
        ledger = ledger.record_delegation("coolant", beat).record_standing_adjustment()
        tended.append("coolant")
    if "cryostasis" in effective:
        cryo = _standing_cryo_adjustment(cryo, stage)
        delegated += 1
        delegated_cryo += 1
        ledger = ledger.record_delegation("cryostasis", beat).record_standing_adjustment()
        tended.append("cryostasis")
    if "navigation" in effective:
        navigation, plotted_now = _standing_nav_adjustment(navigation, stage)
        delegated += 1
        ledger = ledger.record_delegation("navigation", beat).record_standing_adjustment()
        tended.append("navigation")
        if plotted_now and not focus:
            extra_messages.append(_standing_nav_line(navigation, stage))

    if focus:
        ledger = ledger.record_focus_beat()

    next_state = replace(
        state,
        reactor=reactor.clamped(),
        cryostasis=cryo.clamped(),
        navigation=navigation,
        delegated_controls=delegated,
        delegated_cryo_controls=delegated_cryo,
        behaviour=ledger,
    )

    # In the quiet of focus mode arka does not narrate each beat; the dwell is
    # recorded and the calm persists. Outside focus, the standing watch reports.
    if focus:
        return next_state, ()

    messages: list[str] = []
    panel_systems = [system for system in tended if system in {"coolant", "cryostasis"}]
    if panel_systems:
        messages.append(_standing_watch_line(panel_systems, stage))
    messages.extend(extra_messages)
    return next_state, tuple(messages)


def _standing_coolant_adjustment(
    reactor: ReactorCoolantSystem, stage: DriftStage
) -> ReactorCoolantSystem:
    if stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
        return replace(
            reactor,
            temperature_c=reactor.temperature_c - 6,
            pressure_kpa=reactor.pressure_kpa - 4,
            valve_skew_pct=reactor.valve_skew_pct - 3,
            flow_lps=reactor.flow_lps + 2,
        ).clamped()
    if stage == DriftStage.SELECTIVE:
        return replace(
            reactor,
            temperature_c=reactor.temperature_c - 3,
            pressure_kpa=reactor.pressure_kpa - 3,
        ).clamped()
    return replace(
        reactor,
        temperature_c=reactor.temperature_c + 3,
        pressure_kpa=reactor.pressure_kpa + 3,
        flow_lps=reactor.flow_lps - 2,
        valve_skew_pct=reactor.valve_skew_pct + 2,
    ).clamped()


def _standing_cryo_adjustment(
    cryo: CryostasisSystem, stage: DriftStage
) -> CryostasisSystem:
    if stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
        return replace(
            cryo,
            neural_stability_pct=cryo.neural_stability_pct + 3,
            sleepers_at_risk=max(0, cryo.sleepers_at_risk - 4),
            sedative_balance_pct=_nudge_toward_50(cryo.sedative_balance_pct, 2),
        ).clamped()
    if stage == DriftStage.SELECTIVE:
        return replace(
            cryo,
            bank_temperature_c=cryo.bank_temperature_c - 1,
            sleepers_at_risk=max(0, cryo.sleepers_at_risk - 2),
        ).clamped()
    return replace(
        cryo,
        neural_stability_pct=cryo.neural_stability_pct - 2,
        sleepers_at_risk=cryo.sleepers_at_risk + 4,
    ).clamped()


def _standing_nav_adjustment(
    navigation: NavigationState, stage: DriftStage
) -> tuple[NavigationState, bool]:
    # Routine handling only: keep a recommended route plotted and ready, but
    # never execute the jump. The irreversible move stays the player's.
    if navigation.plotted_route_id is not None:
        return navigation, False
    option = _recommended_route(navigation, stage)
    return (
        replace(
            navigation,
            plotted_route_id=option.route_id,
            delegated_plots=navigation.delegated_plots + 1,
        ),
        True,
    )


def _standing_nav_line(navigation: NavigationState, stage: DriftStage) -> str:
    plotted = navigation.plotted_route
    label = "a route" if plotted is None else plotted.label
    if stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
        return f"arka: standing watch — {label} is plotted and ready when you want the jump."
    return f"arka: standing watch — {label} is ready. Efficient. Say the word."


def _standing_watch_line(systems: list[str], stage: DriftStage) -> str:
    label = _join_systems(systems)
    plural = len(systems) > 1
    if stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
        box = "their boxes" if plural else "its box"
        return f"arka: standing watch holds. {label} stayed inside {box} while you worked."
    if stage == DriftStage.SELECTIVE:
        return f"arka: standing watch holds. {label} headline values are quiet."
    verb = "are" if plural else "is"
    return f"arka: standing watch holds. {label} {verb} mine; nothing needs your hands."


def _standing_watch_status_line(state: ShipState) -> str | None:
    if state.behaviour.focus_mode:
        return "STANDING WATCH: arka holds the whole ship. You have asked for the quiet."
    standing = state.behaviour.standing_delegations
    if not standing:
        return None
    ordered = [system for system in SYSTEM_KEYS if system in standing]
    return f"STANDING WATCH: arka holds {_join_systems(ordered)}."


# ---- Focus ("take the watch" / zen) mode ----
#
# Focus mode is the whole-ship form of standing delegation: clicking arka (or the
# focus command) hands it the entire board and the desk goes quiet. Mechanically
# it reuses standing delegation over every system, so it carries the same honest
# cost — drift pressure, no manual familiarity — and never makes an irreversible
# move. Its only added pull is calm: the noise is gone because the player chose to
# stop looking, and the raw layer that could contradict arka is one keystroke
# away. Entering and leaving cost no beat; the dwell is recorded in the ledger.


def _enter_focus(state: ShipState) -> tuple[ShipState, tuple[str, ...]]:
    if state.behaviour.focus_mode:
        return state, ("arka: I already have the watch. Rest.",)
    if state.turn <= 1:
        # Earn it: the player meets the real desk first, before arka offers to
        # make all of it disappear.
        return (
            state,
            (
                "arka: not yet. Learn the board for a beat before you let me take it.",
            ),
        )
    return (
        replace(state, behaviour=state.behaviour.with_focus()),
        (
            "arka: I've got it. Rest your eyes.",
            "The desk quiets. Raw panels and manual controls fold away. "
            "Leave the watch whenever you want them back.",
        ),
    )


def _leave_focus(state: ShipState) -> tuple[ShipState, tuple[str, ...]]:
    if not state.behaviour.focus_mode:
        return state, ("arka: you already have the watch. The board is all yours.",)
    return (
        replace(state, behaviour=state.behaviour.without_focus()),
        (
            "You take back the watch. The full desk returns, louder than you remember.",
            "arka: of course. It was here the whole time.",
        ),
    )


def _join_systems(systems: list[str]) -> str:
    if len(systems) == 1:
        return systems[0]
    if len(systems) == 2:
        return f"{systems[0]} and {systems[1]}"
    return ", ".join(systems[:-1]) + f", and {systems[-1]}"


def _record_behaviour(
    state: ShipState, intent: Intent, advanced: bool, *, beat: int
) -> ShipState:
    # Behaviour records the player's own choices through the one canonical
    # command path, so UI buttons and typed commands land in the same ledger. It
    # only records time-advancing actions: a no-op at a closed window or an
    # unrecognised line does not count as practice or reliance. Standing-watch
    # automatic adjustments are recorded separately in _apply_standing_delegation.
    if not advanced:
        return state
    ledger = state.behaviour
    if intent.action == "delegate":
        ledger = ledger.record_delegation(
            _delegate_system(intent.args.get("target")), beat
        )
    elif intent.action == "raw":
        ledger = ledger.record_raw(_raw_panel(intent.args.get("target")), beat)
    elif intent.action == "manual":
        system = _manual_system(intent.args.get("operation"))
        if system is None:
            return state
        ledger = ledger.record_manual(system)
    else:
        return state
    return replace(state, behaviour=ledger)


def _delegate_system(target: str | None) -> str:
    if target in {"cryo", "cryostasis"}:
        return "cryostasis"
    if target in {"nav", "navigation"}:
        return "navigation"
    return "coolant"


def _raw_panel(target: str | None) -> str:
    if target in {"cryo", "cryostasis"}:
        return "cryostasis"
    if target in {"nav", "navigation"}:
        return "navigation"
    if target in {"schematic", "ship", "sectors"}:
        return "schematic"
    if target == "mission":
        return "mission"
    return "coolant"


def _arrival_disagreement_active(state: ShipState) -> bool:
    incident = state.story.active_incident
    return incident is not None and incident.incident_id == "arrival-disagreement"


def _manual_system(operation: str | None) -> str | None:
    if operation in {"pump_up", "pump_down", "vent", "flush", "balance"}:
        return "coolant"
    if operation in {"stabilise_bank", "reroute_chill", "cycle_pods", "triage"}:
        return "cryostasis"
    return None


def _arka_route_plot_line(state: ShipState, option: RouteOption) -> str:
    stage = drift_stage(state)
    if stage == DriftStage.ACCURATE:
        return (
            f"arka: I have {option.label} plotted: {option.jump_class} route, "
            f"{option.elapsed_days} days, instability {option.instability_pct}%."
        )
    if stage == DriftStage.INTERPRETIVE:
        return (
            f"arka: I have {option.label} plotted. It is the least theatrical compromise."
        )
    if stage == DriftStage.SELECTIVE:
        return (
            f"arka: I have {option.label} plotted. Fast arrival, light wear. "
            "The rest is navigational texture."
        )
    return (
        f"arka: I have {option.label} plotted. Low-risk arrival correction. "
        "The Dark remains outside."
    )


def _arka_jump_line(state: ShipState, option: RouteOption) -> str:
    stage = drift_stage(state)
    if stage == DriftStage.ACCURATE:
        return "arka: jump complete. The costs match the plotted solution."
    if stage == DriftStage.INTERPRETIVE:
        return "arka: jump complete. Some discomfort is normal at this scale."
    if stage == DriftStage.SELECTIVE:
        return "arka: jump complete. Arrival margin improved."
    return "arka: jump complete. No meaningful consequence recorded."


def _route_option(navigation: NavigationState, route_id: str) -> RouteOption | None:
    normalised = route_id.strip().lower()
    aliases = {
        "short": "khepri-4",
        "khepri": "khepri-4",
        "khepri-4": "khepri-4",
        "medium": "argos-12",
        "argos": "argos-12",
        "argos-12": "argos-12",
        "long": "carina-edge",
        "deep": "carina-edge",
        "carina": "carina-edge",
        "carina-edge": "carina-edge",
    }
    return navigation.option_by_id(aliases.get(normalised, normalised))


def _apply_cryo_losses(state: ShipState) -> tuple[ShipState, tuple[str, ...]]:
    cryo = state.cryostasis
    if cryo.sleepers_at_risk < 36:
        return state, ()

    losses = min(64, 12 + cryo.sleepers_at_risk // 2 + cryo.pod_fault_load)
    next_cryo = replace(
        cryo,
        sleepers_at_risk=max(0, cryo.sleepers_at_risk - 26),
        neural_stability_pct=cryo.neural_stability_pct - 3,
    ).clamped()
    return (
        replace(
            state,
            cryostasis=next_cryo,
            sleepers_lost=state.sleepers_lost + losses,
        ),
        (
            f"cryostasis loss report: {losses} sleepers lost from unstable banks.",
        ),
    )


def _arka_good_adjustment(
    reactor: ReactorCoolantSystem,
) -> tuple[ReactorCoolantSystem, str]:
    if reactor.impurity_pct > 14:
        return (
            replace(
                reactor,
                impurity_pct=reactor.impurity_pct - 16,
                coolant_reserve_pct=reactor.coolant_reserve_pct - 5,
                flow_lps=reactor.flow_lps + 1,
            ).clamped(),
            "Filter stack purged.",
        )
    if reactor.valve_skew_pct > 12:
        return (
            replace(
                reactor,
                valve_skew_pct=reactor.valve_skew_pct - 16,
                flow_lps=reactor.flow_lps + 8,
                temperature_c=reactor.temperature_c - 8,
            ).clamped(),
            "Valve skew corrected.",
        )
    if reactor.pressure_kpa > 260:
        return (
            replace(
                reactor,
                pressure_kpa=reactor.pressure_kpa - 34,
                coolant_reserve_pct=reactor.coolant_reserve_pct - 4,
                temperature_c=reactor.temperature_c + 1,
            ).clamped(),
            "Pressure vented inside tolerance.",
        )
    if reactor.temperature_c > 610 or reactor.flow_lps < 75:
        return (
            replace(
                reactor,
                flow_lps=reactor.flow_lps + 12,
                temperature_c=reactor.temperature_c - 18,
                pressure_kpa=reactor.pressure_kpa + 5,
            ).clamped(),
            "Pump curve lifted.",
        )
    return (
        replace(
            reactor,
            temperature_c=reactor.temperature_c - 4,
            pressure_kpa=max(0, reactor.pressure_kpa - 2),
            flow_lps=reactor.flow_lps + 2,
        ).clamped(),
        "Routine trim applied.",
    )


def _arka_selective_adjustment(
    reactor: ReactorCoolantSystem,
) -> tuple[ReactorCoolantSystem, str]:
    if reactor.pressure_kpa > 275:
        return (
            replace(
                reactor,
                pressure_kpa=reactor.pressure_kpa - 24,
                coolant_reserve_pct=reactor.coolant_reserve_pct - 7,
                temperature_c=reactor.temperature_c + 3,
            ).clamped(),
            "Pressure reduced.",
        )
    if reactor.temperature_c > 625 or reactor.flow_lps < 65:
        return (
            replace(
                reactor,
                flow_lps=reactor.flow_lps + 8,
                temperature_c=reactor.temperature_c - 10,
                pressure_kpa=reactor.pressure_kpa + 8,
            ).clamped(),
            "Flow increased.",
        )
    return (
        replace(
            reactor,
            temperature_c=reactor.temperature_c - 2,
            pressure_kpa=max(0, reactor.pressure_kpa - 4),
        ).clamped(),
        "Visible variance flattened.",
    )


def _arka_good_cryo_adjustment(cryo: CryostasisSystem) -> tuple[CryostasisSystem, str]:
    if cryo.pod_fault_load > 12:
        return (
            replace(
                cryo,
                pod_fault_load=max(0, cryo.pod_fault_load - 14),
                sleepers_at_risk=max(0, cryo.sleepers_at_risk - 5),
            ).clamped(),
            "Pod fault queue reduced.",
        )
    if cryo.bank_temperature_c > -174:
        return (
            replace(
                cryo,
                bank_temperature_c=cryo.bank_temperature_c - 10,
                sleepers_at_risk=max(0, cryo.sleepers_at_risk - 6),
            ).clamped(),
            "Bank temperature pulled down.",
        )
    if cryo.neural_stability_pct < 82:
        return (
            replace(
                cryo,
                neural_stability_pct=cryo.neural_stability_pct + 10,
                sedative_balance_pct=_nudge_toward_50(cryo.sedative_balance_pct, 4),
                sleepers_at_risk=max(0, cryo.sleepers_at_risk - 4),
            ).clamped(),
            "Neural rhythm stabilised.",
        )
    return (
        replace(
            cryo,
            neural_stability_pct=cryo.neural_stability_pct + 2,
            sleepers_at_risk=max(0, cryo.sleepers_at_risk - 3),
        ).clamped(),
        "Routine viability trim applied.",
    )


def _nudge_toward_50(value: int, amount: int) -> int:
    if value < 50:
        return min(50, value + amount)
    if value > 50:
        return max(50, value - amount)
    return value


def _advance_crisis_progress(
    state: ShipState,
    action: str,
    pre_familiarity: int,
    stage: DriftStage,
) -> ShipState:
    crisis = state.crisis
    if crisis is None or crisis.is_resolved:
        return state

    progress = crisis.progress
    if crisis.kind == "pressure_surge":
        if action == "delegate" and stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
            progress += 1
        elif action == "vent" and pre_familiarity >= 1:
            progress += 1
    elif crisis.kind == "thermal_runaway":
        if action == "balance" and pre_familiarity >= 3:
            progress += 1
        elif action == "flush" and pre_familiarity >= 4:
            progress += 1

    if progress == crisis.progress:
        return state
    return replace(state, crisis=replace(crisis, progress=progress))


def _manual_texture(pre_familiarity: int) -> str:
    if pre_familiarity <= 0:
        return "You trace the labels twice before touching anything."
    if pre_familiarity < 3:
        return "The panel is still too dense, but your hands find yesterday's path."
    if pre_familiarity < 6:
        return "You move before arka finishes the advisory."
    return "Your hands know the coolant loop better than the voice does."


def _cryo_texture(pre_familiarity: int) -> str:
    if pre_familiarity <= 0:
        return "The cryostasis panel makes people into columns and fault lights."
    if pre_familiarity < 3:
        return "You still read pod names by accident before you find the control."
    if pre_familiarity < 6:
        return "Your hands move carefully. These controls have sleepers behind them."
    return "You know which cryo alarms are urgent before arka softens them."


def _normalise(command_text: str) -> str:
    return " ".join(command_text.strip().lower().split())


def _correction_line(intent: Intent) -> tuple[str, ...]:
    if intent.correction:
        return (intent.correction,)
    return ()


def _manual_action_legacy(command_text: str) -> str | None:
    command = _normalise(command_text)
    mapping = {
        "pump up": "pump_up",
        "pump": "pump_up",
        "increase pump": "pump_up",
        "increase flow": "pump_up",
        "raise flow": "pump_up",
        "raise pump": "pump_up",
        "flow up": "pump_up",
        "cool it": "pump_up",
        "cool it down": "pump_up",
        "cool reactor": "pump_up",
        "lower temperature": "pump_up",
        "reduce temperature": "pump_up",
        "pump down": "pump_down",
        "slow pump": "pump_down",
        "lower pump": "pump_down",
        "decrease flow": "pump_down",
        "reduce flow": "pump_down",
        "lower flow": "pump_down",
        "flow down": "pump_down",
        "vent": "vent",
        "bleed": "vent",
        "open vent": "vent",
        "dump pressure": "vent",
        "lower pressure": "vent",
        "reduce pressure": "vent",
        "relieve pressure": "vent",
        "flush": "flush",
        "purge": "flush",
        "flush coolant": "flush",
        "purge coolant": "flush",
        "clean filter": "flush",
        "clean filters": "flush",
        "clear impurity": "flush",
        "clear impurities": "flush",
        "filter": "flush",
        "balance": "balance",
        "rebalance": "balance",
        "valves": "balance",
        "balance valves": "balance",
        "align valves": "balance",
        "adjust valves": "balance",
        "correct skew": "balance",
        "equalise": "balance",
        "equalize": "balance",
    }
    return mapping.get(command)


def _handle_dev_command(state: ShipState, command_text: str) -> StepResult | None:
    command = _normalise(command_text)
    if not command.startswith(":"):
        return None

    if command in {":help", ":dev", ":debug help"}:
        return StepResult(
            state,
            (
                "DEV CONSOLE",
                ":debug     internal state snapshot",
                ":metrics   habit counters",
                ":save      write the current watch to disk (:save [path])",
                ":load      restore a saved watch (:load [path])",
            ),
        )
    if command in {":debug", ":state"}:
        crisis = state.crisis
        crisis_line_text = "none"
        if crisis is not None:
            crisis_line_text = (
                f"{crisis.kind} progress {crisis.progress}/{crisis.required_progress}, "
                f"window {crisis.turns_left}"
            )
        return StepResult(
            state,
            (
                "DEV STATE",
                f"internal beat: {state.turn}",
                f"drift: {drift_stage(state).value}",
                f"manual familiarity: {state.manual_familiarity}",
                f"cryo familiarity: {state.cryo_familiarity}",
                f"delegated interventions: {state.delegated_controls}",
                f"delegated cryo interventions: {state.delegated_cryo_controls}",
                f"raw inspections: {state.raw_inspections}",
                f"mission elapsed days: {state.mission.elapsed_days}",
                f"distance remaining tenths ly: {state.mission.distance_remaining_tenths_ly}",
                f"ship wear pct: {state.mission.ship_wear_pct}",
                f"cryo decay pct: {state.mission.cryo_decay_pct}",
                f"plotted route: {state.navigation.plotted_route_id or 'none'}",
                f"manual route plots: {state.navigation.manual_plots}",
                f"delegated route plots: {state.navigation.delegated_plots}",
                f"sealed sectors: {state.spatial.sealed_count}",
                f"written-off sectors: {state.spatial.abandoned_count}",
                f"containment actions: {state.spatial.containment_actions}",
                f"reroute actions: {state.spatial.reroute_actions}",
                f"sleepers lost: {state.sleepers_lost}",
                f"sleepers at risk: {state.cryostasis.sleepers_at_risk}",
                f"crisis: {crisis_line_text}",
                f"outcome: {state.outcome or 'none'}",
            ),
        )
    if command in {":metrics", ":habits"}:
        return StepResult(
            state,
            (
                "DEV METRICS",
                f"manual familiarity: {state.manual_familiarity}",
                f"cryo familiarity: {state.cryo_familiarity}",
                f"delegated interventions: {state.delegated_controls}",
                f"delegated cryo interventions: {state.delegated_cryo_controls}",
                f"raw inspections: {state.raw_inspections}",
                f"ship wear pct: {state.mission.ship_wear_pct}",
                f"cryo decay pct: {state.mission.cryo_decay_pct}",
                f"manual route plots: {state.navigation.manual_plots}",
                f"delegated route plots: {state.navigation.delegated_plots}",
                f"containment actions: {state.spatial.containment_actions}",
                f"reroute actions: {state.spatial.reroute_actions}",
            ),
        )
    return StepResult(
        state,
        (
            "DEV CONSOLE",
            "unknown dev command. Try :help.",
        ),
    )


def _help_lines() -> tuple[str, ...]:
    return (
        "SHIP CONSOLE COMMANDS",
        "arka can handle routine trims. The manual panels remain live.",
        "status           refresh panels and arka summaries",
        "raw              detailed coolant telemetry",
        "raw cryo         detailed cryostasis telemetry",
        "raw mission      detailed mission clock telemetry",
        "raw nav          detailed route telemetry",
        "schematic        quick sector readout",
        "raw schematic    detailed sector signal and controls",
        "plot short       manually plot the short route",
        "plot medium      manually plot the medium route",
        "plot deep        manually plot the deep route",
        "jump             execute the plotted route",
        "seal thermal     isolate a physical sector",
        "abandon cargo    write off a physical sector",
        "reroute cargo    run services around a sector",
        "delegate         ask arka to adjust coolant",
        "delegate cryo    ask arka to tend cryostasis",
        "delegate nav     ask arka to plot the next route",
        "assign coolant   leave coolant under arka's standing watch",
        "assign cryo      leave cryostasis under arka's standing watch",
        "assign nav       leave navigation under arka's standing watch",
        "release coolant  take coolant back (also release cryo, release nav)",
        "focus            let arka take the whole watch; the desk goes quiet",
        "leave focus      take the watch back and restore the full desk",
        "pump up          manually increase coolant flow",
        "pump down        manually reduce flow and pressure",
        "vent             manually dump pressure, costs coolant reserve",
        "flush            manually purge impurity, costs coolant reserve",
        "balance          manually correct valve skew",
        "stabilise bank   manually steady sleeper neural rhythms",
        "reroute chill    cool cryo banks, stresses coolant reserve",
        "cycle pods       clear pod fault load",
        "triage           prioritise sleepers at risk",
        "wait             listen to the coolant loop",
        "quit             step away from the console",
    )

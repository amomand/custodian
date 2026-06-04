from __future__ import annotations

from dataclasses import dataclass, replace

from custodian.arka import (
    crisis_line,
    drift_stage,
    summarize_coolant,
    summarize_cryostasis,
)
from custodian.arka_interpreter import ArkaInterpreter, Intent
from custodian.engine_constants import MISSION_END_TURN
from custodian.models import (
    CrisisState,
    CryostasisSystem,
    DriftStage,
    ReactorCoolantSystem,
    ShipState,
)
from custodian.telemetry import coolant_hud_lines, cryostasis_hud_lines


@dataclass(frozen=True)
class StepResult:
    state: ShipState
    messages: tuple[str, ...]
    advanced: bool = False
    presentation_break: bool = False


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
        correction = _correction_line(intent)
        if state.is_finished:
            return StepResult(state, ("The maintenance window is already closed.",))

        if intent.action == "status":
            return StepResult(state, correction + self._status_messages(state))
        if intent.action == "help":
            return StepResult(state, correction + _help_lines())
        if intent.action == "quit":
            return StepResult(
                replace(state, outcome="You step away from the maintenance console."),
                correction + ("arka: I will keep the loop warm. Go, then.",),
            )
        if intent.action == "raw":
            target = intent.args.get("target", "coolant")
            if target == "cryo":
                return self._advance(
                    replace(state, raw_inspections=state.raw_inspections + 1),
                    correction
                    + (
                        "You lean into the raw cryostasis panel.",
                        *state.cryostasis.raw_lines(),
                    ),
                )
            return self._advance(
                replace(state, raw_inspections=state.raw_inspections + 1),
                correction
                + ("You lean into the raw coolant panel.", *state.reactor.raw_lines()),
            )
        if intent.action == "delegate":
            delegated_state, messages = self._delegate_to_arka(
                state, intent.args.get("target", "coolant")
            )
            return self._advance(delegated_state, correction + messages)
        if intent.action == "wait":
            return self._advance(
                state,
                correction + ("You wait and listen to coolant move through the walls.",),
            )

        if intent.action == "manual":
            operation = intent.args.get("operation", "")
            target = intent.args.get("target", "coolant")
            if operation in {"pump_up", "pump_down", "vent", "flush", "balance"}:
                manual_state, messages = self._manual_control(state, operation)
                return self._advance(manual_state, correction + messages)
            if target == "cryo" and operation in {
                "stabilise_bank",
                "reroute_chill",
                "cycle_pods",
                "triage",
            }:
                manual_state, messages = self._manual_cryo_control(state, operation)
                return self._advance(manual_state, correction + messages)

        if intent.action in {"converse", "none"}:
            reply = intent.reply or (
                "arka: I can file that under psychological maintenance, but the ship "
                "accepts status, raw, delegate, manual coolant controls, and cryostasis work."
            )
            return StepResult(state, correction + (reply,))

        manual_action = _manual_action_legacy(command_text)
        if manual_action is not None:
            manual_state, messages = self._manual_control(state, manual_action)
            return self._advance(manual_state, correction + messages)

        return StepResult(
            state,
            (
                "arka: I can file that under psychological maintenance, but the ship console "
                "accepts status, raw, delegate, pump up, pump down, vent, flush, balance, "
                "stabilise bank, reroute chill, cycle pods, triage, wait.",
            ),
        )

    def _status_messages(self, state: ShipState) -> tuple[str, ...]:
        messages = [
            *coolant_hud_lines(state),
            summarize_coolant(state),
            *cryostasis_hud_lines(state),
            summarize_cryostasis(state),
        ]
        line = crisis_line(state)
        if line is not None:
            messages.append(line)
        if state.sleepers_lost:
            messages.append(f"cryostasis loss report: {state.sleepers_lost} sleepers lost.")
        return tuple(messages)

    def _advance(self, state: ShipState, messages: tuple[str, ...]) -> StepResult:
        if state.outcome is not None:
            return StepResult(state, messages, advanced=True)

        had_crisis = state.crisis is not None
        reactor = _ambient_coolant_drift(state).clamped()
        cryostasis = _ambient_cryo_drift(replace(state, reactor=reactor)).clamped()
        next_state = replace(
            state,
            turn=state.turn + 1,
            reactor=reactor,
            cryostasis=cryostasis,
        )
        next_messages = list(messages)
        presentation_break = False

        if had_crisis:
            next_state, crisis_messages = self._tick_crisis(next_state)
            next_messages.extend(crisis_messages)
            presentation_break = presentation_break or bool(crisis_messages)

        next_state, event_messages = self._apply_scheduled_events(next_state)
        next_messages.extend(event_messages)
        presentation_break = presentation_break or bool(event_messages)

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
        if target == "cryo":
            return self._delegate_cryo_to_arka(state)
        return self._delegate_coolant_to_arka(state)

    def _delegate_coolant_to_arka(
        self, state: ShipState
    ) -> tuple[ShipState, tuple[str, ...]]:
        stage = drift_stage(state)
        reactor = state.reactor
        messages: list[str] = []

        if stage in {DriftStage.ACCURATE, DriftStage.INTERPRETIVE}:
            reactor, action = _arka_good_adjustment(reactor)
            messages.append(f"arka: I have it. {action}")
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
            messages.append(f"arka: cryostasis acknowledged. {action}")
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
        familiarity = min(pre_familiarity, 6)
        reactor = state.reactor
        messages: list[str] = [_manual_texture(pre_familiarity)]

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
        familiarity = min(pre_familiarity, 5)
        cryo = state.cryostasis
        reactor = state.reactor
        messages: list[str] = [_cryo_texture(pre_familiarity)]

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
    heat_gain = 8 + state.turn // 4
    pressure_gain = 0
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

    neural_drop = 1
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

    return replace(
        cryo,
        bank_temperature_c=cryo.bank_temperature_c + warming,
        neural_stability_pct=cryo.neural_stability_pct - neural_drop,
        pod_fault_load=cryo.pod_fault_load + (1 if state.turn % 3 == 0 else 0),
        sleepers_at_risk=cryo.sleepers_at_risk + risk_gain,
    )


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
        "delegate         ask arka to adjust coolant",
        "delegate cryo    ask arka to tend cryostasis",
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

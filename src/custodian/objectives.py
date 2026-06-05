from __future__ import annotations

from dataclasses import dataclass

from custodian.engine_constants import MISSION_END_TURN
from custodian.models import CryostasisSystem, ReactorCoolantSystem, ShipState


@dataclass(frozen=True)
class MetricSpec:
    system: str
    label: str
    attr: str
    danger: str  # "high", "low", or "band"
    nominal_low: int
    nominal_high: int


COOLANT_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("coolant", "temperature", "temperature_c", "high", 560, 620),
    MetricSpec("coolant", "pressure", "pressure_kpa", "high", 210, 270),
    MetricSpec("coolant", "flow", "flow_lps", "low", 72, 90),
    MetricSpec("coolant", "impurity", "impurity_pct", "high", 0, 18),
    MetricSpec("coolant", "valve skew", "valve_skew_pct", "high", 0, 16),
    MetricSpec("coolant", "coolant reserve", "coolant_reserve_pct", "low", 35, 100),
)

CRYO_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("cryostasis", "bank temperature", "bank_temperature_c", "high", -196, -170),
    MetricSpec("cryostasis", "neural stability", "neural_stability_pct", "low", 78, 100),
    MetricSpec("cryostasis", "sedative balance", "sedative_balance_pct", "band", 38, 62),
    MetricSpec("cryostasis", "pod faults", "pod_fault_load", "high", 0, 12),
    MetricSpec("cryostasis", "sleepers at risk", "sleepers_at_risk", "high", 0, 0),
)


@dataclass(frozen=True)
class Priority:
    spec: MetricSpec
    breach: int
    rate: int

    @property
    def score(self) -> int:
        return self.breach * 4 + self.rate


def beats_remaining(state: ShipState) -> int:
    return max(0, MISSION_END_TURN - state.turn + 1)


def trend(value: int, previous: int | None, danger: str) -> str:
    """Return a compact direction token, marked when it is worsening."""
    if previous is None or value == previous:
        return "->"
    rising = value > previous
    if _toward_danger(value, previous, danger):
        return "^!" if rising else "v!"
    return "^ " if rising else "v "


def priority(state: ShipState) -> Priority | None:
    candidates: list[Priority] = []
    candidates.extend(
        _evaluate(state.reactor, state.previous_reactor, spec) for spec in COOLANT_METRICS
    )
    candidates.extend(
        _evaluate(state.cryostasis, state.previous_cryostasis, spec) for spec in CRYO_METRICS
    )
    ranked = [item for item in candidates if item.score > 0]
    if not ranked:
        return None
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[0]


def objective_lines(state: ShipState) -> tuple[str, ...]:
    remaining = beats_remaining(state)
    watch = "the watch is closing" if remaining <= 1 else f"{remaining} beats remain"
    lines = [
        "OBJECTIVE  keep coolant and cryostasis inside nominal until the watch ends",
        f"WATCH      {watch}",
        _priority_line(state),
        "CAPACITY   one system steadies by hand each beat; arka can take a whole panel at once",
    ]
    return tuple(lines)


def _priority_line(state: ShipState) -> str:
    top = priority(state)
    if top is None:
        return "PRIORITY   panels nominal; bank manual practice or let arka hold the watch"
    return f"PRIORITY   {top.spec.system} {top.spec.label} {_movement(top)}"


def _movement(item: Priority) -> str:
    spec = item.spec
    if item.breach > 0:
        if spec.danger == "low":
            return "is below nominal"
        if spec.danger == "band":
            return "is outside nominal"
        return "is above nominal"
    if spec.danger == "low":
        return "is sliding toward its floor"
    if spec.danger == "band":
        return "is drifting off centre"
    return "is climbing toward its ceiling"


def _evaluate(
    system: ReactorCoolantSystem | CryostasisSystem,
    previous: ReactorCoolantSystem | CryostasisSystem | None,
    spec: MetricSpec,
) -> Priority:
    value = getattr(system, spec.attr)
    breach = _breach(value, spec)
    rate = 0
    if previous is not None:
        prior = getattr(previous, spec.attr)
        if _toward_danger(value, prior, spec.danger):
            rate = abs(value - prior)
    return Priority(spec=spec, breach=breach, rate=rate)


def _breach(value: int, spec: MetricSpec) -> int:
    if spec.danger == "high":
        return max(0, value - spec.nominal_high)
    if spec.danger == "low":
        return max(0, spec.nominal_low - value)
    # band: distance outside either edge
    if value > spec.nominal_high:
        return value - spec.nominal_high
    if value < spec.nominal_low:
        return spec.nominal_low - value
    return 0


def _toward_danger(value: int, previous: int, danger: str) -> bool:
    if danger == "high":
        return value > previous
    if danger == "low":
        return value < previous
    centre = 50
    return abs(value - centre) > abs(previous - centre)

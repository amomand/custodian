from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum


class DriftStage(Enum):
    ACCURATE = "accurate"
    INTERPRETIVE = "interpretive"
    SELECTIVE = "selective"
    WRONG = "wrong"


@dataclass(frozen=True)
class ReactorCoolantSystem:
    temperature_c: int = 588
    pressure_kpa: int = 232
    flow_lps: int = 82
    impurity_pct: int = 6
    valve_skew_pct: int = 4
    coolant_reserve_pct: int = 100

    def clamped(self) -> "ReactorCoolantSystem":
        return replace(
            self,
            temperature_c=max(0, min(900, self.temperature_c)),
            pressure_kpa=max(0, min(500, self.pressure_kpa)),
            flow_lps=max(0, min(140, self.flow_lps)),
            impurity_pct=max(0, min(100, self.impurity_pct)),
            valve_skew_pct=max(0, min(100, self.valve_skew_pct)),
            coolant_reserve_pct=max(0, min(100, self.coolant_reserve_pct)),
        )

    def danger_flags(self) -> tuple[str, ...]:
        flags: list[str] = []
        if self.temperature_c > 620:
            flags.append("temperature high")
        if self.pressure_kpa > 270:
            flags.append("pressure high")
        if self.flow_lps < 72:
            flags.append("flow low")
        if self.impurity_pct > 18:
            flags.append("impurity high")
        if self.valve_skew_pct > 16:
            flags.append("valve skew high")
        if self.coolant_reserve_pct < 35:
            flags.append("coolant reserve low")
        return tuple(flags)

    def raw_lines(self) -> tuple[str, ...]:
        return (
            "RAW COOLANT TELEMETRY",
            f"temperature_c       {self.temperature_c:>3}   nominal 560-620",
            f"pressure_kpa        {self.pressure_kpa:>3}   nominal 210-270",
            f"flow_lps            {self.flow_lps:>3}   nominal 72-90",
            f"impurity_pct        {self.impurity_pct:>3}   nominal 0-18",
            f"valve_skew_pct      {self.valve_skew_pct:>3}   nominal 0-16",
            f"coolant_reserve_pct {self.coolant_reserve_pct:>3}   caution below 35",
        )


@dataclass(frozen=True)
class CrisisState:
    kind: str
    label: str
    turns_left: int
    required_progress: int
    progress: int = 0

    @property
    def is_resolved(self) -> bool:
        return self.progress >= self.required_progress


@dataclass(frozen=True)
class ShipState:
    turn: int = 1
    reactor: ReactorCoolantSystem = field(default_factory=ReactorCoolantSystem)
    manual_familiarity: int = 0
    delegated_controls: int = 0
    raw_inspections: int = 0
    sleepers_lost: int = 0
    crisis: CrisisState | None = None
    outcome: str | None = None

    @property
    def is_finished(self) -> bool:
        return self.outcome is not None


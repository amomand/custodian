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
class CryostasisSystem:
    bank_temperature_c: int = -184
    neural_stability_pct: int = 94
    sedative_balance_pct: int = 50
    pod_fault_load: int = 3
    sleepers_at_risk: int = 0

    def clamped(self) -> "CryostasisSystem":
        return replace(
            self,
            bank_temperature_c=max(-220, min(-120, self.bank_temperature_c)),
            neural_stability_pct=max(0, min(100, self.neural_stability_pct)),
            sedative_balance_pct=max(0, min(100, self.sedative_balance_pct)),
            pod_fault_load=max(0, min(100, self.pod_fault_load)),
            sleepers_at_risk=max(0, min(240, self.sleepers_at_risk)),
        )

    def danger_flags(self) -> tuple[str, ...]:
        flags: list[str] = []
        if self.bank_temperature_c > -170:
            flags.append("bank warming")
        if self.neural_stability_pct < 78:
            flags.append("neural stability low")
        if self.sedative_balance_pct < 38 or self.sedative_balance_pct > 62:
            flags.append("sedative balance off")
        if self.pod_fault_load > 12:
            flags.append("pod faults high")
        if self.sleepers_at_risk > 0:
            flags.append("sleepers at risk")
        return tuple(flags)

    def raw_lines(self) -> tuple[str, ...]:
        return (
            "RAW CRYOSTASIS TELEMETRY",
            f"bank_temperature_c   {self.bank_temperature_c:>4}   nominal -196 to -170",
            f"neural_stability_pct {self.neural_stability_pct:>4}   caution below 78",
            f"sedative_balance_pct {self.sedative_balance_pct:>4}   nominal 38-62",
            f"pod_fault_load       {self.pod_fault_load:>4}   nominal 0-12",
            f"sleepers_at_risk     {self.sleepers_at_risk:>4}   nominal 0",
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
class CommandRecord:
    raw: str
    action: str
    target: str | None = None
    operation: str | None = None
    advanced: bool = False
    beat_after: int = 1


@dataclass(frozen=True)
class ShipState:
    turn: int = 1
    reactor: ReactorCoolantSystem = field(default_factory=ReactorCoolantSystem)
    cryostasis: CryostasisSystem = field(default_factory=CryostasisSystem)
    manual_familiarity: int = 0
    cryo_familiarity: int = 0
    delegated_controls: int = 0
    delegated_cryo_controls: int = 0
    raw_inspections: int = 0
    sleepers_lost: int = 0
    crisis: CrisisState | None = None
    outcome: str | None = None
    previous_reactor: ReactorCoolantSystem | None = None
    previous_cryostasis: CryostasisSystem | None = None
    history: tuple[CommandRecord, ...] = ()

    @property
    def is_finished(self) -> bool:
        return self.outcome is not None

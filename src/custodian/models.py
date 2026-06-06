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
class MissionStatus:
    elapsed_days: int = 14_235
    distance_remaining_tenths_ly: int = 118
    ship_wear_pct: int = 17
    cryo_decay_pct: int = 6

    def clamped(self) -> "MissionStatus":
        return replace(
            self,
            elapsed_days=max(0, self.elapsed_days),
            distance_remaining_tenths_ly=max(0, self.distance_remaining_tenths_ly),
            ship_wear_pct=max(0, min(100, self.ship_wear_pct)),
            cryo_decay_pct=max(0, min(100, self.cryo_decay_pct)),
        )

    def raw_lines(self) -> tuple[str, ...]:
        elapsed_years = self.elapsed_days // 365
        elapsed_remainder = self.elapsed_days % 365
        distance_whole = self.distance_remaining_tenths_ly // 10
        distance_decimal = self.distance_remaining_tenths_ly % 10
        return (
            "RAW MISSION CLOCK",
            f"elapsed_mission      {elapsed_years:>3}y {elapsed_remainder:>3}d",
            f"distance_remaining  {distance_whole:>3}.{distance_decimal} ly",
            f"ship_wear_pct       {self.ship_wear_pct:>4}   caution above 35",
            f"cryo_decay_pct      {self.cryo_decay_pct:>4}   caution above 24",
        )


@dataclass(frozen=True)
class RouteOption:
    route_id: str
    label: str
    jump_class: str
    distance_tenths_ly: int
    elapsed_days: int
    dark_exposure: int
    instability_pct: int
    wear_delta_pct: int
    cryo_decay_delta_pct: int

    @property
    def distance_label(self) -> str:
        whole = self.distance_tenths_ly // 10
        decimal = self.distance_tenths_ly % 10
        return f"{whole}.{decimal} ly"


@dataclass(frozen=True)
class NavigationFix:
    fix_id: str
    label: str
    signal: str
    purpose: str


def default_route_options() -> tuple[RouteOption, ...]:
    return (
        RouteOption(
            route_id="khepri-4",
            label="KHEPRI-4",
            jump_class="short",
            distance_tenths_ly=18,
            elapsed_days=126,
            dark_exposure=4,
            instability_pct=6,
            wear_delta_pct=3,
            cryo_decay_delta_pct=3,
        ),
        RouteOption(
            route_id="argos-12",
            label="ARGOS-12",
            jump_class="medium",
            distance_tenths_ly=36,
            elapsed_days=84,
            dark_exposure=9,
            instability_pct=13,
            wear_delta_pct=2,
            cryo_decay_delta_pct=2,
        ),
        RouteOption(
            route_id="carina-edge",
            label="CARINA-EDGE",
            jump_class="deep",
            distance_tenths_ly=71,
            elapsed_days=42,
            dark_exposure=21,
            instability_pct=31,
            wear_delta_pct=1,
            cryo_decay_delta_pct=1,
        ),
    )


def default_navigation_fixes() -> tuple[NavigationFix, ...]:
    return (
        NavigationFix(
            fix_id="wakeful-drift",
            label="WAKEFUL DRIFT",
            signal="destination solution unresolved",
            purpose="starting fix; no reliable local signal",
        ),
        NavigationFix(
            fix_id="khepri-4",
            label="KHEPRI-4",
            signal="cold beacon, long coast corridor",
            purpose="safe nav reference at the cost of mission time",
        ),
        NavigationFix(
            fix_id="argos-12",
            label="ARGOS-12",
            signal="broken relay shadow, partial triangulation",
            purpose="balanced fix for the next destination solution",
        ),
        NavigationFix(
            fix_id="carina-edge",
            label="CARINA EDGE",
            signal="thin Dark boundary, poor audit trail",
            purpose="fast arrival fix with unreliable surrounding data",
        ),
    )


def navigation_fix_by_id(fix_id: str) -> NavigationFix:
    for fix in default_navigation_fixes():
        if fix.fix_id == fix_id:
            return fix
    return default_navigation_fixes()[0]


@dataclass(frozen=True)
class NavigationState:
    options: tuple[RouteOption, ...] = field(default_factory=default_route_options)
    current_fix_id: str = "wakeful-drift"
    plotted_route_id: str | None = None
    last_jump_route_id: str | None = None
    manual_plots: int = 0
    delegated_plots: int = 0
    jumps_executed: int = 0
    total_dark_exposure: int = 0

    @property
    def plotted_route(self) -> RouteOption | None:
        if self.plotted_route_id is None:
            return None
        return self.option_by_id(self.plotted_route_id)

    @property
    def last_jump_route(self) -> RouteOption | None:
        if self.last_jump_route_id is None:
            return None
        return self.option_by_id(self.last_jump_route_id)

    @property
    def current_fix(self) -> NavigationFix:
        return navigation_fix_by_id(self.current_fix_id)

    def option_by_id(self, route_id: str) -> RouteOption | None:
        for option in self.options:
            if option.route_id == route_id:
                return option
        return None

    def raw_lines(self) -> tuple[str, ...]:
        plotted = self.plotted_route
        plotted_label = "none" if plotted is None else plotted.label
        last_jump = self.last_jump_route
        last_jump_label = "none" if last_jump is None else last_jump.label
        lines = [
            "RAW NAVIGATION SOLUTIONS",
            f"current_fix         {self.current_fix.label}",
            f"current_signal      {self.current_fix.signal}",
            f"plotted_route        {plotted_label}",
            f"last_jump_route      {last_jump_label}",
            f"jumps_executed       {self.jumps_executed}",
            f"dark_exposure_total  {self.total_dark_exposure}",
            "id                  class   dist     elapsed  dark  instab  wear  cryo-age",
        ]
        for option in self.options:
            lines.append(
                f"{option.label:<19} {option.jump_class:<6} "
                f"{option.distance_label:>6}  {option.elapsed_days:>4} d"
                f"   {option.dark_exposure:>2}    {option.instability_pct:>3}%"
                f"    +{option.wear_delta_pct:<2}   +{option.cryo_decay_delta_pct}"
            )
        return tuple(lines)


@dataclass(frozen=True)
class SectorProfile:
    sector_id: str
    label: str
    function: str
    controls: str
    adjacent: tuple[str, ...] = ()
    sealable: bool = True


def default_sector_profiles() -> tuple[SectorProfile, ...]:
    return (
        SectorProfile(
            sector_id="bridge",
            label="BRIDGE",
            function="custodian console",
            controls="status, schematic, route commit",
            adjacent=("cargo-spine", "maintenance-d"),
            sealable=False,
        ),
        SectorProfile(
            sector_id="cryo-1-3",
            label="CRYOBAY 1-3",
            function="sleepers",
            controls="stabilise bank, cycle pods, triage",
            adjacent=("hydroponics", "thermal-ring"),
        ),
        SectorProfile(
            sector_id="thermal-ring",
            label="THERMAL RING",
            function="heat rejection",
            controls="vent, reroute chill",
            adjacent=("cryo-1-3", "maintenance-d"),
        ),
        SectorProfile(
            sector_id="maintenance-d",
            label="MAINTENANCE D",
            function="manual coolant trunks",
            controls="pump curve, flush, balance",
            adjacent=("bridge", "thermal-ring", "cargo-spine"),
        ),
        SectorProfile(
            sector_id="cargo-spine",
            label="CARGO SPINE",
            function="navigation mass corridor",
            controls="route relays, service access",
            adjacent=("bridge", "maintenance-d", "hydroponics"),
        ),
        SectorProfile(
            sector_id="hydroponics",
            label="HYDROPONICS",
            function="long-duration stores",
            controls="life support buffers",
            adjacent=("cargo-spine", "cryo-1-3"),
        ),
    )


def sector_profile_by_id(sector_id: str) -> SectorProfile:
    for profile in default_sector_profiles():
        if profile.sector_id == sector_id:
            return profile
    return default_sector_profiles()[0]


def sector_id_from_alias(value: str) -> str | None:
    normalised = " ".join(value.strip().lower().replace("_", " ").split())
    aliases = {
        "bridge": "bridge",
        "command": "bridge",
        "console": "bridge",
        "cryo": "cryo-1-3",
        "cryobay": "cryo-1-3",
        "cryobay 1-3": "cryo-1-3",
        "cryostasis": "cryo-1-3",
        "sleepers": "cryo-1-3",
        "pods": "cryo-1-3",
        "thermal": "thermal-ring",
        "thermal ring": "thermal-ring",
        "radiator": "thermal-ring",
        "radiators": "thermal-ring",
        "heat rejection": "thermal-ring",
        "maintenance": "maintenance-d",
        "maintenance d": "maintenance-d",
        "maintenance sector d": "maintenance-d",
        "sector d": "maintenance-d",
        "coolant trunks": "maintenance-d",
        "cargo": "cargo-spine",
        "cargo spine": "cargo-spine",
        "spine": "cargo-spine",
        "navigation relays": "cargo-spine",
        "nav relays": "cargo-spine",
        "hydroponics": "hydroponics",
        "hydro": "hydroponics",
        "stores": "hydroponics",
        "life support": "hydroponics",
        "arka": "arka",
        "a.r.k.a": "arka",
        "arka core": "arka",
        "ai": "arka",
    }
    return aliases.get(normalised)


@dataclass(frozen=True)
class ShipSector:
    sector_id: str
    symptom_load: int = 0
    containment: str = "open"
    rerouted: bool = False

    @property
    def profile(self) -> SectorProfile:
        return sector_profile_by_id(self.sector_id)

    @property
    def reported_state(self) -> str:
        if self.containment == "abandoned":
            return "written off"
        if self.containment == "sealed":
            return "sealed"
        if self.symptom_load >= 60:
            return "no signal"
        if self.symptom_load >= 42:
            return "intermittent"
        if self.symptom_load >= 24:
            return "readings disagree"
        if self.symptom_load >= 10:
            return "sensor noise"
        return "nominal"

    @property
    def signal_confidence(self) -> str:
        if self.containment == "abandoned":
            return "none"
        if self.symptom_load >= 60:
            return "lost"
        if self.symptom_load >= 42:
            return "poor"
        if self.symptom_load >= 24:
            return "contested"
        if self.symptom_load >= 10:
            return "thin"
        return "steady"

    def clamped(self) -> "ShipSector":
        containment = self.containment
        if containment not in {"open", "sealed", "abandoned"}:
            containment = "open"
        return replace(
            self,
            symptom_load=max(0, min(100, self.symptom_load)),
            containment=containment,
        )


def default_ship_sectors() -> tuple[ShipSector, ...]:
    return tuple(ShipSector(profile.sector_id) for profile in default_sector_profiles())


@dataclass(frozen=True)
class SpatialState:
    sectors: tuple[ShipSector, ...] = field(default_factory=default_ship_sectors)
    containment_actions: int = 0
    reroute_actions: int = 0

    def sector_by_id(self, sector_id: str) -> ShipSector | None:
        for sector in self.sectors:
            if sector.sector_id == sector_id:
                return sector
        return None

    def with_sector(self, replacement_sector: ShipSector) -> "SpatialState":
        sectors = tuple(
            replacement_sector if sector.sector_id == replacement_sector.sector_id else sector
            for sector in self.sectors
        )
        return replace(self, sectors=sectors)

    @property
    def sealed_count(self) -> int:
        return sum(1 for sector in self.sectors if sector.containment == "sealed")

    @property
    def abandoned_count(self) -> int:
        return sum(1 for sector in self.sectors if sector.containment == "abandoned")

    @property
    def open_symptom_sectors(self) -> tuple[ShipSector, ...]:
        return tuple(
            sector
            for sector in self.sectors
            if sector.containment == "open" and sector.reported_state != "nominal"
        )

    def clamped(self) -> "SpatialState":
        return replace(self, sectors=tuple(sector.clamped() for sector in self.sectors))

    def raw_lines(self) -> tuple[str, ...]:
        lines = [
            "RAW SHIP SCHEMATIC",
            "source              reported state       signal      containment  routing",
        ]
        for sector in self.sectors:
            routing = "rerouted" if sector.rerouted else "primary"
            lines.append(
                f"{sector.profile.label:<19} {sector.reported_state:<20} "
                f"{sector.signal_confidence:<11} {sector.containment:<11} {routing}"
            )
            lines.append(f"  controls: {sector.profile.controls}")
        lines.append("arka locus: none. no compartment or bulkhead contains arka.")
        return tuple(lines)


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
    mission: MissionStatus = field(default_factory=MissionStatus)
    navigation: NavigationState = field(default_factory=NavigationState)
    spatial: SpatialState = field(default_factory=SpatialState)
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

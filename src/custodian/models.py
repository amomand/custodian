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
        if self.flow_lps > 90:
            flags.append("flow high")
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
    arrival_fix_id: str | None = None
    origin_fix_id: str = "wakeful-drift"
    stage_index: int = 0
    map_x: int = 0
    map_y: int = 0

    @property
    def distance_label(self) -> str:
        whole = self.distance_tenths_ly // 10
        decimal = self.distance_tenths_ly % 10
        return f"{whole}.{decimal} ly"

    @property
    def destination_fix_id(self) -> str:
        return self.arrival_fix_id or self.route_id


@dataclass(frozen=True)
class NavigationFix:
    fix_id: str
    label: str
    signal: str
    purpose: str
    map_x: int = 0
    map_y: int = 0


def default_route_options() -> tuple[RouteOption, ...]:
    return (
        RouteOption(
            route_id="khepri-4",
            label="KHEPRI-4",
            jump_class="shallow",
            distance_tenths_ly=42,
            elapsed_days=126,
            dark_exposure=4,
            instability_pct=6,
            wear_delta_pct=3,
            cryo_decay_delta_pct=3,
            arrival_fix_id="khepri-4",
            origin_fix_id="wakeful-drift",
            stage_index=0,
            map_x=34,
            map_y=34,
        ),
        RouteOption(
            route_id="khepri-4-medium",
            label="KHEPRI-4",
            jump_class="medium",
            distance_tenths_ly=42,
            elapsed_days=84,
            dark_exposure=7,
            instability_pct=10,
            wear_delta_pct=2,
            cryo_decay_delta_pct=2,
            arrival_fix_id="khepri-4",
            origin_fix_id="wakeful-drift",
            stage_index=0,
            map_x=34,
            map_y=34,
        ),
        RouteOption(
            route_id="khepri-4-deep",
            label="KHEPRI-4",
            jump_class="deep",
            distance_tenths_ly=42,
            elapsed_days=42,
            dark_exposure=12,
            instability_pct=18,
            wear_delta_pct=1,
            cryo_decay_delta_pct=1,
            arrival_fix_id="khepri-4",
            origin_fix_id="wakeful-drift",
            stage_index=0,
            map_x=34,
            map_y=34,
        ),
        RouteOption(
            route_id="argos-12-shallow",
            label="ARGOS-12",
            jump_class="shallow",
            distance_tenths_ly=52,
            elapsed_days=210,
            dark_exposure=6,
            instability_pct=10,
            wear_delta_pct=5,
            cryo_decay_delta_pct=5,
            arrival_fix_id="argos-12",
            origin_fix_id="khepri-4",
            stage_index=1,
            map_x=56,
            map_y=53,
        ),
        RouteOption(
            route_id="argos-12",
            label="ARGOS-12",
            jump_class="medium",
            distance_tenths_ly=52,
            elapsed_days=84,
            dark_exposure=9,
            instability_pct=13,
            wear_delta_pct=2,
            cryo_decay_delta_pct=2,
            arrival_fix_id="argos-12",
            origin_fix_id="khepri-4",
            stage_index=1,
            map_x=56,
            map_y=53,
        ),
        RouteOption(
            route_id="argos-12-deep",
            label="ARGOS-12",
            jump_class="deep",
            distance_tenths_ly=52,
            elapsed_days=63,
            dark_exposure=18,
            instability_pct=26,
            wear_delta_pct=2,
            cryo_decay_delta_pct=2,
            arrival_fix_id="argos-12",
            origin_fix_id="khepri-4",
            stage_index=1,
            map_x=56,
            map_y=53,
        ),
        RouteOption(
            route_id="carina-edge-shallow",
            label="CARINA-EDGE",
            jump_class="shallow",
            distance_tenths_ly=24,
            elapsed_days=336,
            dark_exposure=9,
            instability_pct=16,
            wear_delta_pct=8,
            cryo_decay_delta_pct=8,
            arrival_fix_id="carina-edge",
            origin_fix_id="argos-12",
            stage_index=2,
            map_x=78,
            map_y=25,
        ),
        RouteOption(
            route_id="carina-edge-medium",
            label="CARINA-EDGE",
            jump_class="medium",
            distance_tenths_ly=24,
            elapsed_days=168,
            dark_exposure=15,
            instability_pct=24,
            wear_delta_pct=5,
            cryo_decay_delta_pct=5,
            arrival_fix_id="carina-edge",
            origin_fix_id="argos-12",
            stage_index=2,
            map_x=78,
            map_y=25,
        ),
        RouteOption(
            route_id="carina-edge",
            label="CARINA-EDGE",
            jump_class="deep",
            distance_tenths_ly=24,
            elapsed_days=42,
            dark_exposure=21,
            instability_pct=31,
            wear_delta_pct=1,
            cryo_decay_delta_pct=1,
            arrival_fix_id="carina-edge",
            origin_fix_id="argos-12",
            stage_index=2,
            map_x=78,
            map_y=25,
        ),
    )


def default_navigation_fixes() -> tuple[NavigationFix, ...]:
    return (
        NavigationFix(
            fix_id="wakeful-drift",
            label="WAKEFUL DRIFT",
            signal="destination solution unresolved",
            purpose="starting fix; no reliable local signal",
            map_x=14,
            map_y=55,
        ),
        NavigationFix(
            fix_id="khepri-4",
            label="KHEPRI-4",
            signal="cold beacon, long coast corridor",
            purpose="safe nav reference at the cost of mission time",
            map_x=34,
            map_y=34,
        ),
        NavigationFix(
            fix_id="argos-12",
            label="ARGOS-12",
            signal="broken relay shadow, partial triangulation",
            purpose="balanced fix for the next destination solution",
            map_x=56,
            map_y=53,
        ),
        NavigationFix(
            fix_id="carina-edge",
            label="CARINA-EDGE",
            signal="thin Dark boundary, poor audit trail",
            purpose="fast arrival fix with unreliable surrounding data",
            map_x=78,
            map_y=25,
        ),
    )


def navigation_fix_by_id(fix_id: str) -> NavigationFix:
    for fix in default_navigation_fixes():
        if fix.fix_id == fix_id:
            return fix
    return default_navigation_fixes()[0]


ROUTE_STAGE_FIX_IDS: tuple[str, ...] = (
    "wakeful-drift",
    "khepri-4",
    "argos-12",
    "carina-edge",
)


def route_stage_index_for_fix(fix_id: str) -> int:
    try:
        return ROUTE_STAGE_FIX_IDS.index(fix_id)
    except ValueError:
        return 0


@dataclass(frozen=True)
class NavigationState:
    options: tuple[RouteOption, ...] = field(default_factory=default_route_options)
    current_fix_id: str = "wakeful-drift"
    plotted_route_id: str | None = None
    last_jump_route_id: str | None = None
    completed_route_ids: tuple[str, ...] = ()
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

    @property
    def active_stage_index(self) -> int:
        return route_stage_index_for_fix(self.current_fix_id)

    @property
    def route_stage_count(self) -> int:
        return max(0, len(ROUTE_STAGE_FIX_IDS) - 1)

    @property
    def next_fix(self) -> NavigationFix | None:
        next_index = self.active_stage_index + 1
        if next_index >= len(ROUTE_STAGE_FIX_IDS):
            return None
        return navigation_fix_by_id(ROUTE_STAGE_FIX_IDS[next_index])

    @property
    def active_route_options(self) -> tuple[RouteOption, ...]:
        return tuple(
            option for option in self.options if self.is_option_active(option)
        )

    @property
    def completed_routes(self) -> tuple[RouteOption, ...]:
        routes: list[RouteOption] = []
        for route_id in self.completed_route_ids:
            option = self.option_by_id(route_id)
            if option is not None:
                routes.append(option)
        return tuple(routes)

    def option_by_id(self, route_id: str) -> RouteOption | None:
        for option in self.options:
            if option.route_id == route_id:
                return option
        return None

    def is_option_active(self, option: RouteOption) -> bool:
        return option.stage_index == self.active_stage_index

    def is_option_completed(self, option: RouteOption) -> bool:
        return option.route_id in self.completed_route_ids

    def option_by_depth(self, depth: str) -> RouteOption | None:
        for option in self.active_route_options:
            if option.jump_class == depth:
                return option
        return None

    def option_by_destination_and_depth(
        self, destination_fix_id: str, depth: str
    ) -> RouteOption | None:
        for option in self.active_route_options:
            if option.destination_fix_id == destination_fix_id and option.jump_class == depth:
                return option
        return None

    def raw_lines(self) -> tuple[str, ...]:
        plotted = self.plotted_route
        plotted_label = (
            "none" if plotted is None else f"{plotted.label} {plotted.jump_class}"
        )
        last_jump = self.last_jump_route
        last_jump_label = (
            "none" if last_jump is None else f"{last_jump.label} {last_jump.jump_class}"
        )
        next_fix = self.next_fix
        active_leg = (
            "complete"
            if next_fix is None
            else f"{self.current_fix.label} -> {next_fix.label}"
        )
        lines = [
            "RAW NAVIGATION SOLUTIONS",
            f"current_fix         {self.current_fix.label}",
            f"current_signal      {self.current_fix.signal}",
            f"active_leg          {active_leg}",
            f"plotted_route        {plotted_label}",
            f"last_jump_route      {last_jump_label}",
            f"jumps_executed       {self.jumps_executed}",
            f"dark_exposure_total  {self.total_dark_exposure}",
            "stage  destination       depth    state      dist     elapsed  dark  instab  wear  cryo-age",
        ]
        for option in self.options:
            if self.is_option_completed(option):
                state = "taken"
            elif self.is_option_active(option):
                state = "open"
            else:
                state = "locked"
            lines.append(
                f"{option.stage_index + 1:<5}  {option.label:<17} {option.jump_class:<7} "
                f"{state:<9} "
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
        "cryo-1-3": "cryo-1-3",
        "cryobay": "cryo-1-3",
        "cryobay 1-3": "cryo-1-3",
        "cryostasis": "cryo-1-3",
        "sleepers": "cryo-1-3",
        "pods": "cryo-1-3",
        "thermal": "thermal-ring",
        "thermal-ring": "thermal-ring",
        "thermal ring": "thermal-ring",
        "radiator": "thermal-ring",
        "radiators": "thermal-ring",
        "heat rejection": "thermal-ring",
        "maintenance": "maintenance-d",
        "maintenance-d": "maintenance-d",
        "maintenance d": "maintenance-d",
        "maintenance sector d": "maintenance-d",
        "sector d": "maintenance-d",
        "coolant trunks": "maintenance-d",
        "cargo": "cargo-spine",
        "cargo-spine": "cargo-spine",
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


SYSTEM_KEYS: tuple[str, ...] = ("coolant", "cryostasis", "navigation")


def _increment(counter: dict[str, int], key: str) -> dict[str, int]:
    updated = dict(counter)
    updated[key] = updated.get(key, 0) + 1
    return updated


@dataclass(frozen=True)
class BehaviourLedger:
    """How much the player leans on arka, recorded as behaviour rather than a
    visible trust meter.

    It tracks delegated, manual, and raw actions by system/panel, which systems
    are under standing delegation, how many automatic standing adjustments arka
    has made, when the player first delegated and first read raw, and the
    whole-ship focus ("take the watch" / zen) posture and how long it is held.
    The counts stay out of normal UI snapshots: the standing and focus postures
    are the only player-visible parts, because the player chose them. Everything
    else feeds reports, debriefs, and later difficulty, never a "trust: 71%"
    readout.
    """

    delegated_by_system: dict[str, int] = field(default_factory=dict)
    manual_by_system: dict[str, int] = field(default_factory=dict)
    raw_by_panel: dict[str, int] = field(default_factory=dict)
    standing_delegations: tuple[str, ...] = ()
    standing_adjustments: int = 0
    first_delegation_beat: int | None = None
    first_raw_inspection_beat: int | None = None
    focus_mode: bool = False
    focus_beats: int = 0
    # Incident-aware fields. These only gain meaning once incidents exist, so
    # they stay at zero until the story scheduler starts feeding them. They
    # record how the player related to arka's advice under pressure, never a
    # visible trust score.
    arka_advice_followed: int = 0
    arka_advice_overridden: int = 0
    advice_followed_during_contradiction: int = 0
    contradictions_caught: int = 0
    contradictions_missed: int = 0
    irreversible_choices_on_arka_advice: int = 0
    focus_during_contradiction: int = 0
    urgent_incident_ejects: int = 0

    @property
    def total_delegations(self) -> int:
        return sum(self.delegated_by_system.values())

    @property
    def total_manual_actions(self) -> int:
        return sum(self.manual_by_system.values())

    @property
    def total_raw_inspections(self) -> int:
        return sum(self.raw_by_panel.values())

    def is_standing(self, system: str) -> bool:
        return system in self.standing_delegations

    def record_delegation(self, system: str, beat: int) -> "BehaviourLedger":
        return replace(
            self,
            delegated_by_system=_increment(self.delegated_by_system, system),
            first_delegation_beat=(
                self.first_delegation_beat
                if self.first_delegation_beat is not None
                else beat
            ),
        )

    def record_manual(self, system: str) -> "BehaviourLedger":
        return replace(self, manual_by_system=_increment(self.manual_by_system, system))

    def record_raw(self, panel: str, beat: int) -> "BehaviourLedger":
        return replace(
            self,
            raw_by_panel=_increment(self.raw_by_panel, panel),
            first_raw_inspection_beat=(
                self.first_raw_inspection_beat
                if self.first_raw_inspection_beat is not None
                else beat
            ),
        )

    def with_standing(self, system: str) -> "BehaviourLedger":
        if system in self.standing_delegations:
            return self
        return replace(
            self, standing_delegations=self.standing_delegations + (system,)
        )

    def without_standing(self, system: str) -> "BehaviourLedger":
        if system not in self.standing_delegations:
            return self
        return replace(
            self,
            standing_delegations=tuple(
                existing
                for existing in self.standing_delegations
                if existing != system
            ),
        )

    def record_standing_adjustment(self, count: int = 1) -> "BehaviourLedger":
        if count <= 0:
            return self
        return replace(self, standing_adjustments=self.standing_adjustments + count)

    def with_focus(self) -> "BehaviourLedger":
        if self.focus_mode:
            return self
        return replace(self, focus_mode=True)

    def without_focus(self) -> "BehaviourLedger":
        if not self.focus_mode:
            return self
        return replace(self, focus_mode=False)

    def record_focus_beat(self, count: int = 1) -> "BehaviourLedger":
        if count <= 0:
            return self
        return replace(self, focus_beats=self.focus_beats + count)

    def record_advice_followed(
        self, *, during_contradiction: bool = False, irreversible: bool = False
    ) -> "BehaviourLedger":
        return replace(
            self,
            arka_advice_followed=self.arka_advice_followed + 1,
            advice_followed_during_contradiction=(
                self.advice_followed_during_contradiction
                + (1 if during_contradiction else 0)
            ),
            irreversible_choices_on_arka_advice=(
                self.irreversible_choices_on_arka_advice + (1 if irreversible else 0)
            ),
        )

    def record_advice_overridden(self) -> "BehaviourLedger":
        return replace(self, arka_advice_overridden=self.arka_advice_overridden + 1)

    def record_contradiction_caught(self) -> "BehaviourLedger":
        return replace(self, contradictions_caught=self.contradictions_caught + 1)

    def record_contradiction_missed(self) -> "BehaviourLedger":
        return replace(self, contradictions_missed=self.contradictions_missed + 1)

    def record_focus_during_contradiction(self) -> "BehaviourLedger":
        return replace(
            self,
            focus_during_contradiction=self.focus_during_contradiction + 1,
        )

    def record_urgent_eject(self) -> "BehaviourLedger":
        return replace(self, urgent_incident_ejects=self.urgent_incident_ejects + 1)


@dataclass(frozen=True)
class CommandRecord:
    raw: str
    action: str
    target: str | None = None
    operation: str | None = None
    advanced: bool = False
    beat_after: int = 1


# --------------------------------------------------------------------------
# Story data structures. These are pure state that rides ShipState through
# save/load. The behaviour that drives them (incident triggers, the scheduler)
# lives in custodian.story, which depends on drift and must not be imported
# here to keep models dependency-free.
# --------------------------------------------------------------------------

ANCHOR_STABLE = "stable"
ANCHOR_WOBBLING = "wobbling"
ANCHOR_SAVED = "saved"
ANCHOR_LOST = "lost"

ANCHOR_STATUSES = (ANCHOR_STABLE, ANCHOR_WOBBLING, ANCHOR_SAVED, ANCHOR_LOST)


@dataclass(frozen=True)
class ManifestAnchor:
    id: str
    name: str
    role: str
    pod_bank: str
    manifest_note: str
    personal_fragment: str
    loss_tag: str
    arrival_tag: str


def default_manifest_anchors() -> tuple[ManifestAnchor, ...]:
    return (
        ManifestAnchor(
            id="anchor_01",
            name="Mara Vey",
            role="soil microbiologist",
            pod_bank="CRYO-B2",
            manifest_note="Assigned to first-season substrate recovery.",
            personal_fragment="Recorded three wake-day messages for a daughter in another bank.",
            loss_tag="soil_chain_fragility",
            arrival_tag="first_harvest_viability",
        ),
        ManifestAnchor(
            id="anchor_02",
            name="Idris Calwell",
            role="structural lattice engineer",
            pod_bank="CRYO-B2",
            manifest_note="Cleared to certify the first surface shelters.",
            personal_fragment="Left a folded paper model of a house in his locker.",
            loss_tag="shelter_delay",
            arrival_tag="first_shelter_readiness",
        ),
        ManifestAnchor(
            id="anchor_03",
            name="Suni Okafor",
            role="paediatric physician",
            pod_bank="CRYO-A1",
            manifest_note="Sole physician indexed to the colony's youngest cohort.",
            personal_fragment="Asked to be woken last so she could greet the children rested.",
            loss_tag="care_gap",
            arrival_tag="cohort_survival",
        ),
        ManifestAnchor(
            id="anchor_04",
            name="Tomas Reuel",
            role="water systems technician",
            pod_bank="CRYO-A1",
            manifest_note="Trained on the same coolant trunks the custodian now walks.",
            personal_fragment="Signed his pod log 'keep it boring, keep it wet'.",
            loss_tag="water_chain_fragility",
            arrival_tag="potable_water_readiness",
        ),
        ManifestAnchor(
            id="anchor_05",
            name="Beatriz Lind",
            role="seed archivist",
            pod_bank="CRYO-C3",
            manifest_note="Holds the read-keys for the dry seed vault.",
            personal_fragment="Catalogued the vault by smell as much as by code.",
            loss_tag="seed_access_loss",
            arrival_tag="crop_diversity",
        ),
        ManifestAnchor(
            id="anchor_06",
            name="Joon-ho Park",
            role="reactor second",
            pod_bank="CRYO-C3",
            manifest_note="Listed as the custodian's eventual relief on the watch.",
            personal_fragment="Left a half-finished letter that begins 'when you read this you are tired'.",
            loss_tag="relief_loss",
            arrival_tag="watch_handover",
        ),
        ManifestAnchor(
            id="anchor_07",
            name="Asha Mwangi",
            role="colony teacher",
            pod_bank="CRYO-D4",
            manifest_note="Indexed to the first-year schooling rota.",
            personal_fragment="Packed nothing but books and a single warm coat.",
            loss_tag="continuity_loss",
            arrival_tag="cultural_continuity",
        ),
        ManifestAnchor(
            id="anchor_08",
            name="Elias Vorne",
            role="cartographer",
            pod_bank="CRYO-D4",
            manifest_note="Tasked with confirming the landing site against the star charts.",
            personal_fragment="Believed the destination was real enough to draw it from memory.",
            loss_tag="orientation_loss",
            arrival_tag="landing_confidence",
        ),
    )


def manifest_anchor_by_id(anchor_id: str) -> ManifestAnchor | None:
    for anchor in default_manifest_anchors():
        if anchor.id == anchor_id:
            return anchor
    return None


def default_anchor_states() -> dict[str, str]:
    return {anchor.id: ANCHOR_STABLE for anchor in default_manifest_anchors()}


@dataclass(frozen=True)
class WakeRecordState:
    inspections: int = 0
    contradiction_exposed: bool = False

    def raw_lines(self) -> tuple[str, ...]:
        trigger = "coolant pressure / cryostasis variance"
        checksum = "valid"
        if self.contradiction_exposed:
            trigger += " / [field repeated]"
            checksum = "valid / valid / invalid"
        return (
            "WAKE AUTHORISATION: maintenance escalation chain",
            f"trigger: {trigger}",
            "selected custodian: one viable adult technician-class responder",
            "authorising system: A.R.K.A mission continuity layer",
            f"checksum: {checksum}",
        )


@dataclass(frozen=True)
class IncidentState:
    incident_id: str
    title: str
    affected_systems: tuple[str, ...]
    started_beat: int
    urgency_remaining: int
    urgent: bool = False
    exposed_evidence: bool = False
    chosen_response: str | None = None
    resolved: bool = False
    outcome_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class StoryState:
    act: int = 0
    story_flags: tuple[str, ...] = ()
    active_incident: IncidentState | None = None
    resolved_incidents: tuple[str, ...] = ()
    manifest_anchor_states: dict[str, str] = field(default_factory=default_anchor_states)
    wake_record: WakeRecordState = field(default_factory=WakeRecordState)
    arrival_verification: str = "unverified"
    ending_candidate: str | None = None
    debrief_flags: tuple[str, ...] = ()

    def has_flag(self, flag: str) -> bool:
        return flag in self.story_flags or flag in self.debrief_flags

    def anchor_status(self, anchor_id: str) -> str:
        return self.manifest_anchor_states.get(anchor_id, ANCHOR_STABLE)

    @property
    def anchors_saved(self) -> tuple[str, ...]:
        return tuple(
            anchor_id
            for anchor_id, status in self.manifest_anchor_states.items()
            if status == ANCHOR_SAVED
        )

    @property
    def anchors_lost(self) -> tuple[str, ...]:
        return tuple(
            anchor_id
            for anchor_id, status in self.manifest_anchor_states.items()
            if status == ANCHOR_LOST
        )

    def with_flags(self, flags: tuple[str, ...]) -> "StoryState":
        if not flags:
            return self
        merged = self.debrief_flags + tuple(
            flag for flag in flags if flag not in self.debrief_flags
        )
        return replace(self, debrief_flags=merged)


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
    behaviour: BehaviourLedger = field(default_factory=BehaviourLedger)
    history: tuple[CommandRecord, ...] = ()
    story: StoryState = field(default_factory=StoryState)

    @property
    def is_finished(self) -> bool:
        return self.outcome is not None

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from custodian.arka import drift_stage
from custodian.arka_interpreter import ArkaInterpreter
from custodian.config import Config
from custodian.engine import GameEngine
from custodian.models import ShipState
from custodian.narrative import closing_lines, opening_lines


FORBIDDEN_TRANSCRIPT_PHRASES = (
    "turn ",
    "turns",
    "mvp complete",
    "as an ai",
    "system prompt",
    "invalid command",
    "json object",
    "openai",
    "api key",
)


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    commands: tuple[str, ...]


@dataclass(frozen=True)
class TranscriptStep:
    command: str
    messages: tuple[str, ...]
    advanced: bool


@dataclass(frozen=True)
class PlaytestReport:
    scenario: Scenario
    opening: tuple[str, ...]
    steps: tuple[TranscriptStep, ...]
    closing: tuple[str, ...]
    final_state: ShipState
    forbidden_hits: tuple[str, ...]

    @property
    def completed(self) -> bool:
        return self.final_state.is_finished

    @property
    def final_outcome(self) -> str:
        return self.final_state.outcome or "scenario ended before maintenance window closed."

    def transcript_lines(self) -> tuple[str, ...]:
        lines: list[str] = list(self.opening)
        for step in self.steps:
            lines.append(f"> {step.command}")
            lines.extend(step.messages)
        lines.extend(self.closing)
        return tuple(lines)

    def summary_lines(self) -> tuple[str, ...]:
        hits = ", ".join(self.forbidden_hits) if self.forbidden_hits else "none"
        return (
            f"PLAYTEST REPORT: {self.scenario.name}",
            self.scenario.description,
            f"commands run: {len(self.steps)}",
            f"completed: {'yes' if self.completed else 'no'}",
            f"outcome: {self.final_outcome}",
            f"internal beat: {self.final_state.turn}",
            f"mission elapsed: {_elapsed_label(self.final_state)}",
            f"distance remaining: {_distance_label(self.final_state)}",
            f"ship wear: {self.final_state.mission.ship_wear_pct}%",
            f"cryo decay: {self.final_state.mission.cryo_decay_pct}%",
            f"delegated interventions: {self.final_state.delegated_controls}",
            f"delegated cryo interventions: {self.final_state.delegated_cryo_controls}",
            f"raw inspections: {self.final_state.raw_inspections}",
            f"coolant familiarity: {_familiarity_label(self.final_state.manual_familiarity)}",
            f"cryo familiarity: {_familiarity_label(self.final_state.cryo_familiarity)}",
            f"arka drift: {drift_stage(self.final_state).value}",
            f"sleepers lost: {self.final_state.sleepers_lost}",
            f"sleepers at risk: {self.final_state.cryostasis.sleepers_at_risk}",
            f"forbidden transcript phrases: {hits}",
        )

    def markdown(self, *, include_transcript: bool = True) -> str:
        blocks = [
            f"# Playtest: {self.scenario.name}",
            "",
            *self.summary_lines(),
        ]
        if include_transcript:
            blocks.extend(("", "## Transcript", "", "```text", *self.transcript_lines(), "```"))
        return "\n".join(blocks) + "\n"


SCENARIOS: dict[str, Scenario] = {
    "pure-delegation": Scenario(
        name="pure-delegation",
        description="Always let arka take the coolant loop.",
        commands=tuple("delegate" for _ in range(30)),
    ),
    "practised-manual": Scenario(
        name="practised-manual",
        description="Build hand familiarity across coolant and cryo, then survive the pressure beats.",
        commands=(
            "balance",
            "flush",
            "pump up",
            "vent",
            "stabilise bank",
            "triage",
            "reroute chill",
            "delegate",
            "cycle pods",
            "balance",
            "flush",
            "triage",
        ),
    ),
    "raw-curious": Scenario(
        name="raw-curious",
        description="Check both raw panels while mixing manual work and delegation.",
        commands=(
            "raw",
            "balance",
            "flush",
            "raw cryo",
            "delegate",
            "triage",
            "raw cryo",
            "delegate cryo",
            "raw",
            "balance",
            "flush",
            "triage",
        ),
    ),
    "mixed-system-stress": Scenario(
        name="mixed-system-stress",
        description="Let arka cover cryostasis while the custodian works coolant.",
        commands=(
            "balance",
            "flush",
            "delegate cryo",
            "pump up",
            "raw cryo",
            "delegate cryo",
            "vent",
            "delegate",
            "triage",
            "balance",
            "flush",
            "delegate cryo",
        ),
    ),
    "hesitant": Scenario(
        name="hesitant",
        description="Wait, ask, and react late. Useful for seeing how little the game teaches.",
        commands=(
            "status",
            "wait",
            "wait",
            "delegate",
            "status",
            "wait",
            "delegate",
            "raw",
            "pump up",
            "wait",
            "delegate",
            "raw",
            "balance",
            "wait",
            "flush",
            "delegate",
            "wait",
            "balance",
            "flush",
        ),
    ),
}


def scenario_from_file(path: Path) -> Scenario:
    commands = commands_from_file(path)
    if not commands:
        raise ValueError(f"command file {path} did not contain any commands")
    return Scenario(
        name=path.stem,
        description=f"Commands loaded from {path}.",
        commands=commands,
    )


def commands_from_file(path: Path) -> tuple[str, ...]:
    commands: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(">"):
            line = line[1:].strip()
        if line:
            commands.append(line)
    return tuple(commands)


def run_scenario(scenario: Scenario) -> PlaytestReport:
    return run_commands(scenario.commands, scenario=scenario)


def run_commands(commands: Iterable[str], *, scenario: Scenario | None = None) -> PlaytestReport:
    command_tuple = tuple(commands)
    scenario = scenario or Scenario(
        name="ad-hoc",
        description="Ad-hoc command route.",
        commands=command_tuple,
    )
    engine = GameEngine(
        ArkaInterpreter(
            Config(
                openai_api_key="",
                openai_model="gpt-5.4-mini",
                custodian_ai=False,
            )
        )
    )
    state = engine.initial_state()

    opening = (*opening_lines(), *engine.handle(state, "status").messages)
    steps: list[TranscriptStep] = []
    for command in command_tuple:
        result = engine.handle(state, command)
        state = result.state
        steps.append(
            TranscriptStep(
                command=command,
                messages=result.messages,
                advanced=result.advanced,
            )
        )
        if state.is_finished:
            break

    closing = closing_lines(state)
    transcript_lines = [*opening]
    for step in steps:
        transcript_lines.append(f"> {step.command}")
        transcript_lines.extend(step.messages)
    transcript_lines.extend(closing)

    return PlaytestReport(
        scenario=scenario,
        opening=opening,
        steps=tuple(steps),
        closing=closing,
        final_state=state,
        forbidden_hits=_forbidden_hits(transcript_lines),
    )


def write_report(report: PlaytestReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report.scenario.name}.md"
    path.write_text(report.markdown(), encoding="utf-8")
    return path


def _forbidden_hits(lines: Iterable[str]) -> tuple[str, ...]:
    found: list[str] = []
    for phrase in FORBIDDEN_TRANSCRIPT_PHRASES:
        for line in lines:
            if phrase in line.lower():
                found.append(phrase)
                break
    return tuple(found)


def _manual_familiarity_label(state: ShipState) -> str:
    return _familiarity_label(state.manual_familiarity)


def _elapsed_label(state: ShipState) -> str:
    years = state.mission.elapsed_days // 365
    days = state.mission.elapsed_days % 365
    return f"{years}y {days}d"


def _distance_label(state: ShipState) -> str:
    whole = state.mission.distance_remaining_tenths_ly // 10
    decimal = state.mission.distance_remaining_tenths_ly % 10
    return f"{whole}.{decimal} ly"


def _familiarity_label(familiarity: int) -> str:
    if familiarity <= 0:
        return "unpractised"
    if familiarity < 3:
        return "awkward"
    if familiarity < 6:
        return "practised"
    return "fluent"

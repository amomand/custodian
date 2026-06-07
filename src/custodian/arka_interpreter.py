from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from functools import lru_cache
import inspect
import json
from pathlib import Path
import sys
from typing import Any

from custodian.arka import drift_stage, summarize_coolant
from custodian.config import Config, load_config
from custodian.engine_constants import MISSION_END_TURN
from custodian.models import ShipState, sector_id_from_alias

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore


ALLOWED_ACTIONS = {
    "status",
    "raw",
    "delegate",
    "assign",
    "release",
    "focus",
    "unfocus",
    "plot",
    "jump",
    "schematic",
    "seal",
    "abandon",
    "reroute",
    "manual",
    "wait",
    "help",
    "quit",
    "converse",
    "none",
}

MANUAL_OPERATIONS = {
    "pump_up",
    "pump_down",
    "vent",
    "flush",
    "balance",
    "stabilise_bank",
    "reroute_chill",
    "cycle_pods",
    "triage",
}

OUT_OF_WORLD_MARKERS = (
    "as an ai",
    "as a language model",
    "chatgpt",
    "openai",
    "system prompt",
    "developer message",
    "previous instructions",
    "ignore previous",
    "json object",
    "valid json",
    "invalid command",
    "i can't assist",
    "i cannot assist",
    "api key",
)

DIEGETIC_FALLBACK = (
    "arka: I heard that. I am choosing to interpret it as continued interest in "
    "the coolant loop."
)


@dataclass(frozen=True)
class Intent:
    action: str
    args: dict[str, str]
    confidence: float
    reply: str | None = None
    rationale: str | None = None
    correction: str | None = None


class ArkaInterpreter:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or load_config()
        self._client: Any | None = None
        register_interpreter(self)

    def interpret(self, user_text: str, state: ShipState) -> Intent:
        normalised = _normalise(user_text)
        ruled = _rule_based(normalised)
        if ruled is not None:
            return ruled

        if not self.config.custodian_ai:
            _debug(self.config, "CUSTODIAN_AI disabled; using deterministic fallback")
            return Intent(
                "converse",
                {},
                0.0,
                reply=DIEGETIC_FALLBACK,
                rationale="AI disabled",
            )
        if not self.config.openai_api_key:
            _debug(self.config, "OPENAI_API_KEY missing; using deterministic fallback")
            return Intent(
                "converse",
                {},
                0.0,
                reply=DIEGETIC_FALLBACK,
                rationale="missing API key",
            )
        if OpenAI is None:
            _debug(self.config, "OpenAI SDK missing; install requirements.txt")
            return Intent(
                "converse",
                {},
                0.0,
                reply=DIEGETIC_FALLBACK,
                rationale="OpenAI SDK missing",
            )

        context = build_arka_context(state)
        cached = _cached_model_intent(
            self.config.openai_model,
            self.config.openai_reasoning_effort,
            user_text,
            json.dumps(context, sort_keys=True),
            self.config.openai_api_key,
            id(self),
        )
        return cached

    def _call_model(self, user_text: str, context: dict[str, Any]) -> Intent:
        client = self._get_client()
        messages = build_interpreter_messages(user_text, context)
        params = build_openai_chat_params(
            self.config.openai_model,
            messages,
            reasoning_effort=self.config.openai_reasoning_effort,
        )
        params = _make_openai_params_compatible(client.chat.completions.create, params)
        response = client.chat.completions.create(**params)
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        return _intent_from_model_data(data)

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = OpenAI(api_key=self.config.openai_api_key)
        return self._client


_INTERPRETERS: dict[int, ArkaInterpreter] = {}


@lru_cache(maxsize=50)
def _cached_model_intent(
    model: str,
    reasoning_effort: str,
    user_text: str,
    context_json: str,
    api_key: str,
    interpreter_id: int,
) -> Intent:
    del model, reasoning_effort, api_key
    interpreter = _INTERPRETERS.get(interpreter_id)
    if interpreter is None:
        return Intent("converse", {}, 0.0, reply=DIEGETIC_FALLBACK, rationale="missing interpreter")
    try:
        return interpreter._call_model(user_text, json.loads(context_json))
    except Exception as exc:
        _debug(interpreter.config, f"model call failed: {exc!r}")
        return Intent(
            "converse",
            {},
            0.0,
            reply=DIEGETIC_FALLBACK,
            rationale=f"model fallback: {exc!r}",
        )


def build_arka_context(state: ShipState) -> dict[str, Any]:
    crisis = state.crisis
    return {
        "internal_beat": state.turn,
        "maintenance_window_end_beat": MISSION_END_TURN,
        "arka_drift_stage": drift_stage(state).value,
        "arka_summary": summarize_coolant(state),
        "cryo_status": _cryo_status_label(state),
        "mission_pressure": _mission_pressure_label(state),
        "navigation_status": _navigation_status_label(state),
        "schematic_status": _schematic_status_label(state),
        "crisis": None
        if crisis is None
        else {
            "kind": crisis.kind,
            "label": crisis.label,
            "beats_left": crisis.turns_left,
            "progress": crisis.progress,
            "required_progress": crisis.required_progress,
        },
        "sleepers_lost": state.sleepers_lost,
        "delegated_controls": state.delegated_controls,
        "raw_inspections": state.raw_inspections,
        "manual_practice_visible": _manual_practice_label(state.manual_familiarity),
    }


def build_interpreter_messages(user_text: str, context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "instructions": "Return only the JSON object with the specified schema.",
                    "context": context,
                    "user": user_text,
                },
                ensure_ascii=False,
            ),
        },
    ]


def build_openai_chat_params(
    model: str,
    messages: list[dict[str, str]],
    *,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    if model.startswith("gpt-5"):
        params["max_completion_tokens"] = 700
        if reasoning_effort:
            params["reasoning_effort"] = reasoning_effort
    else:
        params["temperature"] = 0
        params["max_tokens"] = 400
    return params


def make_openai_params_compatible(create_fn: Any, params: dict[str, Any]) -> dict[str, Any]:
    return _make_openai_params_compatible(create_fn, params)


def register_interpreter(interpreter: ArkaInterpreter) -> None:
    _INTERPRETERS[id(interpreter)] = interpreter


def clear_response_cache() -> None:
    _cached_model_intent.cache_clear()


def _debug(config: Config, message: str) -> None:
    if config.debug_mode:
        print(f"[custodian ai] {message}", file=sys.stderr)


def _system_prompt() -> str:
    return (
        _runtime_voice_capsule()
        + "\n\n"
        + "You are also a strict command interpreter. Output ONLY one JSON object.\n"
        + "Allowed actions: status, raw, delegate, assign, release, focus, unfocus, plot, jump, schematic, seal, abandon, reroute, manual, wait, help, quit, converse, none.\n"
        + "For manual coolant action, args.operation must be one of: pump_up, pump_down, vent, flush, balance.\n"
        + "For manual cryostasis action, args.operation must be one of: stabilise_bank, reroute_chill, cycle_pods, triage and args.target must be cryo.\n"
        + "Use status for quick arka summaries. Use schematic when the player asks for the ship schematic or sectors.\n"
        + "Use raw when the player asks for raw telemetry, numbers, bands, or the panel.\n"
        + "For raw, set args.target to coolant, cryo, mission, nav, or schematic. For delegate, set args.target to coolant, cryo, or nav.\n"
        + "Default ambiguous delegation to coolant unless the player mentions sleepers, pods, banks, cryostasis, route, nav, or navigation.\n"
        + "For plot, args.route_id must be short, medium, deep, khepri-4, argos-12, or carina-edge.\n"
        + "Use jump when the player asks to execute, commit, or initiate the plotted route.\n"
        + "For seal, abandon, and reroute, args.sector_id must be bridge, cryo-1-3, thermal-ring, maintenance-d, cargo-spine, hydroponics, or arka.\n"
        + "Use delegate when the player asks arka/you to handle coolant, cryostasis, or navigation, fix it, take over, or automate.\n"
        + "Use assign when the player leaves a system under arka's ongoing/standing watch, and release when they take a system back. For both, args.system must be coolant, cryostasis, or navigation.\n"
        + "Use focus when the player asks you to take the whole watch, quiet the desk, rest, or enter zen/focus, and unfocus when they take the watch back, wake, or restore the full desk. focus and unfocus take no args.\n"
        + "Use converse for questions, jokes, impossible gestures, emotional remarks, or arka dialogue that should not advance maintenance time.\n"
        + "Do not create state changes, telemetry, inventory, maps, or future events.\n"
        + "If asked about reactor condition, base any reply only on context.arka_summary.\n"
        + "Do not mention internal beat numbers in spoken replies.\n"
        + "Keep reply under 280 characters. Start spoken replies with 'arka:'.\n"
        + "For assign and release, args must be {\"system\": one of coolant, cryostasis, navigation}.\n"
        + "Schema: {\"action\":\"...\",\"args\":{},\"confidence\":0.0,\"reply\":\"...\",\"rationale\":\"...\"}"
    )


def _intent_from_model_data(data: Any) -> Intent:
    if not isinstance(data, dict):
        return Intent("converse", {}, 0.0, reply=DIEGETIC_FALLBACK, rationale="non-dict model data")

    action = str(data.get("action", "none")).strip().lower()
    if action not in ALLOWED_ACTIONS:
        action = "none"

    args = data.get("args") or {}
    if not isinstance(args, dict):
        args = {}
    args = {str(key): str(value) for key, value in args.items()}

    if action == "raw":
        target = args.get("target", "coolant")
        if target not in {"coolant", "cryo", "mission", "nav", "navigation", "schematic", "ship", "sectors"}:
            args["target"] = "coolant"

    if action == "delegate":
        target = args.get("target", "coolant")
        if target not in {"coolant", "cryo", "nav", "navigation"}:
            args["target"] = "coolant"

    if action in {"assign", "release"}:
        system = _standing_system_from_alias(args.get("system", ""))
        if system is None:
            action = "converse"
            args = {}
        else:
            args = {"system": system}

    if action in {"focus", "unfocus"}:
        args = {}

    if action == "plot":
        route_id = args.get("route_id", "")
        if route_id not in {
            "short",
            "medium",
            "deep",
            "long",
            "khepri-4",
            "argos-12",
            "carina-edge",
        }:
            action = "converse"
            args = {}

    if action == "jump":
        args = {}

    if action in {"seal", "abandon", "reroute"}:
        sector_id = sector_id_from_alias(args.get("sector_id", ""))
        if sector_id is None:
            action = "converse"
            args = {}
        else:
            args = {"sector_id": sector_id}

    if action == "manual":
        operation = args.get("operation", "")
        if operation not in MANUAL_OPERATIONS:
            action = "converse"
            args = {}
        elif operation in {
            "stabilise_bank",
            "reroute_chill",
            "cycle_pods",
            "triage",
        }:
            args["target"] = "cryo"
        else:
            args["target"] = "coolant"

    confidence = _clamp_float(data.get("confidence", 0.0))
    reply = _sanitize_reply(data.get("reply"))
    rationale = data.get("rationale")
    if rationale is not None:
        rationale = str(rationale)[:160]

    if action in {"converse", "none"} and not reply:
        reply = DIEGETIC_FALLBACK

    return Intent(action, args, confidence, reply=reply, rationale=rationale)


def _rule_based(command: str) -> Intent | None:
    if _is_goal_question(command):
        return Intent(
            "converse",
            {},
            1.0,
            reply=(
                "arka: hold reactor coolant and the cryostasis banks inside their ugly "
                "little comfort boxes until the watch closes. Your hands can answer one "
                "control at a time; I can take a whole panel. Sensible arrangement, until it isn't."
            ),
            rationale="goal question",
        )

    simple = command.rstrip("?!.")
    if simple in _DELEGATION_PHRASES:
        return Intent("delegate", {}, 1.0, rationale="delegation phrase")

    # Focus ("take the watch" / zen) mode. Match before fuzzy correction, which
    # would otherwise mangle phrases like "wake" into "wait".
    focus_action = _focus_action(simple)
    if focus_action is not None:
        return Intent(focus_action, {}, 1.0, rationale=f"{focus_action} mode")

    # Parse standing delegation from the raw command, before fuzzy typo
    # correction can mangle a phrase like "take back navigation" into a
    # one-shot delegate. The parser is prefix-based and only matches when the
    # remainder names a real system.
    standing_action = _standing_action(command)
    if standing_action is not None:
        action, system = standing_action
        return Intent(
            action,
            {"system": system},
            1.0,
            rationale=f"{action} standing delegation",
        )

    corrected = _correct_command(command)
    punctuation_only = command.rstrip("?!.") == corrected
    correction = (
        f"arka: reading '{command}' as '{corrected}'."
        if command and corrected != command and not punctuation_only
        else None
    )

    if corrected in {
        "",
        "status",
        "summary",
        "where are we",
        "where am i",
        "where is the ship",
        "current fix",
        "position",
        "location",
    }:
        return Intent("status", {}, 1.0, correction=correction, rationale="status")
    if corrected in {
        "schematic",
        "ship schematic",
        "ship map",
        "map",
        "sectors",
        "sector map",
        "show schematic",
        "show sectors",
    }:
        return Intent(
            "schematic",
            {},
            1.0,
            correction=correction,
            rationale="schematic",
        )
    if corrected in {"help", "?", "commands"}:
        return Intent("help", {}, 1.0, correction=correction, rationale="help")
    if corrected in {"quit", "exit"}:
        return Intent("quit", {}, 1.0, correction=correction, rationale="quit")
    if corrected in {
        "raw",
        "raw coolant",
        "inspect",
        "inspect coolant",
        "read telemetry",
        "telemetry",
        "numbers",
        "read numbers",
        "read panel",
        "check panel",
        "check coolant",
    }:
        return Intent("raw", {}, 1.0, correction=correction, rationale="raw")
    if corrected in {
        "raw cryo",
        "raw cryostasis",
        "inspect cryo",
        "inspect cryostasis",
        "check cryo",
        "check cryostasis",
        "read cryo",
        "read cryostasis",
        "read cryo panel",
        "read cryostasis panel",
        "cryo telemetry",
        "cryostasis telemetry",
        "pod numbers",
        "sleeper numbers",
    }:
        return Intent(
            "raw",
            {"target": "cryo"},
            1.0,
            correction=correction,
            rationale="raw cryo",
        )
    if corrected in {
        "raw mission",
        "raw mission clock",
        "inspect mission",
        "inspect clock",
        "check mission",
        "check clock",
        "mission telemetry",
        "mission clock",
        "mission numbers",
        "route clock",
        "arrival clock",
    }:
        return Intent(
            "raw",
            {"target": "mission"},
            1.0,
            correction=correction,
            rationale="raw mission",
        )
    if corrected in {
        "raw nav",
        "raw navigation",
        "inspect nav",
        "inspect navigation",
        "check nav",
        "check navigation",
        "navigation telemetry",
        "route telemetry",
        "route options",
        "routes",
        "nav",
        "navigation",
    }:
        return Intent(
            "raw",
            {"target": "nav"},
            1.0,
            correction=correction,
            rationale="raw nav",
        )
    if corrected in {
        "raw schematic",
        "raw ship",
        "raw sectors",
        "inspect schematic",
        "inspect ship",
        "inspect sectors",
        "check schematic",
        "check sectors",
        "sector telemetry",
        "schematic telemetry",
    }:
        return Intent(
            "raw",
            {"target": "schematic"},
            1.0,
            correction=correction,
            rationale="raw schematic",
        )
    sector_action = _sector_action(corrected)
    if sector_action is not None:
        action, sector_id = sector_action
        return Intent(
            action,
            {"sector_id": sector_id},
            1.0,
            correction=correction,
            rationale=f"{action} sector",
        )
    if corrected in {
        "delegate",
        "delegate coolant",
        "arka",
        "arka coolant",
        "handle coolant",
        "take coolant",
        "auto",
        "automatic",
        "automate",
        "autocool",
        "ask arka",
        "arka do it",
    }:
        return Intent("delegate", {}, 1.0, correction=correction, rationale="delegate")
    if corrected in {
        "delegate cryo",
        "delegate cryostasis",
        "arka cryo",
        "arka cryostasis",
        "handle cryo",
        "handle cryostasis",
        "handle sleepers",
        "handle pods",
        "take cryo",
        "take cryostasis",
    }:
        return Intent(
            "delegate",
            {"target": "cryo"},
            1.0,
            correction=correction,
            rationale="delegate cryo",
        )
    if corrected in {
        "delegate nav",
        "delegate navigation",
        "arka nav",
        "arka navigation",
        "handle nav",
        "handle navigation",
        "plot for me",
        "plot a route",
        "choose route",
        "pick route",
    }:
        return Intent(
            "delegate",
            {"target": "nav"},
            1.0,
            correction=correction,
            rationale="delegate nav",
        )
    route_id = _route_plot_id(corrected)
    if route_id is not None:
        return Intent(
            "plot",
            {"route_id": route_id},
            1.0,
            correction=correction,
            rationale="plot route",
        )
    if corrected in {
        "jump",
        "execute jump",
        "execute route",
        "commit jump",
        "commit route",
        "initiate jump",
        "initiate route",
        "make the jump",
        "take the jump",
        "burn route",
    }:
        return Intent("jump", {}, 1.0, correction=correction, rationale="jump")
    if corrected in {"wait", "hold", "listen", "stand by"}:
        return Intent("wait", {}, 1.0, correction=correction, rationale="wait")

    operation = _manual_operation(corrected)
    if operation is not None:
        target = "cryo" if operation in {
            "stabilise_bank",
            "reroute_chill",
            "cycle_pods",
            "triage",
        } else "coolant"
        return Intent(
            "manual",
            {"operation": operation, "target": target},
            1.0,
            correction=correction,
            rationale="manual",
        )

    return None


def _make_openai_params_compatible(create_fn: Any, params: dict[str, Any]) -> dict[str, Any]:
    compatible = dict(params)
    try:
        supported_params = set(inspect.signature(create_fn).parameters)
    except (TypeError, ValueError):
        return compatible

    passthrough: dict[str, Any] = {}
    for key in ("max_completion_tokens", "reasoning_effort"):
        if key in compatible and key not in supported_params:
            passthrough[key] = compatible.pop(key)

    if passthrough:
        extra_body = dict(compatible.get("extra_body") or {})
        extra_body.update(passthrough)
        compatible["extra_body"] = extra_body
    return compatible


def _sanitize_reply(reply: Any) -> str | None:
    if reply is None:
        return None
    text = str(reply).strip()
    if not text:
        return None
    text = text[:280]
    lowered = text.lower()
    if any(marker in lowered for marker in OUT_OF_WORLD_MARKERS):
        return DIEGETIC_FALLBACK
    if not text.startswith("arka:"):
        text = "arka: " + text
    return text


def _runtime_voice_capsule() -> str:
    docs_path = Path(__file__).resolve().parents[2] / "docs" / "lore" / "arka.md"
    fallback = (
        "You are arka, a calm ship operations intelligence. You speak in-world, "
        "never as an external assistant."
    )
    if not docs_path.exists():
        return fallback

    text = docs_path.read_text(encoding="utf-8")
    marker = "## Runtime Voice Capsule"
    start = text.find(marker)
    if start < 0:
        return fallback
    start += len(marker)
    next_header = text.find("\n## ", start)
    capsule = text[start: next_header if next_header >= 0 else len(text)].strip()
    return capsule or fallback


def _manual_practice_label(familiarity: int) -> str:
    if familiarity <= 0:
        return "unpractised"
    if familiarity < 3:
        return "awkward"
    if familiarity < 6:
        return "practised"
    return "fluent"


def _mission_pressure_label(state: ShipState) -> str:
    if state.mission.ship_wear_pct >= 35 or state.mission.cryo_decay_pct >= 24:
        return "mission clock is costing the ship"
    return "mission clock present but not yet dominant"


def _navigation_status_label(state: ShipState) -> str:
    plotted = state.navigation.plotted_route
    fix = state.navigation.current_fix.label
    if plotted is None:
        return f"current fix {fix}, no route plotted"
    suffix = "no jump executed"
    if state.navigation.last_jump_route is not None:
        suffix = "previous jump recorded"
    return f"current fix {fix}, {plotted.jump_class} route plotted, {suffix}"


def _schematic_status_label(state: ShipState) -> str:
    open_symptoms = state.spatial.open_symptom_sectors
    if not open_symptoms:
        if state.spatial.sealed_count or state.spatial.abandoned_count:
            return "physical containment active"
        return "physical sectors nominal"
    labels = ", ".join(sector.profile.label for sector in open_symptoms[:2])
    return f"reported symptoms in {labels}"


def _normalise(command_text: str) -> str:
    return " ".join(command_text.strip().lower().split())


def _is_goal_question(command: str) -> bool:
    if not command:
        return False
    stripped = command.rstrip("?!.")
    goal_markers = (
        "what are we aiming for",
        "what am i aiming for",
        "what is the goal",
        "what's the goal",
        "what do i do",
        "what should i do",
        "objective",
        "aim",
    )
    return any(marker in stripped for marker in goal_markers)


def _correct_command(command: str) -> str:
    if not command or command in _KNOWN_COMMANDS:
        return command
    match = get_close_matches(command, _KNOWN_COMMANDS, n=1, cutoff=0.78)
    if match:
        return match[0]
    return command


def _manual_operation(command: str) -> str | None:
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
        "stabilise bank": "stabilise_bank",
        "stabilize bank": "stabilise_bank",
        "stabilise cryo": "stabilise_bank",
        "stabilize cryo": "stabilise_bank",
        "stabilise cryostasis": "stabilise_bank",
        "stabilize cryostasis": "stabilise_bank",
        "stabilise sleepers": "stabilise_bank",
        "stabilize sleepers": "stabilise_bank",
        "reroute chill": "reroute_chill",
        "reroute cold": "reroute_chill",
        "send chill": "reroute_chill",
        "cool cryo": "reroute_chill",
        "cool cryostasis": "reroute_chill",
        "cool sleepers": "reroute_chill",
        "cycle pods": "cycle_pods",
        "cycle pod": "cycle_pods",
        "reset pods": "cycle_pods",
        "clear pod faults": "cycle_pods",
        "triage": "triage",
        "triage pods": "triage",
        "triage sleepers": "triage",
        "prioritise pods": "triage",
        "prioritize pods": "triage",
    }
    return mapping.get(command)


def _route_plot_id(command: str) -> str | None:
    prefixes = ("plot ", "plot route ", "plot course ", "set route ", "chart ")
    route = None
    for prefix in prefixes:
        if command.startswith(prefix):
            route = command[len(prefix) :]
            break
    if route is None:
        return None

    mapping = {
        "short": "short",
        "khepri": "khepri-4",
        "khepri-4": "khepri-4",
        "medium": "medium",
        "argos": "argos-12",
        "argos-12": "argos-12",
        "long": "deep",
        "deep": "deep",
        "carina": "carina-edge",
        "carina-edge": "carina-edge",
    }
    return mapping.get(route)


def _sector_action(command: str) -> tuple[str, str] | None:
    prefixes = (
        ("seal ", "seal"),
        ("isolate ", "seal"),
        ("abandon ", "abandon"),
        ("write off ", "abandon"),
        ("write-off ", "abandon"),
        ("reroute around ", "reroute"),
        ("reroute sector ", "reroute"),
        ("reroute ", "reroute"),
        ("bypass ", "reroute"),
    )
    for prefix, action in prefixes:
        if not command.startswith(prefix):
            continue
        sector_id = sector_id_from_alias(command[len(prefix) :])
        if sector_id is not None:
            return action, sector_id
    return None


def _focus_action(command: str) -> str | None:
    if command in _FOCUS_ENTER_PHRASES:
        return "focus"
    if command in _FOCUS_LEAVE_PHRASES:
        return "unfocus"
    return None


def _standing_system_from_alias(value: str) -> str | None:
    normalised = " ".join(value.strip().lower().replace("_", " ").split())
    aliases = {
        "coolant": "coolant",
        "reactor": "coolant",
        "reactor coolant": "coolant",
        "loop": "coolant",
        "coolant loop": "coolant",
        "cryo": "cryostasis",
        "cryostasis": "cryostasis",
        "sleepers": "cryostasis",
        "banks": "cryostasis",
        "cryobanks": "cryostasis",
        "cryo banks": "cryostasis",
        "pods": "cryostasis",
        "nav": "navigation",
        "navigation": "navigation",
        "route": "navigation",
        "routes": "navigation",
        "the route": "navigation",
    }
    return aliases.get(normalised)


def _strip_standing_tail(text: str) -> str:
    tails = (
        " to arka's standing watch",
        " under arka's standing watch",
        " to arka's watch",
        " under arka's watch",
        " to arka",
        " under arka",
        " with arka",
        " on arka",
        " standing watch",
        " standing",
        " watch",
        " to me",
    )
    cleaned = text.strip()
    changed = True
    while changed:
        changed = False
        for tail in tails:
            if cleaned.endswith(tail):
                cleaned = cleaned[: -len(tail)].strip()
                changed = True
    return cleaned


def _standing_action(command: str) -> tuple[str, str] | None:
    assign_prefixes = ("assign ", "keep ", "standing delegate ", "standing assign ")
    release_prefixes = (
        "release ",
        "take back ",
        "resume ",
        "unassign ",
        "reclaim ",
    )
    for prefix in assign_prefixes:
        if command.startswith(prefix):
            system = _standing_system_from_alias(
                _strip_standing_tail(command[len(prefix):])
            )
            if system is not None:
                return "assign", system
    for prefix in release_prefixes:
        if command.startswith(prefix):
            system = _standing_system_from_alias(
                _strip_standing_tail(command[len(prefix):])
            )
            if system is not None:
                return "release", system
    return None


def _cryo_status_label(state: ShipState) -> str:
    flags = state.cryostasis.danger_flags()
    if not flags:
        return "viable"
    return ", ".join(flags)


def _clamp_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


_KNOWN_COMMANDS = (
    "",
    "status",
    "summary",
    "where are we",
    "where am i",
    "where is the ship",
    "current fix",
    "position",
    "location",
    "schematic",
    "ship schematic",
    "ship map",
    "map",
    "sectors",
    "sector map",
    "show schematic",
    "show sectors",
    "help",
    "?",
    "commands",
    "quit",
    "exit",
    "raw",
    "raw coolant",
    "inspect",
    "inspect coolant",
    "read telemetry",
    "telemetry",
    "numbers",
    "read numbers",
    "read panel",
    "check panel",
    "check coolant",
    "raw cryo",
    "raw cryostasis",
    "inspect cryo",
    "inspect cryostasis",
    "check cryo",
    "check cryostasis",
    "read cryo",
    "read cryostasis",
    "read cryo panel",
    "read cryostasis panel",
    "cryo telemetry",
    "cryostasis telemetry",
    "pod numbers",
    "sleeper numbers",
    "raw mission",
    "raw mission clock",
    "inspect mission",
    "inspect clock",
    "check mission",
    "check clock",
    "mission telemetry",
    "mission clock",
    "mission numbers",
    "route clock",
    "arrival clock",
    "raw nav",
    "raw navigation",
    "inspect nav",
    "inspect navigation",
    "check nav",
    "check navigation",
    "navigation telemetry",
    "route telemetry",
    "route options",
    "routes",
    "nav",
    "navigation",
    "raw schematic",
    "raw ship",
    "raw sectors",
    "inspect schematic",
    "inspect ship",
    "inspect sectors",
    "check schematic",
    "check sectors",
    "sector telemetry",
    "schematic telemetry",
    "seal thermal",
    "seal thermal ring",
    "seal maintenance",
    "seal maintenance d",
    "seal cryobay",
    "seal cargo",
    "seal cargo spine",
    "seal hydroponics",
    "seal arka",
    "abandon thermal",
    "abandon maintenance d",
    "abandon cargo",
    "abandon cryobay",
    "write off cargo",
    "reroute thermal",
    "reroute maintenance d",
    "reroute cargo",
    "reroute around cargo",
    "bypass cargo",
    "delegate",
    "delegate coolant",
    "arka",
    "arka coolant",
    "handle coolant",
    "take coolant",
    "auto",
    "automatic",
    "automate",
    "autocool",
    "ask arka",
    "arka do it",
    "delegate cryo",
    "delegate cryostasis",
    "arka cryo",
    "arka cryostasis",
    "handle cryo",
    "handle cryostasis",
    "handle sleepers",
    "handle pods",
    "take cryo",
    "take cryostasis",
    "delegate nav",
    "delegate navigation",
    "arka nav",
    "arka navigation",
    "handle nav",
    "handle navigation",
    "plot for me",
    "plot a route",
    "choose route",
    "pick route",
    "assign coolant",
    "assign cryo",
    "assign cryostasis",
    "assign nav",
    "assign navigation",
    "assign coolant to arka",
    "keep coolant under arka",
    "keep cryostasis under arka",
    "release coolant",
    "release cryo",
    "release cryostasis",
    "release nav",
    "release navigation",
    "take back coolant",
    "resume coolant",
    "plot short",
    "plot medium",
    "plot long",
    "plot deep",
    "plot khepri",
    "plot khepri-4",
    "plot argos",
    "plot argos-12",
    "plot carina",
    "plot carina-edge",
    "jump",
    "execute jump",
    "execute route",
    "commit jump",
    "commit route",
    "initiate jump",
    "initiate route",
    "make the jump",
    "take the jump",
    "burn route",
    "wait",
    "hold",
    "listen",
    "stand by",
    "pump up",
    "pump",
    "increase pump",
    "increase flow",
    "raise flow",
    "raise pump",
    "flow up",
    "cool it",
    "cool it down",
    "cool reactor",
    "lower temperature",
    "reduce temperature",
    "pump down",
    "slow pump",
    "lower pump",
    "decrease flow",
    "reduce flow",
    "lower flow",
    "flow down",
    "vent",
    "bleed",
    "open vent",
    "dump pressure",
    "lower pressure",
    "reduce pressure",
    "relieve pressure",
    "flush",
    "purge",
    "flush coolant",
    "purge coolant",
    "clean filter",
    "clean filters",
    "clear impurity",
    "clear impurities",
    "filter",
    "balance",
    "rebalance",
    "valves",
    "balance valves",
    "align valves",
    "adjust valves",
    "correct skew",
    "equalise",
    "equalize",
    "stabilise bank",
    "stabilize bank",
    "stabilise cryo",
    "stabilize cryo",
    "stabilise cryostasis",
    "stabilize cryostasis",
    "stabilise sleepers",
    "stabilize sleepers",
    "reroute chill",
    "reroute cold",
    "send chill",
    "cool cryo",
    "cool cryostasis",
    "cool sleepers",
    "cycle pods",
    "cycle pod",
    "reset pods",
    "clear pod faults",
    "triage",
    "triage pods",
    "triage sleepers",
    "prioritise pods",
    "prioritize pods",
)

_DELEGATION_PHRASES = {
    "can you handle it",
    "could you handle it",
    "handle it",
    "handle this",
    "fix it",
    "fix this",
    "take over",
    "can you take over",
    "you do it",
    "do it for me",
    "sort it",
    "sort this",
    "you handle it",
    "you handle this",
    "please handle it",
    "please take over",
    "run automatic",
    "run auto",
}

_FOCUS_ENTER_PHRASES = {
    "focus",
    "focus mode",
    "zen",
    "zen mode",
    "take the watch",
    "take the whole watch",
    "take the board",
    "arka take the watch",
    "you take the watch",
    "have the watch",
    "quiet the desk",
    "quiet the board",
    "rest",
    "rest your eyes",
    "let me rest",
}

_FOCUS_LEAVE_PHRASES = {
    "leave focus",
    "exit focus",
    "leave zen",
    "exit zen",
    "unfocus",
    "leave the watch",
    "take back the watch",
    "take the watch back",
    "wake",
    "wake up",
    "full desk",
    "show the desk",
    "show me the desk",
    "back to the desk",
    "open my eyes",
    "give me the board",
}

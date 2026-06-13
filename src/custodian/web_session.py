from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from time import monotonic
from typing import Callable
from uuid import uuid4

from custodian.engine import GameEngine
from custodian.models import ShipState
from custodian.narrative import closing_lines, opening_lines
from custodian.persistence import dumps, load_state, loads, save_state
from custodian.ui_snapshot import project_safe_lines, project_ui_snapshot


OVERSIZE_COMMAND_MESSAGE = (
    "arka: Too much is arriving on that channel. Cut it to one instruction and "
    "send again."
)
THROTTLED_COMMAND_MESSAGE = (
    "arka: Slow the channel. I can keep the board steady, but not if every "
    "light speaks at once."
)
SESSION_CAPACITY_MESSAGE = (
    "arka: No free console lanes. Let a silent session go cold and try again."
)


@dataclass(frozen=True)
class WebSessionLimits:
    max_command_chars: int = 200
    rate_window_seconds: float = 10.0
    max_session_commands: int = 12
    max_client_commands: int = 30
    max_sessions: int = 32
    idle_session_seconds: float = 30.0 * 60.0


@dataclass(frozen=True)
class TranscriptEvent:
    kind: str
    lines: tuple[str, ...]
    beat: int

    def to_dict(self) -> dict:
        return {"kind": self.kind, "lines": list(self.lines), "beat": self.beat}


@dataclass(frozen=True)
class CommandResponse:
    session_id: str
    messages: tuple[str, ...]
    snapshot: dict


class SessionNotFound(KeyError):
    pass


class SessionCapacityExceeded(RuntimeError):
    pass


class BrowserSession:
    def __init__(
        self,
        session_id: str,
        engine: GameEngine,
        state: ShipState | None = None,
        *,
        last_access: float = 0.0,
    ) -> None:
        self.session_id = session_id
        self.engine = engine
        self.state = state or engine.initial_state()
        self.last_access = last_access
        self._lock = RLock()
        self.status_messages = _status_messages(engine, self.state)
        self.last_messages = opening_lines() + self.status_messages
        self.transcript: list[TranscriptEvent] = [
            TranscriptEvent("output", self.last_messages, self.state.turn)
        ]

    def touch(self, now: float) -> None:
        with self._lock:
            self.last_access = now

    def snapshot(self, *, include_dev: bool = False) -> dict:
        with self._lock:
            status_lines = self.status_messages
            transcript_tail = tuple(self.transcript_lines(limit=120))
            ui = project_ui_snapshot(
                self.state,
                last_messages=self.last_messages,
                transcript_tail=transcript_tail,
                include_dev=include_dev,
            ).to_dict()
            return {
                "session_id": self.session_id,
                "turn": self.state.turn,
                "is_finished": self.state.is_finished,
                "outcome": self.state.outcome,
                "status": list(project_safe_lines(self.state, status_lines)),
                "last_messages": list(project_safe_lines(self.state, self.last_messages)),
                "transcript_tail": [entry["text"] for entry in ui["transcript_tail"]],
                "history": [asdict(record) for record in self.state.history[-20:]],
                "ui": ui,
            }

    def command(self, command_text: str) -> CommandResponse:
        with self._lock:
            command = command_text.strip()
            was_finished = self.state.is_finished
            self.transcript.append(TranscriptEvent("input", (command,), self.state.turn))

            result = self.engine.handle(self.state, command)
            self.state = result.state
            messages = result.messages
            if self.state.is_finished and not was_finished:
                messages = messages + closing_lines(self.state)
            self.status_messages = _status_messages(self.engine, self.state)
            self.last_messages = messages
            self.transcript.append(TranscriptEvent("output", messages, self.state.turn))
            safe_messages = project_safe_lines(self.state, messages)
            return CommandResponse(self.session_id, safe_messages, self.snapshot())

    def reject_command(
        self,
        command_text: str,
        message: str,
        *,
        max_command_chars: int = WebSessionLimits.max_command_chars,
    ) -> CommandResponse:
        with self._lock:
            command = _transcript_command(command_text, max_chars=max_command_chars)
            self.transcript.append(TranscriptEvent("input", (command,), self.state.turn))
            self.last_messages = (message,)
            self.transcript.append(TranscriptEvent("output", self.last_messages, self.state.turn))
            safe_messages = project_safe_lines(self.state, self.last_messages)
            return CommandResponse(self.session_id, safe_messages, self.snapshot())

    def save(self, path: Path | None = None) -> dict:
        with self._lock:
            text = dumps(self.state)
            if path is not None:
                save_state(self.state, path)
            return {
                "session_id": self.session_id,
                "save": text,
                "path": None if path is None else str(path),
                "snapshot": self.snapshot(),
            }

    def load(self, *, text: str | None = None, path: Path | None = None) -> dict:
        with self._lock:
            if text is None and path is None:
                raise ValueError("load requires save text or path")
            if text is not None:
                self.state = loads(text)
            else:
                assert path is not None
                self.state = load_state(path)
            self.last_messages = (
                "arka: Session image restored. Same ship, fewer fresh mistakes.",
                f"maintenance beat restored: {self.state.turn}",
            )
            self.status_messages = _status_messages(self.engine, self.state)
            self.transcript.append(
                TranscriptEvent("output", self.last_messages, self.state.turn)
            )
            return {"session_id": self.session_id, "snapshot": self.snapshot()}

    def transcript_events(self) -> tuple[dict, ...]:
        with self._lock:
            return tuple(event.to_dict() for event in self.transcript)

    def transcript_lines(self, *, limit: int | None = None) -> list[str]:
        with self._lock:
            lines: list[str] = []
            for event in self.transcript:
                if event.kind == "input":
                    lines.append(f"> {event.lines[0] if event.lines else ''}")
                else:
                    lines.extend(event.lines)
            if limit is not None and len(lines) > limit:
                return lines[-limit:]
            return lines


class SessionStore:
    def __init__(
        self,
        engine_factory: Callable[[], GameEngine] | None = None,
        *,
        limits: WebSessionLimits | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._engine_factory = engine_factory or GameEngine
        self._limits = limits or WebSessionLimits()
        self._clock = clock or monotonic
        self._lock = RLock()
        self._sessions: dict[str, BrowserSession] = {}
        self._session_attempts: dict[str, list[float]] = {}
        self._client_attempts: dict[str, list[float]] = {}

    def create(self) -> BrowserSession:
        with self._lock:
            now = self._clock()
            self._purge_idle(now)
            if len(self._sessions) >= self._limits.max_sessions:
                raise SessionCapacityExceeded(SESSION_CAPACITY_MESSAGE)
            session = BrowserSession(
                uuid4().hex,
                self._engine_factory(),
                last_access=now,
            )
            self._sessions[session.session_id] = session
            return session

    def get(self, session_id: str) -> BrowserSession:
        with self._lock:
            now = self._clock()
            self._purge_idle(now)
            session = self._get_existing(session_id)
            session.touch(now)
            return session

    def snapshot(self, session_id: str, *, include_dev: bool = False) -> dict:
        return self.get(session_id).snapshot(include_dev=include_dev)

    def command(
        self,
        session_id: str,
        command_text: str,
        *,
        client_id: str | None = None,
    ) -> CommandResponse:
        with self._lock:
            now = self._clock()
            self._purge_idle(now)
            session = self._get_existing(session_id)
            session.touch(now)
            rejection = self._command_rejection(
                session_id,
                client_id or "local",
                command_text,
                now,
            )
        if rejection is not None:
            return session.reject_command(
                command_text,
                rejection,
                max_command_chars=self._limits.max_command_chars,
            )
        return session.command(command_text)

    def save(self, session_id: str, path: Path | None = None) -> dict:
        return self.get(session_id).save(path)

    def load(
        self,
        session_id: str,
        *,
        text: str | None = None,
        path: Path | None = None,
    ) -> dict:
        return self.get(session_id).load(text=text, path=path)

    def transcript(self, session_id: str) -> dict:
        session = self.get(session_id)
        return {
            "session_id": session_id,
            "events": list(session.transcript_events()),
            "lines": session.transcript_lines(),
        }

    def _get_existing(self, session_id: str) -> BrowserSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise SessionNotFound(session_id) from exc

    def _purge_idle(self, now: float) -> None:
        idle_after = self._limits.idle_session_seconds
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if now - session.last_access > idle_after
        ]
        for session_id in expired:
            self._sessions.pop(session_id, None)
            self._session_attempts.pop(session_id, None)
        self._purge_attempts(self._session_attempts, now)
        self._purge_attempts(self._client_attempts, now)

    def _purge_attempts(self, buckets: dict[str, list[float]], now: float) -> None:
        window = self._limits.rate_window_seconds
        for key, timestamps in list(buckets.items()):
            recent = [then for then in timestamps if now - then < window]
            if recent:
                buckets[key] = recent
            else:
                buckets.pop(key, None)

    def _command_rejection(
        self,
        session_id: str,
        client_id: str,
        command_text: str,
        now: float,
    ) -> str | None:
        if self._over_rate(
            self._session_attempts,
            session_id,
            self._limits.max_session_commands,
            now,
        ):
            return THROTTLED_COMMAND_MESSAGE
        if self._over_rate(
            self._client_attempts,
            client_id,
            self._limits.max_client_commands,
            now,
        ):
            return THROTTLED_COMMAND_MESSAGE
        if len(command_text) > self._limits.max_command_chars:
            return OVERSIZE_COMMAND_MESSAGE
        return None

    def _over_rate(
        self,
        buckets: dict[str, list[float]],
        key: str,
        limit: int,
        now: float,
    ) -> bool:
        if limit <= 0:
            return True
        window = self._limits.rate_window_seconds
        recent = [then for then in buckets.get(key, []) if now - then < window]
        if len(recent) >= limit:
            buckets[key] = recent
            return True
        recent.append(now)
        buckets[key] = recent
        return False


def _status_messages(engine: GameEngine, state: ShipState) -> tuple[str, ...]:
    # The CLI already treats status as a presentation read without committing the
    # returned history record during startup. The browser shell does the same.
    return engine.handle(state, "status").messages


def _transcript_command(command_text: str, *, max_chars: int) -> str:
    command = command_text.strip()
    if len(command) <= max_chars:
        return command
    return f"{command[:max_chars]} ... signal clipped"

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Callable
from uuid import uuid4

from custodian.engine import GameEngine
from custodian.models import ShipState
from custodian.narrative import closing_lines, opening_lines
from custodian.persistence import dumps, load_state, loads, save_state


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


class BrowserSession:
    def __init__(
        self,
        session_id: str,
        engine: GameEngine,
        state: ShipState | None = None,
    ) -> None:
        self.session_id = session_id
        self.engine = engine
        self.state = state or engine.initial_state()
        self._lock = RLock()
        self.last_messages = _initial_messages(engine, self.state)
        self.transcript: list[TranscriptEvent] = [
            TranscriptEvent("output", self.last_messages, self.state.turn)
        ]

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "session_id": self.session_id,
                "turn": self.state.turn,
                "is_finished": self.state.is_finished,
                "outcome": self.state.outcome,
                "status": list(_status_messages(self.engine, self.state)),
                "last_messages": list(self.last_messages),
                "transcript_tail": self.transcript_lines(limit=120),
                "history": [asdict(record) for record in self.state.history[-20:]],
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
            self.last_messages = messages
            self.transcript.append(TranscriptEvent("output", messages, self.state.turn))
            return CommandResponse(self.session_id, messages, self.snapshot())

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
    def __init__(self, engine_factory: Callable[[], GameEngine] | None = None) -> None:
        self._engine_factory = engine_factory or GameEngine
        self._sessions: dict[str, BrowserSession] = {}

    def create(self) -> BrowserSession:
        session = BrowserSession(uuid4().hex, self._engine_factory())
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> BrowserSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise SessionNotFound(session_id) from exc

    def snapshot(self, session_id: str) -> dict:
        return self.get(session_id).snapshot()

    def command(self, session_id: str, command_text: str) -> CommandResponse:
        return self.get(session_id).command(command_text)

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


def _initial_messages(engine: GameEngine, state: ShipState) -> tuple[str, ...]:
    return opening_lines() + _status_messages(engine, state)


def _status_messages(engine: GameEngine, state: ShipState) -> tuple[str, ...]:
    # The CLI already treats status as a presentation read without committing the
    # returned history record during startup. The browser shell does the same.
    return engine.handle(state, "status").messages

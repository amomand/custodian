from __future__ import annotations

from custodian.engine import GameEngine


INTRO = (
    "A.R.K.A coolant maintenance console online.",
    "You are the only waking custodian. arka is already being helpful.",
    "Type help for commands.",
)


def main() -> None:
    engine = GameEngine()
    state = engine.initial_state()

    for line in INTRO:
        print(line)
    for line in engine.handle(state, "status").messages:
        print(line)

    while not state.is_finished:
        try:
            command = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            command = "quit"

        result = engine.handle(state, command)
        state = result.state
        for line in result.messages:
            print(line)


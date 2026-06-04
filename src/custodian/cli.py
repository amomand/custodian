from __future__ import annotations

from custodian.engine import GameEngine
from custodian.narrative import closing_lines, opening_lines


def main() -> None:
    engine = GameEngine()
    state = engine.initial_state()

    for line in opening_lines():
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
        if state.is_finished:
            for line in closing_lines(state):
                print(line)

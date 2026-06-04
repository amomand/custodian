from __future__ import annotations

import os
import sys

from custodian.engine import GameEngine
from custodian.narrative import closing_lines, opening_lines


def main() -> None:
    engine = GameEngine()
    state = engine.initial_state()

    _clear_screen()
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
        should_refresh = result.presentation_break or (
            result.advanced and _refresh_each_turn()
        )
        if should_refresh:
            cleared = _clear_screen()
            if cleared:
                print(f"> {command}")
            elif not sys.stdout.isatty():
                print(command)
        for line in result.messages:
            print(line)
        if state.is_finished:
            for line in closing_lines(state):
                print(line)


def _clear_screen() -> bool:
    if not sys.stdout.isatty():
        return False
    if os.getenv("CUSTODIAN_CLEAR", "on").strip().lower() in {"0", "false", "no", "off"}:
        return False
    print("\033[2J\033[H", end="")
    return True


def _refresh_each_turn() -> bool:
    return os.getenv("CUSTODIAN_REFRESH", "on").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }

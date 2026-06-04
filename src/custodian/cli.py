from __future__ import annotations

import os
import sys

from custodian.engine import GameEngine
from custodian.narrative import closing_lines, opening_lines


def main() -> None:
    engine = GameEngine()
    state = engine.initial_state()

    _clear_screen()
    _print_lines(opening_lines())
    _print_lines(engine.handle(state, "status").messages)

    while not state.is_finished:
        try:
            command = _read_command()
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
        _print_lines(result.messages)
        if state.is_finished:
            _print_lines(closing_lines(state))


def _print_lines(lines: tuple[str, ...]) -> None:
    for line in _lines_with_arka_spacing(lines):
        print(line)


def _lines_with_arka_spacing(lines: tuple[str, ...]) -> tuple[str, ...]:
    spaced: list[str] = []
    for line in lines:
        arka_line = line.startswith("arka:")
        if arka_line and spaced and spaced[-1] != "":
            spaced.append("")
        if line == "" and spaced and spaced[-1] == "":
            continue
        spaced.append(line)
        if arka_line:
            spaced.append("")
    return tuple(spaced)


def _read_command() -> str:
    if sys.stdin.isatty():
        return input("> ")
    command = input()
    print(f"> {command}")
    return command


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

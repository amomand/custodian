from __future__ import annotations

import os
import sys
from pathlib import Path

from custodian.engine import GameEngine
from custodian.narrative import boot_lines, closing_lines, opening_lines
from custodian.persistence import DEFAULT_SAVE_PATH, load_state, save_state


COMMAND_COMPLETIONS = (
    "status",
    "raw",
    "raw cryo",
    "raw mission",
    "raw nav",
    "delegate",
    "delegate cryo",
    "delegate nav",
    "plot shallow",
    "plot short",
    "plot medium",
    "plot deep",
    "plot khepri-4 shallow",
    "plot khepri-4 medium",
    "plot khepri-4 deep",
    "plot argos-12 shallow",
    "plot argos-12 medium",
    "plot argos-12 deep",
    "plot carina-edge shallow",
    "plot carina-edge medium",
    "plot carina-edge deep",
    "jump",
    "pump up",
    "pump down",
    "vent",
    "flush",
    "balance",
    "stabilise bank",
    "stabilize bank",
    "reroute chill",
    "cycle pods",
    "triage",
    "wait",
    "help",
    "quit",
)


def main() -> None:
    engine = GameEngine()
    state = engine.initial_state()
    _configure_completion()

    _show_boot_screen()
    _clear_screen()
    _print_lines(opening_lines())
    _print_lines(engine.handle(state, "status").messages)

    while not state.is_finished:
        try:
            command = _read_command()
        except (EOFError, KeyboardInterrupt):
            print()
            command = "quit"

        persistence = _handle_persistence(command, state)
        if persistence is not None:
            state, lines = persistence
            _print_lines(lines)
            continue

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


def _handle_persistence(command: str, state):
    stripped = command.strip()
    head = stripped.split(maxsplit=1)
    if not head or head[0] not in {":save", ":load"}:
        return None

    path = Path(head[1].strip()) if len(head) > 1 and head[1].strip() else DEFAULT_SAVE_PATH
    if head[0] == ":save":
        try:
            save_state(state, path)
        except OSError as error:
            return state, (f"SAVE FAILED: {error}",)
        return state, (f"SAVED to {path}",)

    try:
        loaded = load_state(path)
    except (OSError, ValueError, KeyError) as error:
        return state, (f"LOAD FAILED: {error}",)
    return loaded, (f"LOADED from {path}", f"internal beat restored: {loaded.turn}")


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


def _configure_completion() -> bool:
    if not sys.stdin.isatty():
        return False
    if os.getenv("CUSTODIAN_COMPLETE", "on").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return False

    try:
        import readline
    except ImportError:
        return False

    delimiters = readline.get_completer_delims()
    readline.set_completer_delims(delimiters.replace(" ", ""))
    readline.set_completer(_complete_command)
    if "libedit" in (getattr(readline, "__doc__", "") or ""):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    return True


def _complete_command(text: str, state: int) -> str | None:
    matches = tuple(command for command in COMMAND_COMPLETIONS if command.startswith(text))
    if state >= len(matches):
        return None
    return matches[state]


def _show_boot_screen() -> bool:
    if not _should_show_boot_screen():
        return False
    _clear_screen()
    _print_lines(boot_lines())
    _wait_for_key()
    return True


def _should_show_boot_screen() -> bool:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    return os.getenv("CUSTODIAN_BOOT", "on").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _wait_for_key() -> None:
    if not sys.stdin.isatty():
        return
    try:
        import termios
        import tty
    except ImportError:
        _wait_for_enter()
        return

    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (termios.error, OSError, EOFError):
        _wait_for_enter()


def _wait_for_enter() -> None:
    try:
        input("")
    except EOFError:
        pass


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

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from custodian.cli import (
    _complete_command,
    _configure_completion,
    _lines_with_arka_spacing,
    _should_show_boot_screen,
)


class CliTests(unittest.TestCase):
    def test_arka_lines_get_breathing_room(self) -> None:
        lines = (
            "COOLANT LOOP",
            "TEMP 588 C OK",
            "arka: coolant loop nominal.",
            "CRYOSTASIS",
            "arka: cryostasis viable.",
            "arka: I can keep the banks quiet.",
            "done",
        )

        spaced = _lines_with_arka_spacing(lines)

        self.assertEqual(
            spaced,
            (
                "COOLANT LOOP",
                "TEMP 588 C OK",
                "",
                "arka: coolant loop nominal.",
                "",
                "CRYOSTASIS",
                "",
                "arka: cryostasis viable.",
                "",
                "arka: I can keep the banks quiet.",
                "",
                "done",
            ),
        )

    def test_command_completion_matches_multi_word_controls(self) -> None:
        self.assertEqual(_complete_command("rer", 0), "reroute chill")
        self.assertEqual(_complete_command("delegate c", 0), "delegate cryo")
        self.assertEqual(_complete_command("delegate c", 1), None)

    def test_completion_can_be_disabled(self) -> None:
        tty_stdin = SimpleNamespace(isatty=lambda: True)
        with patch("custodian.cli.sys.stdin", tty_stdin):
            with patch.dict("custodian.cli.os.environ", {"CUSTODIAN_COMPLETE": "off"}):
                self.assertFalse(_configure_completion())

    def test_boot_screen_only_shows_for_interactive_terminals(self) -> None:
        tty = SimpleNamespace(isatty=lambda: True)
        pipe = SimpleNamespace(isatty=lambda: False)

        with patch("custodian.cli.sys.stdin", tty):
            with patch("custodian.cli.sys.stdout", tty):
                self.assertTrue(_should_show_boot_screen())

        with patch("custodian.cli.sys.stdin", pipe):
            with patch("custodian.cli.sys.stdout", tty):
                self.assertFalse(_should_show_boot_screen())

    def test_boot_screen_can_be_disabled(self) -> None:
        tty = SimpleNamespace(isatty=lambda: True)

        with patch("custodian.cli.sys.stdin", tty):
            with patch("custodian.cli.sys.stdout", tty):
                with patch.dict("custodian.cli.os.environ", {"CUSTODIAN_BOOT": "off"}):
                    self.assertFalse(_should_show_boot_screen())


if __name__ == "__main__":
    unittest.main()

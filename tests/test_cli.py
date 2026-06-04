import unittest

from custodian.cli import _lines_with_arka_spacing


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


if __name__ == "__main__":
    unittest.main()

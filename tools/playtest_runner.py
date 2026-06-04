#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from custodian.playtest import SCENARIOS, run_scenario, scenario_from_file, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic Custodian playtest scenarios."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS),
        default="practised-manual",
        help="Scenario to run. Default: practised-manual.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run every scenario.",
    )
    parser.add_argument(
        "--commands-file",
        type=Path,
        help="Run an ad-hoc command file, one command per line.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary report.",
    )
    parser.add_argument(
        "--write",
        type=Path,
        help="Write markdown report files to this directory.",
    )
    args = parser.parse_args(argv)

    if args.list:
        for scenario in SCENARIOS.values():
            print(f"{scenario.name}: {scenario.description}")
        return 0

    if args.all and args.commands_file is not None:
        parser.error("--all cannot be combined with --commands-file")

    if args.commands_file is not None:
        try:
            scenarios = (scenario_from_file(args.commands_file),)
        except OSError as exc:
            parser.error(str(exc))
        except ValueError as exc:
            parser.error(str(exc))
    else:
        scenarios = SCENARIOS.values() if args.all else (SCENARIOS[args.scenario],)
    for index, scenario in enumerate(scenarios):
        if index:
            print()
        report = run_scenario(scenario)
        if args.write is not None:
            path = write_report(report, args.write)
            print(f"wrote {path}")
        print(report.markdown(include_transcript=not args.summary_only), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import unittest
from dataclasses import replace

from custodian.endings import (
    CLEAN_ARRIVAL,
    EFFICIENT_ARRIVAL_WITH_CONTAMINATION,
    ENDING_TITLES,
    ENDLESS_CUSTODIAN,
    FALSE_ARRIVAL,
    QUIET_EXTINCTION,
    ending_lines,
    evaluate_ending,
)
from custodian.models import (
    BehaviourLedger,
    CryostasisSystem,
    MissionStatus,
    NavigationState,
    ShipSector,
    ShipState,
    SpatialState,
    StoryState,
)


def _state(
    *,
    distance: int = 60,
    neural: int = 80,
    sleepers_lost: int = 0,
    exposure: int = 0,
    open_symptom: int = 0,
    verification: str = "unverified",
    delegated_plots: int = 0,
    manual_plots: int = 0,
    raw_nav: int = 0,
    delegated_controls: int = 0,
    turn: int = 6,
    flags: tuple[str, ...] = (),
) -> ShipState:
    sectors = (
        ShipSector("bridge"),
        ShipSector("hydroponics", symptom_load=open_symptom, containment="open"),
    )
    raw_by_panel = {"nav": raw_nav} if raw_nav else {}
    return ShipState(
        turn=turn,
        cryostasis=CryostasisSystem(neural_stability_pct=neural),
        mission=MissionStatus(distance_remaining_tenths_ly=distance),
        navigation=NavigationState(
            delegated_plots=delegated_plots,
            manual_plots=manual_plots,
            total_dark_exposure=exposure,
        ),
        spatial=SpatialState(sectors=sectors),
        delegated_controls=delegated_controls,
        sleepers_lost=sleepers_lost,
        behaviour=BehaviourLedger(raw_by_panel=raw_by_panel),
        story=StoryState(arrival_verification=verification, debrief_flags=flags),
    )


class EvaluateEndingTests(unittest.TestCase):
    def test_clean_arrival_when_viable_and_contained(self) -> None:
        state = _state(distance=0, neural=80, open_symptom=0, verification="manual")
        self.assertEqual(evaluate_ending(state), CLEAN_ARRIVAL)

    def test_efficient_arrival_with_contamination(self) -> None:
        state = _state(
            distance=0,
            neural=75,
            exposure=40,
            open_symptom=30,
            verification="manual",
        )
        self.assertEqual(
            evaluate_ending(state), EFFICIENT_ARRIVAL_WITH_CONTAMINATION
        )

    def test_false_arrival_from_high_arka_nav_reliance(self) -> None:
        # Drift reaches WRONG via heavy delegation; the fix was never verified
        # and the player leaned entirely on arka's routing.
        state = _state(
            distance=0,
            neural=75,
            verification="unverified",
            delegated_plots=4,
            manual_plots=0,
            raw_nav=0,
            delegated_controls=7,
            turn=11,
        )
        self.assertEqual(evaluate_ending(state), FALSE_ARRIVAL)

    def test_false_arrival_from_flag(self) -> None:
        state = _state(distance=0, neural=80, flags=("false_arrival_path",))
        self.assertEqual(evaluate_ending(state), FALSE_ARRIVAL)

    def test_quiet_extinction_when_arrived_but_viability_collapsed(self) -> None:
        state = _state(distance=0, neural=30, verification="manual")
        self.assertEqual(evaluate_ending(state), QUIET_EXTINCTION)

    def test_quiet_extinction_from_sleeper_loss_without_arrival(self) -> None:
        state = _state(distance=50, neural=70, sleepers_lost=150)
        self.assertEqual(evaluate_ending(state), QUIET_EXTINCTION)

    def test_endless_custodian_when_not_arrived_and_maintainable(self) -> None:
        state = _state(distance=50, neural=70, sleepers_lost=0)
        self.assertEqual(evaluate_ending(state), ENDLESS_CUSTODIAN)

    def test_contamination_outranks_clean_when_arrived_messy(self) -> None:
        # Arrived with unresolved symptoms but low exposure: still not clean.
        state = _state(
            distance=0, neural=80, exposure=5, open_symptom=40, verification="manual"
        )
        self.assertEqual(
            evaluate_ending(state), EFFICIENT_ARRIVAL_WITH_CONTAMINATION
        )


class EndingLinesTests(unittest.TestCase):
    def test_every_candidate_has_a_title(self) -> None:
        for candidate in (
            CLEAN_ARRIVAL,
            EFFICIENT_ARRIVAL_WITH_CONTAMINATION,
            FALSE_ARRIVAL,
            ENDLESS_CUSTODIAN,
            QUIET_EXTINCTION,
        ):
            self.assertIn(candidate, ENDING_TITLES)

    def test_lines_render_for_resolved_candidate(self) -> None:
        state = _state(distance=0, neural=80, verification="manual")
        resolved = replace(state, story=replace(state.story, ending_candidate=CLEAN_ARRIVAL))
        lines = ending_lines(resolved)
        self.assertTrue(lines)
        self.assertTrue(any("ARRIVAL PROTOCOL" in line for line in lines))

    def test_lines_never_explain_the_dark(self) -> None:
        for candidate in ENDING_TITLES:
            state = _state(distance=0)
            resolved = replace(
                state, story=replace(state.story, ending_candidate=candidate)
            )
            text = "\n".join(ending_lines(resolved)).lower()
            self.assertNotIn("the dark is", text)


if __name__ == "__main__":
    unittest.main()

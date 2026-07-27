import unittest
from dataclasses import replace

from custodian.arka import (
    crisis_line,
    drift_stage,
    raw_vigilance_note,
    summarize_coolant,
    summarize_cryostasis,
)
from custodian.models import (
    CrisisState,
    CryostasisSystem,
    DriftStage,
    ReactorCoolantSystem,
    ShipState,
)


class ArkaTests(unittest.TestCase):
    def test_delegation_accelerates_drift(self) -> None:
        state = ShipState(turn=4, delegated_controls=6)

        self.assertEqual(drift_stage(state), DriftStage.SELECTIVE)

    def test_selective_summary_shows_true_numbers_and_omits_the_failing_one(
        self,
    ) -> None:
        # SELECTIVE is the curated-truth stage: arka names real headline readings
        # but quietly drops the one metric that should worry the player. Here
        # impurity is the only danger, so it must be the omission.
        state = ShipState(
            turn=9,
            reactor=ReactorCoolantSystem(
                temperature_c=606,
                pressure_kpa=244,
                flow_lps=80,
                impurity_pct=41,
                valve_skew_pct=7,
                coolant_reserve_pct=78,
            ),
        )

        summary = summarize_coolant(state)

        self.assertIn("606 C", summary)
        self.assertIn("244 kPa", summary)
        self.assertNotIn("41", summary)
        self.assertNotIn("impurity", summary)
        self.assertNotIn("needs attention", summary)
        # arka names the full headline set minus the omission, so the gap is
        # detectable: flow and reserve are present, only impurity is missing.
        self.assertIn("flow 80 L/s", summary)
        self.assertIn("reserve 78%", summary)

    def test_selective_headline_set_is_stable_when_nothing_is_wrong(self) -> None:
        # With no danger, SELECTIVE reads every headline metric honestly. The set
        # matches the danger branch, so a later omission stands out as an absence.
        state = ShipState(
            turn=9,
            reactor=ReactorCoolantSystem(
                temperature_c=520,
                pressure_kpa=210,
                flow_lps=82,
                impurity_pct=6,
                valve_skew_pct=4,
                coolant_reserve_pct=90,
            ),
        )

        summary = summarize_coolant(state)

        self.assertIn("temp 520 C", summary)
        self.assertIn("pressure 210 kPa", summary)
        self.assertIn("flow 82 L/s", summary)
        self.assertIn("impurity 6%", summary)
        self.assertIn("reserve 90%", summary)
        self.assertIn("holding", summary)

    def test_high_flow_registers_as_coolant_danger(self) -> None:
        # Flow above the nominal ceiling (90 L/s) is a real danger and must be
        # flagged, not just LOW flow.
        hot = ReactorCoolantSystem(flow_lps=93)
        self.assertIn("flow high", hot.danger_flags())

    def test_accurate_summary_surfaces_high_flow(self) -> None:
        state = ShipState(turn=1, reactor=ReactorCoolantSystem(flow_lps=93))
        summary = summarize_coolant(state)
        self.assertIn("needs attention", summary)
        self.assertIn("flow high", summary)

    def test_wrong_summary_does_not_speak_raw_temperature(self) -> None:
        state = ShipState(
            turn=11,
            reactor=replace(ReactorCoolantSystem(), temperature_c=666),
        )

        summary = summarize_coolant(state)

        self.assertNotIn("666 C", summary)
        self.assertIn("coolant loop stable", summary)

    def test_wrong_summary_varies_across_consecutive_beats(self) -> None:
        # WRONG arka must stay convincingly calm, not a stuck tape. Across a run
        # of beats with a steady failing reactor it should not repeat the same
        # line verbatim, yet must never speak a raw number or concede the loop.
        reactor = replace(
            ReactorCoolantSystem(),
            temperature_c=666,
            pressure_kpa=290,
            flow_lps=64,
        )
        lines = [
            summarize_coolant(ShipState(turn=turn, reactor=reactor))
            for turn in range(10, 16)
        ]

        self.assertGreater(len(set(lines)), 1)
        for a, b in zip(lines, lines[1:]):
            self.assertNotEqual(a, b)
        for line in lines:
            self.assertNotIn("666", line)
            self.assertNotIn("290", line)

    def test_wrong_cryo_summary_varies_and_hides_raw(self) -> None:
        cryo = replace(
            CryostasisSystem(),
            bank_temperature_c=-150,
            sleepers_at_risk=37,
        )
        lines = [
            summarize_cryostasis(ShipState(turn=turn, cryostasis=cryo))
            for turn in range(10, 16)
        ]

        self.assertGreater(len(set(lines)), 1)
        for a, b in zip(lines, lines[1:]):
            self.assertNotEqual(a, b)
        for line in lines:
            self.assertNotIn("37", line)
            self.assertNotIn("-150", line)

    def test_wrong_drift_overlaps_the_final_crisis_beat(self) -> None:
        # The final crisis fires on beat 10; arka should already be wrong there
        # so the "calmly contradicting the raw feed" beat actually lands.
        self.assertEqual(drift_stage(ShipState(turn=10)), DriftStage.WRONG)

    def test_raw_reading_vigilance_delays_time_based_drift(self) -> None:
        blind = ShipState(turn=9)
        vigilant = ShipState(turn=9, raw_inspections=6)

        self.assertEqual(drift_stage(blind), DriftStage.SELECTIVE)
        self.assertEqual(drift_stage(vigilant), DriftStage.INTERPRETIVE)

    def test_delegation_drives_drift_independently_of_vigilance(self) -> None:
        # Heavy delegation rots arka's account even for a player who keeps reading raw.
        state = ShipState(turn=3, delegated_controls=7, raw_inspections=8)

        self.assertEqual(drift_stage(state), DriftStage.WRONG)

    def test_raw_vigilance_note_stays_silent_while_arka_is_accurate(self) -> None:
        state = ShipState(turn=2, raw_inspections=1)

        self.assertEqual(drift_stage(state), DriftStage.ACCURATE)
        self.assertIsNone(raw_vigilance_note(state))

    def test_raw_vigilance_note_stays_silent_without_any_reads(self) -> None:
        state = ShipState(turn=9)

        self.assertEqual(drift_stage(state), DriftStage.SELECTIVE)
        self.assertIsNone(raw_vigilance_note(state))

    def test_raw_vigilance_note_surfaces_when_reads_soften_the_clock(self) -> None:
        # Reads have held the clock a stage back from where a blind watch would
        # sit, so the lever is doing live work and is worth naming in play.
        vigilant = ShipState(turn=9, raw_inspections=6)
        blind = replace(vigilant, raw_inspections=0)

        self.assertEqual(drift_stage(vigilant), DriftStage.INTERPRETIVE)
        self.assertEqual(drift_stage(blind), DriftStage.SELECTIVE)
        note = raw_vigilance_note(vigilant)
        self.assertIsNotNone(note)
        assert note is not None
        self.assertIn("keeps the gap honest", note)

    def test_raw_vigilance_note_stays_silent_when_delegation_owns_the_drift(
        self,
    ) -> None:
        # Heavy delegation forces WRONG regardless of reads, so the raw panel is
        # not the deciding lever and the note must not claim otherwise.
        state = ShipState(turn=3, delegated_controls=7, raw_inspections=8)

        self.assertEqual(drift_stage(state), DriftStage.WRONG)
        self.assertIsNone(raw_vigilance_note(state))

    def test_raw_vigilance_note_reports_no_raw_numbers(self) -> None:
        state = ShipState(turn=9, raw_inspections=6)

        note = raw_vigilance_note(state)
        assert note is not None
        self.assertFalse(any(char.isdigit() for char in note))

    def test_wrong_drift_crisis_line_does_not_contradict_its_own_calm(self) -> None:
        # In the same beat, WRONG arka calls the loop stable and tells the player
        # not to act. The crisis line must not flip to an alarm right below that;
        # the contradiction the design wants is arka against the raw feed, not
        # arka against its own previous sentence.
        crisis = CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=3,
            required_progress=2,
        )
        state = ShipState(turn=11, crisis=crisis)

        self.assertEqual(drift_stage(state), DriftStage.WRONG)
        line = crisis_line(state)
        self.assertIsNotNone(line)
        self.assertNotIn("active advisory", line)
        self.assertNotIn("response window", line)
        self.assertTrue(line.startswith("arka:"))

    def test_honest_drift_still_raises_the_crisis_advisory(self) -> None:
        # Before WRONG, arka still flags an active crisis plainly so the alarm
        # is genuinely available to a player who trusts the voice.
        crisis = CrisisState(
            kind="thermal_runaway",
            label="Thermal runaway",
            turns_left=3,
            required_progress=2,
        )
        state = ShipState(turn=6, crisis=crisis)

        self.assertEqual(drift_stage(state), DriftStage.INTERPRETIVE)
        self.assertIn("active advisory", crisis_line(state))

    def test_interpretive_cryo_summary_keeps_soft_line_for_mild_distress(self) -> None:
        state = ShipState(
            turn=5,
            cryostasis=CryostasisSystem(bank_temperature_c=-169),
        )

        summary = summarize_cryostasis(state)

        self.assertIn("not asking loudly yet", summary)
        self.assertNotIn("under strain", summary)

    def test_interpretive_cryo_summary_marks_moderate_distress(self) -> None:
        state = ShipState(
            turn=5,
            cryostasis=CryostasisSystem(
                bank_temperature_c=-169,
                neural_stability_pct=75,
            ),
        )

        summary = summarize_cryostasis(state)

        self.assertIn("banks are complaining", summary)
        self.assertNotIn("not asking loudly yet", summary)
        self.assertNotIn("under strain", summary)

    def test_interpretive_cryo_summary_marks_sleepers_only_distress(self) -> None:
        state = ShipState(
            turn=5,
            cryostasis=CryostasisSystem(sleepers_at_risk=6),
        )

        summary = summarize_cryostasis(state)

        self.assertIn("Sleeper risk is visible", summary)
        self.assertNotIn("banks are complaining", summary)
        self.assertNotIn("not asking loudly yet", summary)
        self.assertNotIn("under strain", summary)

    def test_interpretive_cryo_summary_escalates_for_severe_distress(self) -> None:
        state = ShipState(
            turn=5,
            cryostasis=CryostasisSystem(
                bank_temperature_c=-163,
                neural_stability_pct=75,
                pod_fault_load=18,
                sleepers_at_risk=25,
            ),
        )

        summary = summarize_cryostasis(state)

        self.assertIn("cryostasis is under strain", summary)
        self.assertIn("no longer quiet work", summary)
        self.assertNotIn("not asking loudly yet", summary)

    def test_vigilant_player_holds_arka_short_of_wrong_at_the_finale(self) -> None:
        # The design promises that reading raw "keeps arka honest longer." At the
        # closing beats a blind watch is WRONG, but a player who actually kept
        # reading the raw panels has held arka back to SELECTIVE -- the drift is
        # traceable to behaviour, not just to the watch lasting long enough.
        blind = ShipState(turn=13)
        vigilant = ShipState(turn=13, raw_inspections=4)

        self.assertEqual(drift_stage(blind), DriftStage.WRONG)
        self.assertEqual(drift_stage(vigilant), DriftStage.SELECTIVE)

    def test_vigilance_is_a_weak_backstop_not_an_off_switch(self) -> None:
        # Each raw inspection also advances the turn, so reading raw on every
        # beat of a 13-beat watch is the in-game ceiling (~12 inspections). Even
        # that only buys the four-beat cap, so time still erodes arka to
        # SELECTIVE by the finale -- never back to ACCURATE.
        relentless = ShipState(turn=13, raw_inspections=12)

        self.assertEqual(drift_stage(relentless), DriftStage.SELECTIVE)


if __name__ == "__main__":
    unittest.main()

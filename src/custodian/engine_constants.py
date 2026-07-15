MISSION_END_TURN = 12

# Outcome strings for reactor-failure end states. Named here so the engine that
# sets them and the debrief that reads them share one vocabulary, rather than
# matching loose substrings.
REACTOR_MELTDOWN_OUTCOME = (
    "The coolant loop flashes dry. The reactor becomes a small, patient sun."
)
REACTOR_OVERHEAT_OUTCOME = "Reactor temperature exceeds containment."
REACTOR_OVERPRESSURE_OUTCOME = "Coolant pressure ruptures the primary loop."
REACTOR_COOLANT_DRY_OUTCOME = "The coolant reserve runs dry."

# The full set of outcomes where the reactor itself was lost. Any other resolved
# outcome means containment held for the window.
REACTOR_FAILURE_OUTCOMES = frozenset(
    {
        REACTOR_MELTDOWN_OUTCOME,
        REACTOR_OVERHEAT_OUTCOME,
        REACTOR_OVERPRESSURE_OUTCOME,
        REACTOR_COOLANT_DRY_OUTCOME,
    }
)

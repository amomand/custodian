# Codex Notes

Custodian is early. Follow the nose a little.

This file is a map and a few current invariants, not a constitution. Prefer the
shape of the idea and the current playtest feel over rigid process.

## Where To Look

- `~/obsidian/Projects/Custodian/idea.md` - original vision and thesis.
- `~/obsidian/Projects/Custodian/roadmap.md` - working long-range plan.
- `README.md` - maintainer/player overview.
- `design.md` - current terminal MVP.
- `docs/roadmap.md` - repo copy of the long-range plan.
- `docs/production/codex-direction-phase4.md` - operating-surface production direction.
- `docs/architecture/engine-contracts.md` - canonical truth owners and boundaries.
- `docs/architecture/web-session-api.md` - browser session API and snapshot contract.
- `docs/ui/operating-desk.md` - the graphical operating desk web client.
- `docs/lore/arka.md` - arka character and runtime voice capsule.
- `docs/architecture/ai-interpreter.md` - current AI/simulation boundary.
- `docs/architecture/project-operating-system.md` - notes on borrowed process.

If the Obsidian and repo copies disagree, treat Obsidian as the sketchpad and
ask or update both when the change is intentional.

## Useful Commands

```bash
python3 main.py
CUSTODIAN_AI=off python3 main.py
CUSTODIAN_DEBUG=1 python3 main.py
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests main.py
```

Tests must pass without an API key.

## Current Core Truths

These are the bits to be careful with even while exploring:

- Delegation should be genuinely attractive.
- Manual control should be real, effortful, and learnable.
- Raw telemetry comes from deterministic state, not generated prose.
- The model may interpret and speak as arka; it should not own ship truth.
- Manual familiarity improves through manual action, not delegation.
- arka should remain competent reassurance, not turn into a cartoon villain.
- Player-facing text should stay in-world.

Everything else is allowed to move.

## Working Style

- Start substantial implementation work on a branch and aim to publish it as a
  PR, even while the project is young.
- Use plain branch names, for example `phase-2b-route-options`; do not add a
  `codex/` prefix.
- Keep changes narrow enough that playtest feedback remains readable.
- Update docs when a change creates a new rule, mechanic, or strong direction.
- For docs that also live in Obsidian, sync the vault copy too.
- Borrow from The Cabin proudly, but adapt to Custodian's needs.
- Use local review skills as lenses when useful, not as blockers.

## Optional Review Lenses

The repo has two local skills:

- `.codex/skills/custodian-diegesis-review/SKILL.md`
- `.codex/skills/custodian-simulation-truth-review/SKILL.md`

They are useful before larger PRs or when a change touches arka, player-facing
text, telemetry, or model boundaries. Early in the project, their job is to
surface questions, not shut down experiments.

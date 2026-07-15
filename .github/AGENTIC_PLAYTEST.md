# Agentic playtest repair loop

The weekly playtester still stops at issues. A second workflow picks up only the
issues carrying that run's hidden gh-aw provenance marker, checks them against
the current game, and opens one draft PR per coherent root cause. It may open
three PRs in a run, but it may not alter the control plane or merge its work.

```mermaid
flowchart LR
  P["Weekly playtest"] --> I["Provenanced issues"]
  I --> F["Opus implementer"]
  F --> PR["Draft fix PR"]
  PR --> D["Opus diegesis review"]
  PR --> S["Opus simulation-truth review"]
  PR --> C["Copilot review"]
  D --> B["Exact-head barrier"]
  S --> B
  C --> B
  PR --> T["Exact-head CI"]
  T --> B
  B --> A["Opus adjudicator"]
  A -->|"substantive fix, cycles 1-2"| PR
  A -->|"cycle 3 fix"| V["Cap-pending final verification"]
  V --> T
  V --> D
  V --> S
  A -->|"validated clean"| X["Deterministic clean marker"]
  A -->|"human choice"| H["Human hand-off"]
```

## What counts as all reviews being in

The join is ordinary Actions code, not an agent judgement. Diegesis and
simulation-truth reviews must each include their receipt and the full current
head SHA. Copilot's review must also belong to that SHA, and CI must have
completed on it. A failed CI run still dispatches the adjudicator so it can be
diagnosed and fixed; it can never produce a clean marker. Old reviews do not
carry over after a push, and a forged specialist receipt is ignored unless it
was submitted by the repository workflow actor.

Copilot cycles are counted by unique reviewed head SHAs. Duplicate reviews on
one commit still count as one cycle. After a third Copilot-reviewed head, the
adjudicator may make one final fix but must not ask for a fourth Copilot review.
That pushed head enters a non-terminal `cap-pending` state: CI and both Opus
reviewers run again, then one final adjudication either records a validated
clean result or hands a remaining change to a human.

Terminal state is a safe-output operation backed by deterministic checks. It
verifies the current SHA, green CI, required review receipts and zero unresolved
threads before writing the exact clean marker. The model supplies the decision
ledger, but does not format or authorise its own terminal state.

The watchdog checks every ten minutes. After twenty minutes it names missing
reviewers or pending CI on the PR; silence never becomes a pass. It recovers a
completed join if the immediate barrier missed its dispatch and retries stale
dispatch locks when an adjudicator run or its safe outputs failed.

## Agent authority

All automated PRs must target `main`, carry the `playtest` label, use the
`[agentic playtest] ` title prefix, and come from this repository. Code-writing
outputs are restricted to game source, tests, tools and project docs. Agent
instructions, workflows, dependency files and other protected files are
blocked. Reviewers can only leave non-blocking `COMMENT` reviews. Nothing in the
loop can approve or merge a PR.

The adjudicator replies to each handled thread as `Addressed`, `Overridden`,
`Already covered` or `Outdated`, then resolves it. `Needs human` stops the loop
when the feedback exposes a real product choice. Copilot advice can be
overridden when it is wrong, disproportionate, out of scope, bad for arka's
voice, or crosses the deterministic simulation boundary.

## Token setup

The existing `COPILOT_GITHUB_TOKEN` fine-grained PAT is reused for all gh-aw
safe outputs. Give it access only to this repository, with:

- account permission `Copilot Requests: Read`;
- repository permission `Contents: Read and write`;
- repository permission `Pull requests: Read and write`.

The account permission permits Copilot review requests. Using the PAT for PR
creation and subsequent pushes gives those events one consistent user actor,
so ordinary CI and reviewer workflows wake without approval-only recursion or
extra empty commits. Pull requests write lets the adjudicator reply to and
resolve review threads reliably. The deterministic barrier and watchdog retain
GitHub's short-lived workflow token for their own comments and dispatches.

The Opus reviewer triggers also explicitly allow `github-actions[bot]` as a
fallback. The normal path remains the PAT-authored PR and pushes; the bot
allowlist prevents a missing PAT from silently stranding a bot-authored PR.

## Editing the loop

Edit the `.md` agentic workflows, not their generated `.lock.yml` files. Compile
with the current gh-aw release:

```bash
gh aw compile --approve --validate
node --test tests/test_agentic_review_state.cjs
```

The specialist skills live under `.agents/skills/`. `.agents` is the portable
project convention; Copilot also recognises it, behind its GitHub-specific
`.github/skills` location in lookup priority.

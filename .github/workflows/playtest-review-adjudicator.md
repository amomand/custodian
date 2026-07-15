---
name: Adjudicate playtest fix reviews
description: Act once all three exact-head reviews are present, reply thread by thread, and request another bounded Copilot round only after a substantive fix.

on:
  workflow_dispatch:
    inputs:
      pull_request_number:
        description: Pull request to adjudicate
        required: true
        type: string
      head_sha:
        description: Exact head reviewed by all three reviewers
        required: true
        type: string
      cycle:
        description: Number of unique Copilot-reviewed heads so far
        required: true
        type: string

permissions:
  contents: read
  issues: read
  pull-requests: read

engine:
  id: copilot
  model: claude-opus-4.8

imports:
  - .github/agents/custodian-review-adjudicator.md

checkout:
  ref: refs/pull/${{ github.event.inputs.pull_request_number }}/head
  fetch: ["*"]
  fetch-depth: 0

network:
  allowed: [defaults, github]

tools:
  github:
    toolsets: [pull_requests, repos]
  bash:
    - "rg"
    - "sed -n"
    - "git diff"
    - "git status"
    - "PYTHONPATH=src python -m unittest"
    - "python -m compileall"
    - "python tools/playtest_runner.py"
    - "node --check"
    - "node --test"

safe-outputs:
  push-to-pull-request-branch:
    target: ${{ github.event.inputs.pull_request_number }}
    max: 1
    if-no-changes: ignore
    fallback-as-pull-request: false
    check-branch-protection: false
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
    github-token-for-extra-empty-commit: ${{ secrets.COPILOT_GITHUB_TOKEN }}
    allowed-files:
      - "src/**"
      - "tests/**"
      - "tools/**"
      - "docs/**"
      - "main.py"
      - "design.md"
    protected-files: blocked
  reply-to-pull-request-review-comment:
    target: ${{ github.event.inputs.pull_request_number }}
    max: 30
    footer: false
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
  resolve-pull-request-review-thread:
    target: ${{ github.event.inputs.pull_request_number }}
    max: 30
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
    github-token: ${{ secrets.COPILOT_GITHUB_TOKEN }}
  add-reviewer:
    target: ${{ github.event.inputs.pull_request_number }}
    max: 1
    allowed-reviewers: [copilot]
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
  add-comment:
    target: ${{ github.event.inputs.pull_request_number }}
    max: 1
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
---

# Adjudicate a complete review round

The barrier dispatched:

- pull request: `#${{ github.event.inputs.pull_request_number }}`
- reviewed head: `${{ github.event.inputs.head_sha }}`
- Copilot cycle: `${{ github.event.inputs.cycle }}` of 3

Before doing anything, read the pull request and confirm it is open, same-repo,
labelled `playtest`, titled with `[agentic playtest] `, and still at the exact
reviewed head above. If any check fails, make no outputs.

Read every review and every review-comment thread, including resolved state and
outdated comments. The barrier has already established that Copilot, diegesis,
and simulation-truth reviews exist for this head. Adjudicate all feedback using
the imported agent's classifications. A Copilot suggestion may be overridden
when it is factually wrong, worsens arka's voice, crosses the simulation-truth
boundary, duplicates a stronger fix, or is disproportionate to the finding.

For each inline comment you handle:

1. reply with `Addressed:`, `Overridden:`, `Already covered:`, or `Outdated:` and
   a concise reason;
2. resolve the thread after the code and reply agree;
3. use `Needs human:` only for a real product-direction choice, not ordinary
   uncertainty.

If you make substantive code changes, run all of:

```text
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests tools main.py
node --check src/custodian/web_static/app.js
node --test tests/test_agentic_review_state.cjs
python tools/playtest_runner.py --all --summary-only
```

Then follow exactly one terminal path:

- **No code changes and no human choice:** reply/resolve as needed, do not push
  and do not request another review. Add one PR comment containing
  `<!-- agentic-review-clean:${{ github.event.inputs.head_sha }} -->`
  and a short decision ledger.
- **Code changes, cycle 1 or 2:** push once to this PR, reply/resolve all handled
  threads, and request `copilot` once. Do not add a terminal marker. The
  PAT-authored empty commit will wake both local reviewers for the new head.
- **Code changes, cycle 3:** push once but do not request Copilot again. Add one
  PR comment containing `<!-- agentic-review-cap-reached -->`, the decision
  ledger, validation, and the explicit warning that the final head has not had
  another Copilot review.
- **Needs human:** do not request another Copilot review. Add one PR comment
  containing `<!-- agentic-review-needs-human -->`, name the decision, and give
  the smallest useful options. Only push mechanical fixes if they do not choose
  a side in that decision.

Every safe-output call must include pull request number
`${{ github.event.inputs.pull_request_number }}`. Never merge.

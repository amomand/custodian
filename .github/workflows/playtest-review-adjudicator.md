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
      ci_conclusion:
        description: CI conclusion for the reviewed head
        required: true
        type: string
      ci_run_id:
        description: CI workflow run for the reviewed head
        required: true
        type: string
      final_verification:
        description: Whether this head follows the third Copilot-reviewed head
        required: true
        type: string

permissions:
  actions: read
  contents: read
  issues: read
  pull-requests: read

# The default gh-aw group falls back to github.ref on workflow_dispatch, so
# concurrent dispatches for different PRs cancel each other. Key on the PR.
concurrency:
  group: "gh-aw-${{ github.workflow }}-${{ github.event.inputs.pull_request_number }}"
  cancel-in-progress: true

engine:
  id: copilot
  model: claude-opus-4.8

imports:
  - .github/agents/custodian-review-adjudicator.md

checkout:
  ref: refs/pull/${{ github.event.inputs.pull_request_number }}/head
  fetch: ["*"]
  fetch-depth: 0

env:
  PYTHONPATH: src

pre-agent-steps:
  - name: Require the CI trigger token
    env:
      CI_TRIGGER_TOKEN: ${{ secrets.GH_AW_CI_TRIGGER_TOKEN }}
    run: |
      if [ -z "$CI_TRIGGER_TOKEN" ]; then
        echo "::error::GH_AW_CI_TRIGGER_TOKEN is not configured. Without it, adjudicator pushes never wake CI or the reviewers and the loop stalls silently. Failing loudly instead."
        exit 1
      fi
  - name: Prepare a writable adjudication branch
    env:
      PR_NUMBER: ${{ github.event.inputs.pull_request_number }}
    run: |
      [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]
      git switch -c "agentic-review-${PR_NUMBER}-${GITHUB_RUN_ID}"
      git config user.name "github-actions[bot]"
      git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

network:
  allowed: [defaults, github]

tools:
  edit:
  agentic-workflows:
  github:
    toolsets: [pull_requests, repos]
  bash:
    - "env"
    - "git"
    - "python"
    - "python3"
    - "node"
    - "python -m unittest"
    - "python3 -m unittest"
    - "python -m compileall"
    - "python3 -m compileall"
    - "python tools/playtest_runner.py"
    - "python3 tools/playtest_runner.py"
    - "node --check"
    - "node --test"
    - "rg"
    - "sed -n"

safe-outputs:
  push-to-pull-request-branch:
    target: ${{ github.event.inputs.pull_request_number }}
    max: 1
    if-no-changes: ignore
    fallback-as-pull-request: false
    check-branch-protection: false
    github-token-for-extra-empty-commit: ${{ secrets.GH_AW_CI_TRIGGER_TOKEN }}
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
    allowed-files:
      - "src/**"
      - "tests/**"
      # Deliberately not tools/**: the review-loop state machine
      # (agentic_review_state.cjs, finalize_agentic_review.cjs) lives there
      # and the loop must not be able to rewrite its own control plane.
      - "tools/playtest_runner.py"
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
  add-reviewer:
    target: ${{ github.event.inputs.pull_request_number }}
    max: 1
    allowed-reviewers: [copilot]
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
  jobs:
    complete-review-round:
      description: Validate and record the terminal or cap-pending review state
      runs-on: ubuntu-latest
      needs: safe_outputs
      permissions:
        actions: read
        contents: read
        issues: write
        pull-requests: write
      env:
        EXPECTED_PR: ${{ github.event.inputs.pull_request_number }}
        EXPECTED_HEAD: ${{ github.event.inputs.head_sha }}
        EXPECTED_CYCLE: ${{ github.event.inputs.cycle }}
        PUSH_COMMIT_SHA: ${{ needs.safe_outputs.outputs.push_commit_sha }}
      inputs:
        pull_request_number:
          description: Pull request number from this workflow dispatch
          required: true
          type: string
        reviewed_head:
          description: Exact head adjudicated in this workflow run
          required: true
          type: string
        outcome:
          description: Validated state to record
          required: true
          type: choice
          options: [clean, cap-pending, needs-human]
        summary:
          description: Concise decision ledger and any human decision required
          required: true
          type: string
      steps:
        - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
          with:
            persist-credentials: false
        - name: Validate and record review state
          uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3
          with:
            github-token: ${{ github.token }}
            script: |
              const finalize = require("./tools/finalize_agentic_review.cjs");
              await finalize({ github, context, core });
---

# Adjudicate a complete review round

The barrier dispatched:

- pull request: `#${{ github.event.inputs.pull_request_number }}`
- reviewed head: `${{ github.event.inputs.head_sha }}`
- Copilot cycle: `${{ github.event.inputs.cycle }}` of 3
- CI: `${{ github.event.inputs.ci_conclusion }}` in run `${{ github.event.inputs.ci_run_id }}`
- final cap verification: `${{ github.event.inputs.final_verification }}`

Before doing anything, read the pull request and confirm it is open, same-repo,
labelled `playtest`, titled with `[agentic playtest] `, and still at the exact
reviewed head above. If any check fails, make no outputs.

Read the supplied CI run and treat any failure as blocking review feedback to
diagnose and fix. Read every review and every review-comment thread, including
resolved state and outdated comments. The barrier has established exact-head
diegesis and simulation-truth reviews. It has also established an exact-head
Copilot review unless `final cap verification` is `true`; in that case the
three-review cap was reached on the parent and this is its single post-Copilot
correction head. Adjudicate all feedback using the imported agent's
classifications. A Copilot suggestion may be overridden
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

Use the edit tool for file changes. Before requesting a push, inspect the diff,
stage only allowed files, and commit the change on the prepared writable branch.
Never declare a failed or pending CI head clean.

Then follow exactly one terminal path:

- **No code changes, CI successful, and no human choice:** reply/resolve as
  needed, do not push and do not request another review. Call
  `complete-review-round` exactly once with outcome `clean` and a short decision
  ledger. Deterministic code will verify CI, review receipts, threads and head
  SHA before writing the terminal marker.
- **Code changes, cycle 1 or 2:** push once to this PR, reply/resolve all handled
  threads, and request `copilot` once. Do not call `complete-review-round`. The
  dedicated CI-trigger token adds an empty commit after the code push, waking
  CI and both local reviewers on that exact event head.
- **Code changes, cycle 3, not final cap verification:** push once, do not
  request Copilot again, and call `complete-review-round` exactly once with
  outcome `cap-pending`. CI and both Opus reviewers then verify the pushed head
  before one last adjudication.
- **Final cap verification needs another code change:** do not create an
  unreviewed fourth head. Call `complete-review-round` with outcome
  `needs-human` and name the remaining change.
- **Needs human or an unfixable CI failure:** do not request another Copilot
  review. Call `complete-review-round` with outcome `needs-human`, name the
  decision or blocker, and give the smallest useful options. Only push
  mechanical fixes if they do not choose a side in that decision.

Every safe-output call must include pull request number
`${{ github.event.inputs.pull_request_number }}`. Never merge.

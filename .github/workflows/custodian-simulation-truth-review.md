---
name: Custodian simulation-truth review
description: Give automated playtest fixes an independent, non-blocking simulation and model-boundary review.

on:
  pull_request:
    types: [opened, synchronize, reopened]
  bots: [github-actions]

if: ${{ github.event.pull_request.head.repo.full_name == github.repository && contains(github.event.pull_request.labels.*.name, 'playtest') && startsWith(github.event.pull_request.title, '[agentic playtest] ') }}

permissions:
  contents: read
  pull-requests: read

engine:
  id: copilot
  model: claude-opus-4.8
  concurrency:
    group: "gh-aw-copilot-simulation-truth-${{ github.event.pull_request.number }}"

imports:
  - .github/agents/custodian-simulation-truth-reviewer.md

network:
  allowed: [defaults, github]

tools:
  github:
    toolsets: [pull_requests, repos]
  bash:
    - "git diff"
    - "git status"
    - "sed -n"
    - "rg"

safe-outputs:
  create-pull-request-review-comment:
    max: 10
    target: triggering
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
  submit-pull-request-review:
    max: 1
    target: triggering
    allowed-events: [COMMENT]
    footer: none
    required-labels: [playtest]
    required-title-prefix: "[agentic playtest] "
---

# Review the exact pull request head

Review pull request #${{ github.event.pull_request.number }} at full head SHA
`${{ github.event.pull_request.head.sha }}`. Follow the imported agent and the
portable simulation-truth skill. Submit one `COMMENT` review even when the
result is `PASS`; the exact receipt is how the deterministic barrier knows this
reviewer finished. Do not modify files, approve, request changes, merge, or
request other reviewers.

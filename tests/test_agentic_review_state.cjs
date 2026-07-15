"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const state = require("../tools/agentic_review_state.cjs");

const HEAD = "a".repeat(40);

function localReview(kind, head = HEAD) {
  return {
    commit_id: head,
    state: "COMMENTED",
    user: { login: "github-actions[bot]" },
    body: `Custodian-Review: ${kind}\nHead: ${head}\nVerdict: PASS`,
  };
}

function copilotReview(head = HEAD) {
  return {
    commit_id: head,
    state: "COMMENTED",
    user: { login: "copilot-pull-request-reviewer[bot]" },
    body: "No findings.",
  };
}

test("joins only when all three reviewers covered the exact head", () => {
  const reviews = [
    localReview("diegesis"),
    localReview("simulation-truth"),
    copilotReview(),
  ];
  assert.deepEqual(state.missingReviewers(reviews, HEAD), []);
});

test("ignores stale receipts even when every reviewer commented before", () => {
  const stale = "b".repeat(40);
  const reviews = [
    localReview("diegesis", stale),
    localReview("simulation-truth", stale),
    copilotReview(stale),
  ];
  assert.deepEqual(state.missingReviewers(reviews, HEAD), [
    "diegesis",
    "simulation-truth",
    "copilot",
  ]);
});

test("does not accept a forged or dismissed reviewer receipt", () => {
  const forged = {
    ...localReview("diegesis"),
    user: { login: "passing-stranger" },
  };
  const dismissed = {
    ...localReview("simulation-truth"),
    state: "DISMISSED",
  };
  assert.deepEqual(state.missingReviewers([forged, dismissed, copilotReview()], HEAD), [
    "diegesis",
    "simulation-truth",
  ]);
});

test("counts Copilot review cycles by unique reviewed head", () => {
  const second = "c".repeat(40);
  assert.deepEqual(
    state.copilotReviewedHeads([
      copilotReview(HEAD),
      copilotReview(HEAD),
      copilotReview(second),
    ]),
    [HEAD, second],
  );
});

test("recognises scoped PRs and terminal markers", () => {
  const pullRequest = {
    state: "open",
    title: "[agentic playtest] steady the containment report",
    labels: [{ name: "playtest" }],
    base: { ref: "main" },
    head: { repo: { full_name: "alexomand/custodian" } },
  };
  assert.equal(
    state.isAgenticPlaytestPullRequest(pullRequest, "alexomand/custodian"),
    true,
  );
  assert.equal(
    state.isTerminal([{ body: "<!-- agentic-review-cap-reached -->" }]),
    true,
  );
});

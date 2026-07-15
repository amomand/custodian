"use strict";

const REVIEWERS = Object.freeze(["diegesis", "simulation-truth", "copilot"]);
const TITLE_PREFIX = "[agentic playtest] ";
const LABEL = "playtest";

function bodyOf(item) {
  return typeof item?.body === "string" ? item.body : "";
}

function commitOf(review) {
  return review?.commit_id || review?.commitId || "";
}

function loginOf(review) {
  return String(
    review?.user?.login || review?.author?.login || review?.author?.name || "",
  ).toLowerCase();
}

function isSubmitted(review) {
  const reviewState = String(review?.state || "").toUpperCase();
  return reviewState !== "DISMISSED" && reviewState !== "PENDING";
}

function hasReceipt(body, kind, head) {
  if (!head || !body.includes(`Custodian-Review: ${kind}`)) return false;
  if (!body.includes(`Head: ${head}`)) return false;
  return /Verdict:\s*(PASS|QUESTIONS|CONCERNS)\b/.test(body);
}

function reviewReceipts(reviews, head) {
  const receipts = {
    diegesis: false,
    "simulation-truth": false,
    copilot: false,
  };

  for (const review of reviews || []) {
    if (commitOf(review) !== head || !isSubmitted(review)) continue;
    const body = bodyOf(review);
    const login = loginOf(review);
    const localWorkflowReview = login === "github-actions[bot]";
    if (localWorkflowReview && hasReceipt(body, "diegesis", head)) {
      receipts.diegesis = true;
    }
    if (localWorkflowReview && hasReceipt(body, "simulation-truth", head)) {
      receipts["simulation-truth"] = true;
    }
    if (login.startsWith("copilot-pull-request-reviewer")) {
      receipts.copilot = true;
    }
  }

  return receipts;
}

function missingReviewers(reviews, head) {
  const receipts = reviewReceipts(reviews, head);
  return REVIEWERS.filter((reviewer) => !receipts[reviewer]);
}

function copilotReviewedHeads(reviews) {
  const heads = new Set();
  for (const review of reviews || []) {
    if (
      !isSubmitted(review) ||
      !loginOf(review).startsWith("copilot-pull-request-reviewer")
    ) {
      continue;
    }
    const commit = commitOf(review);
    if (commit) heads.add(commit);
  }
  return [...heads];
}

function hasCommentMarker(comments, marker) {
  return (comments || []).some((comment) => bodyOf(comment).includes(marker));
}

function barrierMarker(head) {
  return `<!-- agentic-review-barrier:${head} -->`;
}

function waitingMarker(head) {
  return `<!-- agentic-review-waiting:${head} -->`;
}

function isTerminal(comments) {
  return (
    hasCommentMarker(comments, "<!-- agentic-review-cap-reached -->") ||
    hasCommentMarker(comments, "<!-- agentic-review-needs-human -->") ||
    hasCommentMarker(comments, "<!-- agentic-review-clean:")
  );
}

function isAgenticPlaytestPullRequest(pullRequest, repository) {
  const labels = (pullRequest?.labels || []).map((label) =>
    typeof label === "string" ? label : label?.name,
  );
  return Boolean(
    pullRequest &&
      pullRequest.state === "open" &&
      pullRequest.title?.startsWith(TITLE_PREFIX) &&
      labels.includes(LABEL) &&
      pullRequest.base?.ref === "main" &&
      pullRequest.head?.repo?.full_name === repository,
  );
}

module.exports = {
  LABEL,
  REVIEWERS,
  TITLE_PREFIX,
  barrierMarker,
  copilotReviewedHeads,
  hasCommentMarker,
  isAgenticPlaytestPullRequest,
  isTerminal,
  missingReviewers,
  reviewReceipts,
  waitingMarker,
};

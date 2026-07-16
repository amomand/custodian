"use strict";

const REVIEWERS = Object.freeze(["diegesis", "simulation-truth", "copilot"]);
const TITLE_PREFIX = "[agentic playtest] ";
const LABEL = "playtest";
const CI_WORKFLOW = "CI";
const NEEDS_HUMAN_MARKER = "<!-- agentic-review-needs-human -->";
const WAITING_ESCALATION_MS = 6 * 60 * 60 * 1000;

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

function capPendingMarker(head, reviewedHead) {
  return `<!-- agentic-review-cap-pending:${head}:from:${reviewedHead} -->`;
}

function hasCapPendingForHead(comments, head) {
  const prefix = `<!-- agentic-review-cap-pending:${head}:from:`;
  return (comments || []).some((comment) => bodyOf(comment).includes(prefix));
}

function missingRequiredReviewers(reviews, comments, head) {
  const missing = missingReviewers(reviews, head);
  const capReached = copilotReviewedHeads(reviews).length >= 3;
  if (capReached && hasCapPendingForHead(comments, head)) {
    return missing.filter((reviewer) => reviewer !== "copilot");
  }
  return missing;
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

function copilotRequestMarker(head) {
  return `<!-- agentic-copilot-requested:${head} -->`;
}

function copilotRequestFailedMarker(head) {
  return `<!-- agentic-copilot-request-failed:${head} -->`;
}

function hasPendingCopilotRequest(pullRequest) {
  return (pullRequest?.requested_reviewers || []).some((reviewer) =>
    String(reviewer?.login || "")
      .toLowerCase()
      .startsWith("copilot"),
  );
}

// Copilot silently drops review requests made by actors without a Copilot
// seat, so the watchdog re-requests once per head with the CI trigger token.
function needsCopilotRequest(pullRequest, reviews, comments, head) {
  if (!missingRequiredReviewers(reviews, comments, head).includes("copilot")) {
    return false;
  }
  if (hasPendingCopilotRequest(pullRequest)) return false;
  if (hasCommentMarker(comments, copilotRequestMarker(head))) return false;
  if (hasCommentMarker(comments, copilotRequestFailedMarker(head))) return false;
  return true;
}

function waitingMarker(head) {
  return `<!-- agentic-review-waiting:${head} -->`;
}

function latestWorkflowRun(runs, workflowName = CI_WORKFLOW) {
  return [...(runs || [])]
    .filter((run) => run?.name === workflowName && run?.head_sha)
    .sort((left, right) => Number(right.id || 0) - Number(left.id || 0))[0];
}

function workflowRunState(runs, workflowName = CI_WORKFLOW) {
  const run = latestWorkflowRun(runs, workflowName);
  if (!run) return { status: "missing", conclusion: null, run: null };
  if (run.status !== "completed") {
    return { status: "pending", conclusion: null, run };
  }
  return { status: "completed", conclusion: run.conclusion || null, run };
}

function isTerminal(comments) {
  return (
    hasCommentMarker(comments, "<!-- agentic-review-cap-reached -->") ||
    hasCommentMarker(comments, NEEDS_HUMAN_MARKER) ||
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
  CI_WORKFLOW,
  LABEL,
  NEEDS_HUMAN_MARKER,
  REVIEWERS,
  TITLE_PREFIX,
  WAITING_ESCALATION_MS,
  barrierMarker,
  capPendingMarker,
  copilotRequestFailedMarker,
  copilotRequestMarker,
  copilotReviewedHeads,
  hasCommentMarker,
  hasCapPendingForHead,
  hasPendingCopilotRequest,
  isAgenticPlaytestPullRequest,
  isTerminal,
  latestWorkflowRun,
  missingRequiredReviewers,
  missingReviewers,
  needsCopilotRequest,
  reviewReceipts,
  waitingMarker,
  workflowRunState,
};

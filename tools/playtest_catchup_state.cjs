"use strict";

// Deterministic state for the playtest implementer catch-up sweep.
//
// The implementer is normally woken by a workflow_run trigger on the weekly
// playtest review. When that trigger is missed, because the implementer run
// itself died or the review ran on a branch the trigger does not accept, the
// issues it filed sit unpicked with nothing watching them. This module holds
// the pure decisions the sweep makes; the workflow does the API calls.
//
// The sweep only ever re-dispatches the implementer by provenance run ID. It
// never widens which issues the implementer may act on: every issue it names is
// re-verified against the same provenance marker inside the implementer run.

const review = require("./agentic_review_state.cjs");

const LABEL = review.LABEL;
const REVIEW_WORKFLOW_ID = "playtest-review";
// Long enough that the ordinary workflow_run trigger has had its chance: the
// implementer starts within a minute of the review run and takes ten or so.
const MIN_RUN_AGE_MS = 30 * 60 * 1000;
// A second attempt only earns its keep once the first has plainly not landed.
const RETRY_COOLDOWN_MS = 2 * 60 * 60 * 1000;
const ATTEMPT_LIMIT = 2;

const PROVENANCE_COMMENT_RE = /<!--\s*gh-aw-agentic-workflow:([\s\S]*?)-->/g;
const CLOSING_KEYWORD_RE =
  /\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*:?\s+#(\d+)/gi;

function bodyOf(item) {
  return typeof item?.body === "string" ? item.body : "";
}

// The provenance marker is gh-aw's own footer comment, not free prose, so the
// run ID is read from inside that comment rather than from anywhere in the
// body. A body carrying two different provenance runs is not a run this sweep
// can reason about, so it yields nothing rather than guessing.
function provenanceRunId(issue) {
  const body = bodyOf(issue);
  const found = new Set();
  PROVENANCE_COMMENT_RE.lastIndex = 0;
  let match;
  while ((match = PROVENANCE_COMMENT_RE.exec(body)) !== null) {
    const inner = match[1];
    if (!/\bworkflow_id:\s*playtest-review\b/.test(inner)) continue;
    const idMatch = inner.match(/\bid:\s*(\d+)\b/);
    if (idMatch) found.add(idMatch[1]);
  }
  return found.size === 1 ? [...found][0] : null;
}

// The attempt number is part of the marker so the ledger can be read from the
// union of every open issue the run filed. The sweep writes the same numbered
// marker on each of them, and a duplicate is one attempt rather than several,
// which keeps the count honest after one of those issues is closed by a
// merged fix.
function dispatchMarker(runId, attempt) {
  return `<!-- playtest-catchup-dispatch:${runId}:${attempt} -->`;
}

function dispatchMarkerPrefix(runId) {
  return `<!-- playtest-catchup-dispatch:${runId}:`;
}

function offMainMarker(runId) {
  return `<!-- playtest-catchup-off-main:${runId} -->`;
}

function exhaustedMarker(runId) {
  return `<!-- playtest-catchup-needs-human:${runId} -->`;
}

function commentTime(comment) {
  const stamp = comment?.created_at || comment?.updated_at;
  const parsed = stamp ? Date.parse(stamp) : Number.NaN;
  return Number.isNaN(parsed) ? null : parsed;
}

// Attempts are counted from the sweep's own marker comments, so the ledger
// lives on the issue where a human can read it and, if they disagree, delete
// it.
function catchupState(comments, runId, now) {
  const prefix = dispatchMarkerPrefix(runId);
  const attemptRe = new RegExp(
    `${prefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(\\d+)\\s*-->`,
  );
  const seen = new Set();
  let lastAttemptAt = null;
  let escalated = false;
  let offMain = false;

  for (const comment of comments || []) {
    const body = bodyOf(comment);
    if (body.includes(exhaustedMarker(runId))) escalated = true;
    if (body.includes(offMainMarker(runId))) offMain = true;
    const match = body.match(attemptRe);
    if (!match) continue;
    seen.add(Number(match[1]));
    const at = commentTime(comment);
    if (at !== null && (lastAttemptAt === null || at > lastAttemptAt)) {
      lastAttemptAt = at;
    }
  }

  const attempts = seen.size;
  const cooling =
    lastAttemptAt !== null && now - lastAttemptAt < RETRY_COOLDOWN_MS;
  return {
    attempts,
    nextAttempt: attempts + 1,
    lastAttemptAt,
    escalated,
    offMain,
    cooling,
    exhausted: attempts >= ATTEMPT_LIMIT,
    dispatchable: attempts < ATTEMPT_LIMIT && !cooling,
  };
}

// Only a closing keyword counts. A fix PR that merely mentions an issue it
// deliberately left open must not make that issue look picked up.
function closingIssueNumbers(body) {
  const numbers = new Set();
  const text = typeof body === "string" ? body : "";
  CLOSING_KEYWORD_RE.lastIndex = 0;
  let match;
  while ((match = CLOSING_KEYWORD_RE.exec(text)) !== null) {
    numbers.add(Number(match[1]));
  }
  return numbers;
}

function coveredIssueNumbers(pulls, repository) {
  const covered = new Set();
  for (const pull of pulls || []) {
    if (!review.isAgenticPlaytestPullRequest(pull, repository)) continue;
    for (const number of closingIssueNumbers(bodyOf(pull))) covered.add(number);
  }
  return covered;
}

function hasLabel(issue, name) {
  return (issue?.labels || []).some(
    (label) => (typeof label === "string" ? label : label?.name) === name,
  );
}

function issueTime(issue) {
  const parsed = issue?.created_at ? Date.parse(issue.created_at) : Number.NaN;
  return Number.isNaN(parsed) ? 0 : parsed;
}

// Groups open playtest issues by the run that filed them and drops the ones
// already accounted for. Pull requests are open ones only: an issue closed by
// a merged fix is no longer open, and a fix PR a human closed unmerged was a
// human decision the sweep should not quietly undo, and the attempt ledger
// caps what that costs at a single extra dispatch.
function planCatchup({
  issues,
  pulls,
  repository,
  now,
  minAgeMs = MIN_RUN_AGE_MS,
}) {
  const covered = coveredIssueNumbers(pulls, repository);
  const groups = new Map();

  for (const issue of issues || []) {
    if (issue?.pull_request) continue;
    if (issue?.state && issue.state !== "open") continue;
    if (!hasLabel(issue, LABEL)) continue;
    const runId = provenanceRunId(issue);
    if (!runId) continue;
    if (!groups.has(runId)) {
      groups.set(runId, { runId, issues: [], newestIssueAt: 0 });
    }
    const group = groups.get(runId);
    group.newestIssueAt = Math.max(group.newestIssueAt, issueTime(issue));
    if (!covered.has(issue.number)) group.issues.push(issue.number);
  }

  return [...groups.values()]
    .filter((group) => group.issues.length > 0)
    .filter((group) => now - group.newestIssueAt >= minAgeMs)
    .map((group) => ({
      ...group,
      issues: [...group.issues].sort((a, b) => a - b),
    }))
    .sort((left, right) => left.newestIssueAt - right.newestIssueAt);
}

// The review run behind a provenance ID has to be a real, successful run of
// the playtest review on the default branch. A review run on any other branch
// used that branch's own copy of the reviewer instructions, and the ordinary
// trigger deliberately refuses those; the sweep must not hand them
// main-equivalent authority by the back door.
function reviewRunVerdict(run, defaultBranch) {
  if (!run) return "missing";
  const path = String(run.path || "");
  const workflowFile = path.split("/").pop() || "";
  if (!workflowFile.startsWith(`${REVIEW_WORKFLOW_ID}.`)) return "not-review";
  if (run.status !== "completed") return "incomplete";
  if (run.conclusion !== "success") return "unsuccessful";
  if (run.head_branch !== defaultBranch) return "off-main";
  return "eligible";
}

function isImplementerBusy(runs) {
  return (runs || []).some(
    (run) => run?.status === "queued" || run?.status === "in_progress",
  );
}

module.exports = {
  ATTEMPT_LIMIT,
  LABEL,
  MIN_RUN_AGE_MS,
  RETRY_COOLDOWN_MS,
  REVIEW_WORKFLOW_ID,
  catchupState,
  closingIssueNumbers,
  coveredIssueNumbers,
  dispatchMarker,
  dispatchMarkerPrefix,
  exhaustedMarker,
  isImplementerBusy,
  offMainMarker,
  planCatchup,
  provenanceRunId,
  reviewRunVerdict,
};

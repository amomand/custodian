"use strict";

const fs = require("fs");
const state = require("./agentic_review_state.cjs");

async function finalizeAgenticReview({ github, context, core }) {
  const output = JSON.parse(
    fs.readFileSync(process.env.GH_AW_AGENT_OUTPUT, "utf8"),
  );
  const items = (output.items || []).filter(
    (item) => item.type === "complete_review_round",
  );
  if (items.length !== 1) {
    core.setFailed(
      "Expected one complete_review_round item, found " + items.length,
    );
    return;
  }

  const item = items[0];
  const number = Number(item.pull_request_number);
  const reviewedHead = String(item.reviewed_head || "");
  const outcome = String(item.outcome || "");
  const summary = String(item.summary || "").trim();
  const pushHead = String(process.env.PUSH_COMMIT_SHA || "");
  if (
    String(number) !== process.env.EXPECTED_PR ||
    reviewedHead !== process.env.EXPECTED_HEAD
  ) {
    core.setFailed("Completion request does not match the workflow dispatch");
    return;
  }

  const { owner, repo } = context.repo;
  const repository = owner + "/" + repo;
  const { data: pull } = await github.rest.pulls.get({
    owner,
    repo,
    pull_number: number,
  });
  if (!state.isAgenticPlaytestPullRequest(pull, repository)) {
    core.setFailed(
      "Pull request is no longer an eligible agentic playtest fix",
    );
    return;
  }

  const currentHead = pull.head.sha;
  const comments = await github.paginate(github.rest.issues.listComments, {
    owner,
    repo,
    issue_number: number,
    per_page: 100,
  });
  let marker;
  let heading;

  if (outcome === "cap-pending") {
    if (
      process.env.EXPECTED_CYCLE !== "3" ||
      !pushHead ||
      currentHead !== pushHead
    ) {
      core.setFailed("cap-pending requires the cycle-three pushed head");
      return;
    }
    marker = state.capPendingMarker(currentHead, reviewedHead);
    heading = "Cycle 3 fix awaiting final verification";
  } else if (outcome === "clean") {
    if (pushHead || currentHead !== reviewedHead) {
      core.setFailed("clean requires an unchanged reviewed head");
      return;
    }

    const reviews = await github.paginate(github.rest.pulls.listReviews, {
      owner,
      repo,
      pull_number: number,
      per_page: 100,
    });
    const workflowRuns = await github.paginate(
      github.rest.actions.listWorkflowRunsForRepo,
      {
        owner,
        repo,
        head_sha: currentHead,
        event: "pull_request",
        per_page: 100,
      },
    );
    const ci = state.workflowRunState(workflowRuns);
    const missing = state.missingRequiredReviewers(
      reviews,
      comments,
      currentHead,
    );
    const threadResult = await github.graphql(
      [
        "query($owner: String!, $repo: String!, $number: Int!) {",
        "  repository(owner: $owner, name: $repo) {",
        "    pullRequest(number: $number) {",
        "      reviewThreads(first: 100) { nodes { isResolved } }",
        "    }",
        "  }",
        "}",
      ].join("\n"),
      { owner, repo, number },
    );
    const unresolved =
      threadResult.repository.pullRequest.reviewThreads.nodes.filter(
        (thread) => !thread.isResolved,
      ).length;
    if (
      ci.status !== "completed" ||
      ci.conclusion !== "success" ||
      missing.length ||
      unresolved
    ) {
      core.setFailed(
        [
          "Refusing clean marker:",
          "CI=" + ci.status + "/" + ci.conclusion,
          "missing=" + missing.join(","),
          "unresolved=" + unresolved,
        ].join(" "),
      );
      return;
    }
    marker = "<!-- agentic-review-clean:" + currentHead + " -->";
    heading = "Review loop complete and clean";
  } else if (outcome === "needs-human") {
    if (pushHead && currentHead !== pushHead) {
      core.setFailed("needs-human push does not match the current head");
      return;
    }
    marker = "<!-- agentic-review-needs-human -->";
    heading = "Review loop needs a human decision";
  } else {
    core.setFailed("Unsupported completion outcome: " + outcome);
    return;
  }

  if (state.hasCommentMarker(comments, marker)) {
    core.info("Marker already present: " + marker);
    return;
  }

  const body = [
    marker,
    "## " + heading,
    "",
    summary,
    "",
    "Reviewed head: `" + reviewedHead + "`" +
      (pushHead ? "\nCurrent head: `" + currentHead + "`" : "") +
      ".",
  ].join("\n");
  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: number,
    body,
  });
}

module.exports = finalizeAgenticReview;

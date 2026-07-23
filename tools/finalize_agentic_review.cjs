"use strict";

const fs = require("fs");
const state = require("./agentic_review_state.cjs");

async function currentHeadContainsPush({
  github,
  owner,
  repo,
  currentHead,
  pushHead,
}) {
  if (currentHead === pushHead) return true;

  const { data: commit } = await github.rest.repos.getCommit({
    owner,
    repo,
    ref: currentHead,
  });
  return Boolean(
    commit.parents?.length === 1 &&
      commit.parents[0].sha === pushHead &&
      Array.isArray(commit.files) &&
      commit.files.length === 0,
  );
}

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
    const validPushedHead =
      pushHead &&
      (await currentHeadContainsPush({
        github,
        owner,
        repo,
        currentHead,
        pushHead,
      }));
    if (
      process.env.EXPECTED_CYCLE !== "3" ||
      !validPushedHead
    ) {
      core.setFailed(
        "cap-pending requires the cycle-three push or its empty CI-trigger child",
      );
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
    if (pushHead) {
      const validPushedHead = await currentHeadContainsPush({
        github,
        owner,
        repo,
        currentHead,
        pushHead,
      });
      if (!validPushedHead) {
        core.setFailed("needs-human push does not match the current head");
        return;
      }
    }
    marker = "<!-- agentic-review-needs-human -->";
    heading = "Review loop needs a human decision";
  } else {
    core.setFailed("Unsupported completion outcome: " + outcome);
    return;
  }

  if (state.hasCommentMarker(comments, marker)) {
    core.info("Marker already present: " + marker);
  } else {
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

  // The doorbell: a validated terminal state is surfaced on the PR itself so
  // the PR list shows whose turn it is. The PR deliberately stays a draft:
  // GitHub's draft/ready mutations reject scoped tokens (GITHUB_TOKEN and
  // fine-grained PATs alike), and nothing in the loop needs the ready state,
  // so marking ready is a purely human act at merge time. Each ring is
  // independent so one failure cannot skip the others, and rings run even
  // when the marker already exists, so a rerun can recover a failed ring.
  const rings = [];
  if (outcome === "clean") {
    rings.push(
      [
        "assign @" + owner,
        () =>
          github.rest.issues.addAssignees({
            owner,
            repo,
            issue_number: number,
            assignees: [owner],
          }),
      ],
      [
        "apply the validated-clean label",
        () =>
          github.rest.issues.addLabels({
            owner,
            repo,
            issue_number: number,
            labels: ["validated-clean"],
          }),
      ],
    );
  } else if (outcome === "needs-human") {
    rings.push([
      "apply the needs-human label",
      () =>
        github.rest.issues.addLabels({
          owner,
          repo,
          issue_number: number,
          labels: ["needs-human"],
        }),
    ]);
  }
  const failed = [];
  for (const [description, ring] of rings) {
    try {
      await ring();
    } catch (error) {
      failed.push(description + " (" + (error?.message ?? String(error)) + ")");
    }
  }
  if (failed.length) {
    core.setFailed(
      "Terminal marker recorded, but the doorbell could not " +
        failed.join(" or ") +
        ". Re-run this job or update the PR by hand.",
    );
  }
}

module.exports = finalizeAgenticReview;

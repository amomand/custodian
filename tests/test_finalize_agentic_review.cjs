"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const finalizeAgenticReview = require("../tools/finalize_agentic_review.cjs");

const HEAD = "a".repeat(40);
const PARENT = "b".repeat(40);

function localReview(kind, head = HEAD) {
  return {
    commit_id: head,
    state: "COMMENTED",
    user: { login: "github-actions[bot]" },
    body: [
      "Custodian-Review: " + kind,
      "Head: " + head,
      "Verdict: PASS",
    ].join("\n"),
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

async function runFinalizer({
  outcome,
  currentHead = HEAD,
  reviewedHead = HEAD,
  pushHead = "",
  cycle = "1",
  ciConclusion = "success",
  comments = [],
  reviews = [
    localReview("diegesis"),
    localReview("simulation-truth"),
    copilotReview(),
  ],
  unresolved = 0,
  triggerCommitParent = null,
  triggerCommitFiles = [],
}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "agentic-finalize-"));
  const outputPath = path.join(directory, "agent-output.json");
  fs.writeFileSync(
    outputPath,
    JSON.stringify({
      items: [
        {
          type: "complete_review_round",
          pull_request_number: "77",
          reviewed_head: reviewedHead,
          outcome,
          summary: "Decision ledger.",
        },
      ],
    }),
  );
  process.env.GH_AW_AGENT_OUTPUT = outputPath;
  process.env.EXPECTED_PR = "77";
  process.env.EXPECTED_HEAD = reviewedHead;
  process.env.EXPECTED_CYCLE = cycle;
  process.env.PUSH_COMMIT_SHA = pushHead;

  const endpoints = {
    comments() {},
    reviews() {},
    runs() {},
  };
  const created = [];
  const errors = [];
  const assigned = [];
  const readied = [];
  const github = {
    rest: {
      pulls: {
        get: async () => ({
          data: {
            state: "open",
            title: "[agentic playtest] fix the finding",
            labels: [{ name: "playtest" }],
            base: { ref: "main" },
            draft: true,
            node_id: "PR_node_77",
            head: {
              sha: currentHead,
              repo: { full_name: "alex/custodian" },
            },
          },
        }),
        listReviews: endpoints.reviews,
      },
      issues: {
        listComments: endpoints.comments,
        createComment: async (payload) => {
          created.push(payload);
          return { data: payload };
        },
        addAssignees: async (payload) => {
          assigned.push(payload);
          return { data: payload };
        },
      },
      actions: {
        listWorkflowRunsForRepo: endpoints.runs,
      },
      repos: {
        getCommit: async () => ({
          data: {
            parents: triggerCommitParent
              ? [{ sha: triggerCommitParent }]
              : [],
            files: triggerCommitFiles,
          },
        }),
      },
    },
    paginate: async (endpoint) => {
      if (endpoint === endpoints.comments) return comments;
      if (endpoint === endpoints.reviews) return reviews;
      if (endpoint === endpoints.runs) {
        return [
          {
            id: 99,
            name: "CI",
            head_sha: currentHead,
            status: "completed",
            conclusion: ciConclusion,
          },
        ];
      }
      throw new Error("Unexpected pagination endpoint");
    },
    graphql: async (query, variables) => {
      if (query.includes("markPullRequestReadyForReview")) {
        readied.push(variables);
        return {
          markPullRequestReadyForReview: {
            pullRequest: { isDraft: false },
          },
        };
      }
      return {
        repository: {
          pullRequest: {
            reviewThreads: {
              nodes: Array.from({ length: unresolved }, () => ({
                isResolved: false,
              })),
            },
          },
        },
      };
    },
  };
  const core = {
    setFailed: (message) => errors.push(message),
    info() {},
  };

  await finalizeAgenticReview({
    github,
    context: { repo: { owner: "alex", repo: "custodian" } },
    core,
  });
  fs.rmSync(directory, { recursive: true, force: true });
  return { created, errors, assigned, readied };
}

test("writes a clean marker only after deterministic validation", async () => {
  const result = await runFinalizer({ outcome: "clean" });

  assert.deepEqual(result.errors, []);
  assert.equal(result.created.length, 1);
  assert.match(
    result.created[0].body,
    new RegExp("agentic-review-clean:" + HEAD),
  );
});

test("rings the doorbell on clean: ready for review, assigned to the owner", async () => {
  const result = await runFinalizer({ outcome: "clean" });

  assert.deepEqual(result.readied, [{ id: "PR_node_77" }]);
  assert.equal(result.assigned.length, 1);
  assert.deepEqual(result.assigned[0].assignees, ["alex"]);
});

test("leaves the draft alone on cap-pending and needs-human", async () => {
  const capPending = await runFinalizer({
    outcome: "cap-pending",
    currentHead: HEAD,
    reviewedHead: PARENT,
    pushHead: HEAD,
    cycle: "3",
  });
  const needsHuman = await runFinalizer({ outcome: "needs-human" });

  assert.deepEqual(capPending.readied, []);
  assert.deepEqual(capPending.assigned, []);
  assert.deepEqual(needsHuman.readied, []);
  assert.deepEqual(needsHuman.assigned, []);
});

test("refuses a clean marker while CI is failing", async () => {
  const result = await runFinalizer({
    outcome: "clean",
    ciConclusion: "failure",
  });

  assert.equal(result.created.length, 0);
  assert.match(result.errors[0], /CI=completed\/failure/);
});

test("records the pushed cycle-three head as cap-pending", async () => {
  const result = await runFinalizer({
    outcome: "cap-pending",
    currentHead: HEAD,
    reviewedHead: PARENT,
    pushHead: HEAD,
    cycle: "3",
  });

  assert.deepEqual(result.errors, []);
  assert.equal(result.created.length, 1);
  assert.match(
    result.created[0].body,
    new RegExp("agentic-review-cap-pending:" + HEAD + ":from:" + PARENT),
  );
});

test("accepts the empty CI-trigger commit above a cycle-three push", async () => {
  const result = await runFinalizer({
    outcome: "cap-pending",
    currentHead: HEAD,
    reviewedHead: "c".repeat(40),
    pushHead: PARENT,
    cycle: "3",
    triggerCommitParent: PARENT,
  });

  assert.deepEqual(result.errors, []);
  assert.equal(result.created.length, 1);
  assert.match(
    result.created[0].body,
    new RegExp("agentic-review-cap-pending:" + HEAD + ":from:" + "c".repeat(40)),
  );
});

test("rejects a changed commit above the recorded cycle-three push", async () => {
  const result = await runFinalizer({
    outcome: "cap-pending",
    currentHead: HEAD,
    reviewedHead: "c".repeat(40),
    pushHead: PARENT,
    cycle: "3",
    triggerCommitParent: PARENT,
    triggerCommitFiles: [{ filename: "src/custodian/engine.py" }],
  });

  assert.equal(result.created.length, 0);
  assert.match(result.errors[0], /empty CI-trigger child/);
});

test("refuses clean when a review thread remains unresolved", async () => {
  const result = await runFinalizer({ outcome: "clean", unresolved: 1 });

  assert.equal(result.created.length, 0);
  assert.match(result.errors[0], /unresolved=1/);
});

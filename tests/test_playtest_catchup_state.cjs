"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const catchup = require("../tools/playtest_catchup_state.cjs");

const REPOSITORY = "amomand/custodian";
const NOW = Date.parse("2026-07-29T20:00:00Z");
const HOUR = 60 * 60 * 1000;

function provenance(runId, workflowId = "playtest-review") {
  return `<!-- gh-aw-agentic-workflow: Weekly playtest review, engine: copilot, version: 1.0.73, model: claude-sonnet-4.6, id: ${runId}, workflow_id: ${workflowId}, run: https://github.com/amomand/custodian/actions/runs/${runId} -->`;
}

function issue(number, runId, options = {}) {
  return {
    number,
    state: "open",
    labels: [{ name: options.label || "playtest" }],
    created_at: options.created_at || "2026-07-29T10:14:01Z",
    body: `A finding.\n\n${options.body_marker ?? provenance(runId)}`,
  };
}

function fixPullRequest(body, overrides = {}) {
  return {
    number: 119,
    state: "open",
    title: "[agentic playtest] Only credit wrong-calm catch",
    labels: [{ name: "playtest" }],
    base: { ref: "main" },
    head: { repo: { full_name: REPOSITORY } },
    body,
    ...overrides,
  };
}

test("reads the provenance run ID out of the gh-aw footer comment", () => {
  assert.equal(catchup.provenanceRunId(issue(113, "30441857657")), "30441857657");
});

test("ignores a provenance marker written as ordinary issue prose", () => {
  const forged = issue(200, "0", {
    body_marker: "id: 30441857657, workflow_id: playtest-review",
  });
  assert.equal(catchup.provenanceRunId(forged), null);
});

test("ignores a footer from a different workflow", () => {
  const other = issue(201, "0", {
    body_marker: provenance("30441857657", "some-other-workflow"),
  });
  assert.equal(catchup.provenanceRunId(other), null);
});

test("refuses to guess when a body carries two different provenance runs", () => {
  const doubled = issue(202, "0", {
    body_marker: `${provenance("30441857657")}\n${provenance("30448965532")}`,
  });
  assert.equal(catchup.provenanceRunId(doubled), null);
});

test("only a closing keyword marks an issue as picked up", () => {
  // PR #119's real body: it closes two issues and names two more that it
  // deliberately left open.
  const body = [
    "Fixes two issues sharing one root cause in `_resolve_wrong_calm`:",
    "- Closes #117 — resolution asserted a calm the raw panel contradicts.",
    "- Closes #114 — the debrief then printed vigilance for an unread panel.",
    "Issues #113 and #111 (drift-clock balance) are left open for a separate change.",
  ].join("\n");
  const covered = catchup.coveredIssueNumbers([fixPullRequest(body)], REPOSITORY);
  assert.deepEqual([...covered].sort((a, b) => a - b), [114, 117]);
});

test("a pull request from outside the loop never covers an issue", () => {
  const stranger = fixPullRequest("Closes #113", {
    title: "Unrelated drive-by",
    labels: [],
  });
  assert.deepEqual([...catchup.coveredIssueNumbers([stranger], REPOSITORY)], []);
});

test("groups uncovered issues by run and leaves covered ones out", () => {
  const issues = [
    issue(113, "30441857657"),
    issue(114, "30441857657"),
    issue(117, "30448965532"),
  ];
  const pulls = [fixPullRequest("Closes #117\nCloses #114")];
  const plan = catchup.planCatchup({ issues, pulls, repository: REPOSITORY, now: NOW });
  assert.deepEqual(plan, [
    { runId: "30441857657", issues: [113], newestIssueAt: Date.parse("2026-07-29T10:14:01Z") },
  ]);
});

test("skips a run whose issues are younger than the trigger's own head start", () => {
  const fresh = issue(120, "30490000000", {
    created_at: new Date(NOW - 5 * 60 * 1000).toISOString(),
  });
  assert.deepEqual(
    catchup.planCatchup({ issues: [fresh], pulls: [], repository: REPOSITORY, now: NOW }),
    [],
  );
});

test("skips issues that do not carry the playtest label", () => {
  const unlabelled = issue(121, "30441857657", { label: "bug" });
  assert.deepEqual(
    catchup.planCatchup({ issues: [unlabelled], pulls: [], repository: REPOSITORY, now: NOW }),
    [],
  );
});

test("offers the oldest orphaned run first", () => {
  const issues = [
    issue(130, "30448965532", { created_at: "2026-07-29T12:01:57Z" }),
    issue(131, "30441857657", { created_at: "2026-07-29T10:14:01Z" }),
  ];
  const plan = catchup.planCatchup({ issues, pulls: [], repository: REPOSITORY, now: NOW });
  assert.deepEqual(
    plan.map((group) => group.runId),
    ["30441857657", "30448965532"],
  );
});

test("a fresh run is dispatchable and a just-attempted one is not", () => {
  const clean = catchup.catchupState([], "30441857657", NOW);
  assert.equal(clean.attempts, 0);
  assert.equal(clean.nextAttempt, 1);
  assert.equal(clean.dispatchable, true);

  const justTried = catchup.catchupState(
    [
      {
        body: catchup.dispatchMarker("30441857657", 1),
        created_at: new Date(NOW - 10 * 60 * 1000).toISOString(),
      },
    ],
    "30441857657",
    NOW,
  );
  assert.equal(justTried.attempts, 1);
  assert.equal(justTried.cooling, true);
  assert.equal(justTried.dispatchable, false);
});

test("the same attempt recorded on several issues counts once", () => {
  // One sweep marks every open issue the run filed, so the ledger survives one
  // of them being closed by a merged fix. That must not read as two attempts.
  const stamp = new Date(NOW - 3 * HOUR).toISOString();
  const state = catchup.catchupState(
    [
      { body: catchup.dispatchMarker("30441857657", 1), created_at: stamp },
      { body: catchup.dispatchMarker("30441857657", 1), created_at: stamp },
    ],
    "30441857657",
    NOW,
  );
  assert.equal(state.attempts, 1);
  assert.equal(state.nextAttempt, 2);
  assert.equal(state.dispatchable, true);
});

test("a cooled-off first attempt earns exactly one retry, then stops", () => {
  const first = {
    body: catchup.dispatchMarker("30441857657", 1),
    created_at: new Date(NOW - 3 * HOUR).toISOString(),
  };
  const cooled = catchup.catchupState([first], "30441857657", NOW);
  assert.equal(cooled.dispatchable, true);

  const second = {
    body: catchup.dispatchMarker("30441857657", 2),
    created_at: new Date(NOW - 2.5 * HOUR).toISOString(),
  };
  const spent = catchup.catchupState([first, second], "30441857657", NOW);
  assert.equal(spent.attempts, catchup.ATTEMPT_LIMIT);
  assert.equal(spent.exhausted, true);
  assert.equal(spent.dispatchable, false);
  assert.equal(spent.escalated, false);
});

test("markers for one run do not count towards another", () => {
  const state = catchup.catchupState(
    [{ body: catchup.dispatchMarker("30448965532", 1), created_at: "2026-07-29T13:00:00Z" }],
    "30441857657",
    NOW,
  );
  assert.equal(state.attempts, 0);
  assert.equal(state.dispatchable, true);
});

test("a marker forged in issue prose cannot spend the attempt budget", () => {
  // The run ID must be the whole marker, not a prefix of a longer number, and
  // the comment must actually close.
  const state = catchup.catchupState(
    [
      { body: "<!-- playtest-catchup-dispatch:304418576570:1 -->", created_at: "2026-07-29T13:00:00Z" },
      { body: "<!-- playtest-catchup-dispatch:30441857657:notanumber -->", created_at: "2026-07-29T13:00:00Z" },
    ],
    "30441857657",
    NOW,
  );
  assert.equal(state.attempts, 0);
});

test("an escalated or off-main run is remembered so it is only said once", () => {
  const comments = [
    { body: catchup.exhaustedMarker("30441857657"), created_at: "2026-07-29T14:00:00Z" },
    { body: catchup.offMainMarker("30435646548"), created_at: "2026-07-29T14:00:00Z" },
  ];
  assert.equal(catchup.catchupState(comments, "30441857657", NOW).escalated, true);
  assert.equal(catchup.catchupState(comments, "30435646548", NOW).offMain, true);
});

test("only a successful main-branch playtest review run may be re-dispatched", () => {
  const base = {
    path: ".github/workflows/playtest-review.lock.yml",
    status: "completed",
    conclusion: "success",
    head_branch: "main",
  };
  assert.equal(catchup.reviewRunVerdict(base, "main"), "eligible");
  assert.equal(
    catchup.reviewRunVerdict({ ...base, head_branch: "fictional-disco" }, "main"),
    "off-main",
  );
  assert.equal(catchup.reviewRunVerdict({ ...base, conclusion: "failure" }, "main"), "unsuccessful");
  assert.equal(catchup.reviewRunVerdict({ ...base, status: "in_progress" }, "main"), "incomplete");
  assert.equal(catchup.reviewRunVerdict(null, "main"), "missing");
});

test("a run ID pointing at some other workflow is refused", () => {
  const impostor = {
    path: ".github/workflows/playtest-fix-implementer.lock.yml",
    status: "completed",
    conclusion: "success",
    head_branch: "main",
  };
  assert.equal(catchup.reviewRunVerdict(impostor, "main"), "not-review");
});

test("does not dispatch while an implementer run is already going", () => {
  assert.equal(catchup.isImplementerBusy([{ status: "completed" }]), false);
  assert.equal(
    catchup.isImplementerBusy([{ status: "completed" }, { status: "in_progress" }]),
    true,
  );
  assert.equal(catchup.isImplementerBusy([{ status: "queued" }]), true);
});

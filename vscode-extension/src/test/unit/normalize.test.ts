import test from "node:test";
import assert from "node:assert/strict";
import {
  normalizeArtifact,
  normalizeCost,
  normalizeGate,
  normalizeRun,
  normalizeWorkspace,
} from "../../normalize";

test("normalizeRun reads the canonical tenant schema (snake_case)", () => {
  const run = normalizeRun({
    id: "run_01",
    current_pillar: 3,
    status: "running",
    cost_usd: 1.25,
    idea_text: "A SaaS for dentists",
    created_at: "2026-06-07T00:00:00Z",
  });
  assert.equal(run.id, "run_01");
  assert.equal(run.pillar, 3);
  assert.equal(run.status, "running");
  assert.equal(run.costUsd, 1.25);
  assert.equal(run.title, "A SaaS for dentists");
});

test("normalizeRun tolerates the legacy flat schema + camelCase", () => {
  const run = normalizeRun({ run_id: "run_02", pillar: "2", costTokens: "0.4" });
  assert.equal(run.id, "run_02");
  assert.equal(run.pillar, 2);
  assert.equal(run.costUsd, 0.4);
  assert.equal(run.status, "pending");
});

test("normalizeRun extracts the first pending gate from a gates array", () => {
  const run = normalizeRun({
    id: "run_03",
    gates: [
      { id: "g_old", state: "approved" },
      { id: "g_new", state: "pending", kind: "architecture" },
    ],
  });
  assert.equal(run.activeGate?.id, "g_new");
  assert.equal(run.activeGate?.kind, "architecture");
});

test("normalizeGate fills runId from context when absent", () => {
  const gate = normalizeGate({ gate_id: "g1", status: "pending" }, "run_07");
  assert.equal(gate.id, "g1");
  assert.equal(gate.runId, "run_07");
  assert.equal(gate.state, "pending");
});

test("normalizeArtifact maps url/location aliases", () => {
  const a = normalizeArtifact(
    { artifact_id: "a1", type: "erd", location: "s3://x/erd.mmd" },
    "run_1",
  );
  assert.equal(a.id, "a1");
  assert.equal(a.kind, "erd");
  assert.equal(a.uri, "s3://x/erd.mmd");
  assert.equal(a.runId, "run_1");
});

test("normalizeWorkspace and normalizeCost defaults", () => {
  assert.equal(normalizeWorkspace({ workspace_id: "w1" }).name, "Workspace");
  const cost = normalizeCost({ total_usd: 5, by_model: { gemini: 5 } });
  assert.equal(cost.totalUsd, 5);
  assert.deepEqual(cost.byModel, { gemini: 5 });
});

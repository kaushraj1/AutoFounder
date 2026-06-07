import test from "node:test";
import assert from "node:assert/strict";
import {
  formatCost,
  gateTreeLabel,
  pillarLabel,
  runTreeDescription,
  runTreeLabel,
  shortId,
  statusVisual,
} from "../../format";
import { type RunSummary } from "../../types";

test("statusVisual maps known statuses to codicons", () => {
  assert.equal(statusVisual("completed").icon, "pass-filled");
  assert.equal(statusVisual("failed").icon, "error");
  assert.equal(statusVisual("awaiting_gate").icon, "warning");
  assert.equal(statusVisual("weird-unknown").icon, "circle-outline");
});

test("pillarLabel names pillars and handles not-started", () => {
  assert.equal(pillarLabel(1), "Pillar 1 · Strategy & Ideation");
  assert.equal(pillarLabel(0), "Not started");
  assert.equal(pillarLabel(undefined), "Not started");
});

test("formatCost renders USD with small-value handling", () => {
  assert.equal(formatCost(0), "$0.00");
  assert.equal(formatCost(0.004), "<$0.01");
  assert.equal(formatCost(1.2), "$1.20");
});

test("shortId truncates long ids", () => {
  assert.equal(shortId("run_0123456789abcdef"), "0123456789…");
  assert.equal(shortId("short"), "short");
});

test("run tree label/description", () => {
  const run: RunSummary = {
    id: "run_1",
    pillar: 2,
    status: "running",
    costUsd: 0.5,
    title: "My idea",
  };
  assert.equal(runTreeLabel(run), "My idea");
  assert.equal(runTreeDescription(run), "running · $0.50 · P2");
  assert.equal(
    runTreeLabel({ id: "run_xyz", pillar: 0, status: "pending", costUsd: 0 }),
    "Run xyz",
  );
});

test("gateTreeLabel humanizes the gate kind", () => {
  assert.equal(
    gateTreeLabel({ id: "g", runId: "r", kind: "infra_spend", state: "pending" }),
    "Gate: infra spend (pending)",
  );
});

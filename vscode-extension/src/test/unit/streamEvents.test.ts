import test from "node:test";
import assert from "node:assert/strict";
import { parseStreamFrame } from "../../streamEvents";

test("parses a token frame from a JSON string", () => {
  const ev = parseStreamFrame('{"type":"token","content":"hello","step_id":"s1"}');
  assert.ok(ev);
  assert.equal(ev?.type, "token");
  assert.equal(ev?.content, "hello");
  assert.equal(ev?.stepId, "s1");
});

test("parses a gate.required frame and surfaces kind + payload", () => {
  const ev = parseStreamFrame({
    type: "gate.required",
    gate_id: "g1",
    kind: "infra_spend",
    payload: { estimate_usd: 42 },
  });
  assert.equal(ev?.type, "gate.required");
  assert.equal(ev?.gateId, "g1");
  assert.equal(ev?.gateKind, "infra_spend");
  assert.deepEqual(ev?.payload, { estimate_usd: 42 });
});

test("parses run.completed cost and run.failed error", () => {
  assert.equal(
    parseStreamFrame({ type: "run.completed", run_id: "r1", cost_usd: 0.42 })?.costUsd,
    0.42,
  );
  assert.equal(
    parseStreamFrame({ type: "run.failed", run_id: "r1", error: "boom" })?.error,
    "boom",
  );
});

test("unknown frame types are preserved as 'unknown'", () => {
  const ev = parseStreamFrame({ type: "pillar.completed", message: "Pillar 1 done" });
  assert.equal(ev?.type, "unknown");
  assert.equal(ev?.content, "Pillar 1 done");
});

test("invalid input returns null", () => {
  assert.equal(parseStreamFrame("not json"), null);
  assert.equal(parseStreamFrame(""), null);
  assert.equal(parseStreamFrame(42), null);
});

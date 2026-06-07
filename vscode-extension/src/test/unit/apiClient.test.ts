import test from "node:test";
import assert from "node:assert/strict";
import { ApiClient, type AuthTokenProvider } from "../../apiClient";
import { ApiError } from "../../http";

interface Captured {
  url: string;
  init: RequestInit;
}

function makeClient(
  handler: (url: string, init: RequestInit) => { status?: number; body?: unknown },
  opts: { token?: string; calls?: Captured[] } = {},
): ApiClient {
  const auth: AuthTokenProvider = {
    getAccessToken: async () => opts.token,
  };
  const fetchImpl = (async (input: string | URL, init?: RequestInit) => {
    const url = String(input);
    const safeInit = init ?? {};
    opts.calls?.push({ url, init: safeInit });
    const res = handler(url, safeInit);
    const status = res.status ?? 200;
    const payload = res.body === undefined ? "" : JSON.stringify(res.body);
    return new Response(payload, { status, headers: { "content-type": "application/json" } });
  }) as unknown as typeof fetch;

  return new ApiClient({ baseUrl: "http://localhost:8000/v1/", auth, fetchImpl });
}

function header(init: RequestInit, name: string): string | undefined {
  return (init.headers as Record<string, string> | undefined)?.[name];
}

test("listRuns hits /v1/runs, sends the bearer token, and normalizes", async () => {
  const calls: Captured[] = [];
  const api = makeClient(
    () => ({
      body: { data: [{ id: "run_1", status: "running", current_pillar: 2, cost_usd: 0.5 }] },
    }),
    { token: "tok123", calls },
  );
  const runs = await api.listRuns();
  assert.equal(runs.length, 1);
  assert.equal(runs[0].id, "run_1");
  assert.equal(runs[0].pillar, 2);
  assert.equal(runs[0].costUsd, 0.5);
  assert.ok(calls[0].url.includes("/v1/runs"));
  assert.ok(!calls[0].url.includes("/v1/v1"), "must not double the version prefix");
  assert.equal(header(calls[0].init, "Authorization"), "Bearer tok123");
});

test("listRuns(workspaceId) uses the workspace-scoped path", async () => {
  const calls: Captured[] = [];
  const api = makeClient(() => ({ body: { data: [] } }), { calls });
  await api.listRuns("ws_9");
  assert.ok(calls[0].url.includes("/v1/workspaces/ws_9/runs"));
});

test("omits Authorization when signed out", async () => {
  const calls: Captured[] = [];
  const api = makeClient(() => ({ body: { data: [] } }), { calls });
  await api.listRuns();
  assert.equal(header(calls[0].init, "Authorization"), undefined);
});

test("submitIdea posts idea_text", async () => {
  const calls: Captured[] = [];
  const api = makeClient(() => ({ body: { data: { id: "run_x", status: "pending" } } }), { calls });
  const run = await api.submitIdea("a great idea");
  assert.equal(run.id, "run_x");
  assert.equal(calls[0].init.method, "POST");
  const body = JSON.parse(calls[0].init.body as string) as { idea_text: string };
  assert.equal(body.idea_text, "a great idea");
});

test("decideGate posts the decision to the gate path", async () => {
  const calls: Captured[] = [];
  const api = makeClient(() => ({ status: 200, body: { data: {} } }), { calls });
  await api.decideGate("run_1", "g1", "approved", "looks good");
  assert.equal(calls[0].init.method, "POST");
  assert.ok(calls[0].url.endsWith("/v1/runs/run_1/gates/g1"));
  const body = JSON.parse(calls[0].init.body as string) as { decision: string; notes: string };
  assert.equal(body.decision, "approved");
  // Must be `notes` (plural) to match the backend GateDecision schema / pivot_text.
  assert.equal(body.notes, "looks good");
});

test("throws a typed ApiError on a 409 conflict", async () => {
  const api = makeClient(() => ({
    status: 409,
    body: { error: { code: "AF_ERR_CONFLICT", message: "already decided" } },
  }));
  await assert.rejects(
    () => api.getRun("run_1"),
    (err: unknown) =>
      err instanceof ApiError && err.status === 409 && err.code === "AF_ERR_CONFLICT",
  );
});

test("getCost normalizes the cost summary", async () => {
  const api = makeClient(() => ({ body: { data: { total_usd: 3.5, by_pillar: { "1": 3.5 } } } }));
  const cost = await api.getCost();
  assert.equal(cost.totalUsd, 3.5);
  assert.deepEqual(cost.byPillar, { "1": 3.5 });
});

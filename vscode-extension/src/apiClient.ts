/**
 * Typed REST client for the AutoFounder AI backend (AF-030 contract).
 *
 * No `vscode` dependency — it takes a base URL and an {@link AuthTokenProvider},
 * so it is fully unit-testable with a mocked `fetch`. Every response is unwrapped
 * from the success envelope and normalized to a stable domain type; failures throw
 * an {@link ApiError} carrying the backend error code.
 */

import { ApiError, normalizeBaseUrl, parseApiError, unwrapData } from "./http";
import { normalizeArtifact, normalizeCost, normalizeRun, normalizeWorkspace } from "./normalize";
import {
  type Artifact,
  type CodeGenRequest,
  type CostSummary,
  type GateDecision,
  type RunSummary,
  type Workspace,
} from "./types";

export interface AuthTokenProvider {
  /** Returns a valid bearer token, refreshing if needed, or undefined when signed out. */
  getAccessToken(): Promise<string | undefined>;
}

export interface ApiClientOptions {
  /** Backend base URL, or a getter so live settings changes take effect. */
  baseUrl: string | (() => string);
  auth: AuthTokenProvider;
  /** Per-request timeout in ms (default 15000, per the plan's rate-limit table). */
  timeoutMs?: number;
  /** Injectable for tests; defaults to the global fetch. */
  fetchImpl?: typeof fetch;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  signal?: AbortSignal;
}

export class ApiClient {
  private readonly baseUrlProvider: () => string;
  private readonly auth: AuthTokenProvider;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof fetch;

  constructor(opts: ApiClientOptions) {
    this.baseUrlProvider =
      typeof opts.baseUrl === "function" ? opts.baseUrl : () => opts.baseUrl as string;
    this.auth = opts.auth;
    this.timeoutMs = opts.timeoutMs ?? 15_000;
    this.fetchImpl = opts.fetchImpl ?? globalThis.fetch;
  }

  async listWorkspaces(): Promise<Workspace[]> {
    const data = await this.request("/v1/workspaces");
    return toArray(data).map(normalizeWorkspace);
  }

  async listRuns(workspaceId?: string): Promise<RunSummary[]> {
    const path = workspaceId
      ? `/v1/workspaces/${encodeURIComponent(workspaceId)}/runs`
      : "/v1/runs";
    const data = await this.request(path, { query: { limit: 50, order: "desc" } });
    return toArray(data).map(normalizeRun);
  }

  async getRun(runId: string): Promise<RunSummary> {
    const data = await this.request(`/v1/runs/${encodeURIComponent(runId)}`);
    return normalizeRun(data);
  }

  async submitIdea(text: string, workspaceId?: string): Promise<RunSummary> {
    const body: Record<string, unknown> = { idea_text: text, text };
    if (workspaceId) body.workspace_id = workspaceId;
    const data = await this.request("/v1/ideas", { method: "POST", body });
    return normalizeRun(data);
  }

  async decideGate(
    runId: string,
    gateId: string,
    decision: GateDecision,
    note?: string,
  ): Promise<void> {
    // Backend `GateDecision` field is `notes` (plural); it is fed to `pivot_text`
    // on a rejected gate so the orchestrator re-runs with the founder's correction.
    await this.request(
      `/v1/runs/${encodeURIComponent(runId)}/gates/${encodeURIComponent(gateId)}`,
      { method: "POST", body: { decision, notes: note } },
    );
  }

  async cancelRun(runId: string): Promise<void> {
    await this.request(`/v1/runs/${encodeURIComponent(runId)}`, { method: "DELETE" });
  }

  async listArtifacts(runId: string): Promise<Artifact[]> {
    const data = await this.request(`/v1/runs/${encodeURIComponent(runId)}/artifacts`);
    return toArray(data).map((a) => normalizeArtifact(a, runId));
  }

  async getCost(): Promise<CostSummary> {
    const data = await this.request("/v1/llmops/cost");
    return normalizeCost(data);
  }

  /**
   * Stream code-generation tokens from the Coder Agent (AF-041).
   *
   * AF-041 is not yet shipped; until the `/v1/codegen` streaming endpoint exists
   * this yields a clearly-labelled placeholder so the command is fully usable and
   * the wiring is identical once the backend lands.
   */
  async *streamCodeGen(req: CodeGenRequest): AsyncGenerator<string> {
    let response: Response;
    try {
      response = await this.rawFetch("/v1/codegen", {
        method: "POST",
        body: req,
      });
    } catch {
      yield* placeholderCodeGen(req);
      return;
    }

    if (!response.ok || !response.body) {
      yield* placeholderCodeGen(req);
      return;
    }

    const decoder = new TextDecoder();
    // Node 18 fetch returns a web ReadableStream which is async-iterable.
    for await (const chunk of response.body as unknown as AsyncIterable<Uint8Array>) {
      const text = decoder.decode(chunk, { stream: true });
      if (text.length > 0) yield text;
    }
  }

  private async request(path: string, opts: RequestOptions = {}): Promise<unknown> {
    const response = await this.rawFetch(path, opts);
    const body = await safeJson(response);
    if (!response.ok) {
      throw parseApiError(response.status, body);
    }
    return unwrapData(body);
  }

  private async rawFetch(path: string, opts: RequestOptions): Promise<Response> {
    const url = new URL(`${normalizeBaseUrl(this.baseUrlProvider())}${path}`);
    for (const [key, value] of Object.entries(opts.query ?? {})) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }

    const token = await this.auth.getAccessToken();
    const headers: Record<string, string> = { Accept: "application/json" };
    if (opts.body !== undefined) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    const signal = opts.signal ? anySignal([opts.signal, controller.signal]) : controller.signal;

    try {
      return await this.fetchImpl(url.toString(), {
        method: opts.method ?? "GET",
        headers,
        body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
        signal,
      });
    } catch (err) {
      if (controller.signal.aborted) {
        throw new ApiError("Request timed out", 0, "AF_ERR_TIMEOUT");
      }
      throw new ApiError(
        err instanceof Error ? err.message : "Network request failed",
        0,
        "AF_ERR_NETWORK",
      );
    } finally {
      clearTimeout(timer);
    }
  }
}

function toArray(data: unknown): unknown[] {
  if (Array.isArray(data)) return data;
  if (data === null || data === undefined) return [];
  // Some collection endpoints nest under `items`/`runs`/`artifacts`.
  if (typeof data === "object") {
    for (const key of ["items", "runs", "artifacts", "workspaces", "results"]) {
      const v = (data as Record<string, unknown>)[key];
      if (Array.isArray(v)) return v;
    }
  }
  return [data];
}

async function safeJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text.length === 0) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

/** Combine multiple AbortSignals (Node 18 lacks `AbortSignal.any`). */
function anySignal(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort();
      break;
    }
    signal.addEventListener("abort", () => controller.abort(), { once: true });
  }
  return controller.signal;
}

async function* placeholderCodeGen(req: CodeGenRequest): AsyncGenerator<string> {
  const lines = [
    `// AutoFounder AI — ${req.kind === "component" ? "Component" : "API Endpoint"} generation`,
    `// Coder Agent (AF-041) is not wired to this environment yet.`,
    `// Configure 'autofounder.apiBaseUrl' to a backend exposing POST /v1/codegen to stream real output.`,
    "//",
    `// Requested spec:`,
    ...req.spec.split("\n").map((l) => `//   ${l}`),
    "",
  ];
  for (const line of lines) {
    yield `${line}\n`;
  }
}

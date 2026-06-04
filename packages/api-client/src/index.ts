/**
 * Typed client for the AutoFounder AI backend.
 *
 * Phase 1 ships this hand-written minimal client. Phase 2 replaces it with a client
 * generated from the backend's OpenAPI spec (e.g. openapi-typescript / orval).
 */

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  env: string;
}

export type RunStatus = "pending" | "running" | "awaiting_gate" | "completed" | "failed";

export interface RunRead {
  id: string;
  pillar: string;
  status: RunStatus;
  created_at: string;
}

export interface IdeaCreate {
  text: string;
}

export class AutoFounderClient {
  constructor(private readonly baseUrl: string) {}

  health(): Promise<HealthResponse> {
    return this.request<HealthResponse>("GET", "/health");
  }

  submitIdea(idea: IdeaCreate): Promise<RunRead> {
    return this.request<RunRead>("POST", "/v1/ideas", idea);
  }

  getRun(runId: string): Promise<RunRead> {
    return this.request<RunRead>("GET", `/v1/runs/${runId}`);
  }

  listRuns(): Promise<RunRead[]> {
    return this.request<RunRead[]>("GET", "/v1/runs");
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`AutoFounder API ${method} ${path} failed: ${response.status}`);
    }
    return (await response.json()) as T;
  }
}

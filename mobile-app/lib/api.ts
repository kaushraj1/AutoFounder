import { supabase } from "./supabase";

const API_BASE = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

async function authHeaders(): Promise<HeadersInit> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return {
    "Content-Type": "application/json",
    ...(session?.access_token
      ? { Authorization: `Bearer ${session.access_token}` }
      : {}),
  };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = await authHeaders();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers ?? {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Runs
  getRuns: () => request<{ items: unknown[] }>("/v1/runs"),

  getRunById: (runId: string) => request<unknown>(`/v1/runs/${runId}`),

  // Ideas
  createIdea: (text: string, domain?: string) =>
    request<{ run_id: string; status: string }>("/v1/ideas", {
      method: "POST",
      body: JSON.stringify({ text, domain }),
    }),

  // HITL gates
  approveGate: (runId: string, gateId: string, decision: "approve" | "reject", comment?: string) =>
    request<{ success: boolean }>(`/v1/runs/${runId}/gates/${gateId}`, {
      method: "POST",
      body: JSON.stringify({ decision, comment }),
    }),

  // Monitoring
  getMonitoring: () => request<unknown>("/v1/monitoring"),
};

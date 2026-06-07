/**
 * Tolerant normalizers: backend wire JSON (unknown shape) -> stable domain types.
 *
 * The AF-030 REST surface is still in flux — the same logical field can arrive as
 * `cost_usd`, `costUsd`, or `cost_tokens`, and the run id as `id` or `run_id`.
 * These readers accept every known alias so the UI keeps working across backend
 * revisions instead of crashing on a renamed field.
 */

import {
  type Artifact,
  type CostSummary,
  type Gate,
  type RunSummary,
  type Workspace,
} from "./types";

export function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

/** First string-valued key that is present and non-empty. */
function str(rec: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const v = rec[key];
    if (typeof v === "string" && v.length > 0) return v;
  }
  return undefined;
}

/** First number-valued key (accepts numeric strings). */
function num(rec: Record<string, unknown>, ...keys: string[]): number | undefined {
  for (const key of keys) {
    const v = rec[key];
    if (typeof v === "number" && Number.isFinite(v)) return v;
    if (typeof v === "string" && v.trim() !== "" && Number.isFinite(Number(v))) return Number(v);
  }
  return undefined;
}

export function normalizeRun(raw: unknown): RunSummary {
  const rec = asRecord(raw);
  const id = str(rec, "id", "run_id", "runId") ?? "";
  const gateRaw = rec.active_gate ?? rec.activeGate ?? firstPendingGate(rec.gates);
  return {
    id,
    pillar: num(rec, "current_pillar", "currentPillar", "pillar") ?? 0,
    status: str(rec, "status", "state") ?? "pending",
    costUsd: num(rec, "cost_usd", "costUsd", "cost_tokens", "costTokens") ?? 0,
    title: str(rec, "title", "idea_text", "ideaText", "idea", "name"),
    createdAt: str(rec, "created_at", "createdAt"),
    activeGate: gateRaw ? normalizeGate(gateRaw, id) : undefined,
  };
}

function firstPendingGate(value: unknown): unknown {
  if (!Array.isArray(value)) return undefined;
  return value.find((g) => {
    const state = str(asRecord(g), "state", "status");
    return state === "pending" || state === undefined;
  });
}

export function normalizeGate(raw: unknown, runId?: string): Gate {
  const rec = asRecord(raw);
  return {
    id: str(rec, "id", "gate_id", "gateId") ?? "",
    runId: str(rec, "run_id", "runId") ?? runId ?? "",
    kind: str(rec, "kind", "gate_kind", "type") ?? "approval",
    state: str(rec, "state", "status") ?? "pending",
    payload: rec.payload ? asRecord(rec.payload) : undefined,
  };
}

export function normalizeArtifact(raw: unknown, runId?: string): Artifact {
  const rec = asRecord(raw);
  return {
    id: str(rec, "id", "artifact_id", "artifactId") ?? "",
    runId: str(rec, "run_id", "runId") ?? runId ?? "",
    kind: str(rec, "kind", "type", "artifact_type") ?? "artifact",
    uri: str(rec, "uri", "url", "location", "s3_uri", "path") ?? "",
    title: str(rec, "title", "name", "label"),
    content: str(rec, "content", "body", "text"),
    mimeType: str(rec, "mime_type", "mimeType", "content_type", "contentType"),
  };
}

export function normalizeWorkspace(raw: unknown): Workspace {
  const rec = asRecord(raw);
  return {
    id: str(rec, "id", "workspace_id", "workspaceId") ?? "",
    name: str(rec, "name", "title", "slug") ?? "Workspace",
  };
}

export function normalizeCost(raw: unknown): CostSummary {
  const rec = asRecord(raw);
  return {
    totalUsd: num(rec, "total_usd", "totalUsd", "total", "cost_usd") ?? 0,
    byModel: toNumberMap(rec.by_model ?? rec.byModel),
    byPillar: toNumberMap(rec.by_pillar ?? rec.byPillar),
  };
}

function toNumberMap(value: unknown): Record<string, number> | undefined {
  if (value === null || typeof value !== "object") return undefined;
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    if (typeof v === "number" && Number.isFinite(v)) out[k] = v;
    else if (typeof v === "string" && Number.isFinite(Number(v))) out[k] = Number(v);
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

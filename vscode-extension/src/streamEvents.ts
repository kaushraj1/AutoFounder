/**
 * Pure parser for live run-stream frames.
 *
 * Server -> client frames (api-design.md §WebSocket):
 *   { type: "step.started",   step_id, agent_id, at }
 *   { type: "token",          content, step_id }
 *   { type: "tool.call",      tool, args, step_id }
 *   { type: "step.completed", step_id, at }
 *   { type: "gate.required",  gate_id, kind, payload }
 *   { type: "run.completed",  run_id, cost_usd }
 *   { type: "run.failed",     run_id, error }
 *
 * Also tolerates AF-031 Supabase Realtime `step_events` rows (which carry a
 * `message`/`agent_id` row rather than a typed frame).
 */

import { asRecord } from "./normalize";
import { type StreamEvent, type StreamEventType } from "./types";

const KNOWN_TYPES: ReadonlySet<string> = new Set([
  "step.started",
  "token",
  "tool.call",
  "step.completed",
  "gate.required",
  "run.completed",
  "run.failed",
]);

function readString(rec: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const v = rec[key];
    if (typeof v === "string" && v.length > 0) return v;
  }
  return undefined;
}

function readNumber(rec: Record<string, unknown>, ...keys: string[]): number | undefined {
  for (const key of keys) {
    const v = rec[key];
    if (typeof v === "number" && Number.isFinite(v)) return v;
    if (typeof v === "string" && v.trim() !== "" && Number.isFinite(Number(v))) return Number(v);
  }
  return undefined;
}

/** Parse one frame (JSON string or already-decoded object) into a {@link StreamEvent}. */
export function parseStreamFrame(input: unknown): StreamEvent | null {
  let decoded: unknown = input;
  if (typeof input === "string") {
    const trimmed = input.trim();
    if (trimmed.length === 0) return null;
    try {
      decoded = JSON.parse(trimmed);
    } catch {
      return null;
    }
  }
  if (decoded === null || typeof decoded !== "object") return null;

  const rec = asRecord(decoded);
  const rawType = readString(rec, "type", "event");
  const type: StreamEventType =
    rawType !== undefined && KNOWN_TYPES.has(rawType) ? (rawType as StreamEventType) : "unknown";

  const event: StreamEvent = {
    type,
    runId: readString(rec, "run_id", "runId"),
    stepId: readString(rec, "step_id", "stepId"),
    agentId: readString(rec, "agent_id", "agentId"),
    pillar: readNumber(rec, "pillar", "current_pillar"),
    content: readString(rec, "content", "token", "message", "text"),
    toolName: readString(rec, "tool", "tool_name"),
    gateId: readString(rec, "gate_id", "gateId"),
    gateKind: type === "gate.required" ? readString(rec, "kind", "gate_kind") : undefined,
    payload: rec.payload ? asRecord(rec.payload) : undefined,
    costUsd: readNumber(rec, "cost_usd", "costUsd"),
    error: readString(rec, "error", "error_message"),
    at: readString(rec, "at", "ts", "timestamp"),
    raw: rec,
  };
  return event;
}

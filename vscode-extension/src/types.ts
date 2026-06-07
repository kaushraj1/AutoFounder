/**
 * Shared domain contract for the AutoFounder AI VS Code extension.
 *
 * These camelCase domain types are produced by the normalizers in `normalize.ts`
 * from the backend's snake_case wire JSON (AF-030 REST + AF-031 Realtime + AF-034
 * HITL). Keeping a stable domain shape here insulates the UI from backend schema
 * churn (e.g. the flat-vs-tenant `runs` table divergence).
 */

export type RunStatus =
  | "pending"
  | "running"
  | "awaiting_gate"
  | "completed"
  | "failed"
  | "cancelled"
  | (string & {});

export interface RunSummary {
  id: string;
  /** Current pillar 1..7; 0 when unknown. */
  pillar: number;
  status: RunStatus;
  /** Accumulated cost in USD. */
  costUsd: number;
  /** Idea text / human title for the run. */
  title?: string;
  createdAt?: string;
  /** The gate currently awaiting a decision, if any. */
  activeGate?: Gate;
}

export type GateState = "pending" | "approved" | "rejected" | "timed_out" | (string & {});

export interface Gate {
  id: string;
  runId: string;
  /** e.g. "validation" | "architecture" | "infra_spend" | "launch". */
  kind: string;
  state: GateState;
  payload?: Record<string, unknown>;
}

export interface Artifact {
  id: string;
  runId: string;
  /** e.g. "lean_canvas" | "erd" | "openapi" | "brand_kit". */
  kind: string;
  /** Location of the artifact content (signed URL or backend content path). */
  uri: string;
  title?: string;
  /** Inline content when the backend embeds it on the artifact record. */
  content?: string;
  mimeType?: string;
}

export interface Workspace {
  id: string;
  name: string;
}

export interface CostSummary {
  totalUsd: number;
  byModel?: Record<string, number>;
  byPillar?: Record<string, number>;
}

export type StreamEventType =
  | "step.started"
  | "token"
  | "tool.call"
  | "step.completed"
  | "gate.required"
  | "run.completed"
  | "run.failed"
  | "unknown";

export interface StreamEvent {
  type: StreamEventType;
  runId?: string;
  stepId?: string;
  agentId?: string;
  pillar?: number;
  /** Token text for `token`, or a human-readable message for other frames. */
  content?: string;
  toolName?: string;
  gateId?: string;
  gateKind?: string;
  payload?: Record<string, unknown>;
  costUsd?: number;
  error?: string;
  at?: string;
  /** The raw decoded frame, for forward-compatibility. */
  raw: Record<string, unknown>;
}

export type GateDecision = "approved" | "rejected";

export interface CodeGenRequest {
  kind: "component" | "api_endpoint";
  spec: string;
  runId?: string;
}

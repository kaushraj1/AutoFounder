/**
 * Pure presentation helpers (no `vscode`): status -> codicon, pillar names, cost
 * formatting, and tree row text. The sidebar maps the returned codicon id to a
 * `vscode.ThemeIcon`.
 */

import { type Gate, type RunSummary } from "./types";

export const PILLAR_NAMES: Readonly<Record<number, string>> = {
  1: "Strategy & Ideation",
  2: "Architecture",
  3: "Engineering",
  4: "Review & QA",
  5: "DevOps",
  6: "Marketing",
  7: "LLMOps",
};

export interface StatusVisual {
  /** VS Code codicon id (without the `$(...)` wrapper). */
  icon: string;
  /** Theme color id, or undefined for the default foreground. */
  color?: string;
}

export function statusVisual(status: string): StatusVisual {
  switch (status) {
    case "completed":
      return { icon: "pass-filled", color: "testing.iconPassed" };
    case "failed":
      return { icon: "error", color: "testing.iconFailed" };
    case "cancelled":
      return { icon: "circle-slash", color: "disabledForeground" };
    case "awaiting_gate":
      return { icon: "warning", color: "notificationsWarningIcon.foreground" };
    case "running":
      return { icon: "sync", color: "charts.blue" };
    case "pending":
      return { icon: "clock", color: "charts.yellow" };
    default:
      return { icon: "circle-outline" };
  }
}

export function pillarLabel(pillar: number | undefined): string {
  if (!pillar || pillar < 1) return "Not started";
  const name = PILLAR_NAMES[pillar];
  return name ? `Pillar ${pillar} · ${name}` : `Pillar ${pillar}`;
}

export function formatCost(usd: number | undefined): string {
  const value = usd ?? 0;
  if (value === 0) return "$0.00";
  if (value < 0.01) return "<$0.01";
  return `$${value.toFixed(2)}`;
}

/** Short, stable id fragment for labels (`run_01ABC…` -> `01ABC…`). */
export function shortId(id: string): string {
  const tail = id.includes("_") ? id.slice(id.lastIndexOf("_") + 1) : id;
  return tail.length > 10 ? `${tail.slice(0, 10)}…` : tail;
}

export function runTreeLabel(run: RunSummary): string {
  if (run.title && run.title.trim().length > 0) {
    const title = run.title.trim();
    return title.length > 48 ? `${title.slice(0, 48)}…` : title;
  }
  return `Run ${shortId(run.id)}`;
}

export function runTreeDescription(run: RunSummary): string {
  const parts = [run.status, formatCost(run.costUsd)];
  if (run.pillar >= 1) parts.push(`P${run.pillar}`);
  return parts.join(" · ");
}

export function gateTreeLabel(gate: Gate): string {
  const kind = gate.kind ? gate.kind.replace(/_/g, " ") : "approval";
  return `Gate: ${kind} (${gate.state})`;
}

/**
 * AF-074 — HITL gate notifications.
 *
 * Shows a VS Code notification banner the first time a run needs a human decision
 * (driven by `RunMonitor.onGateRequired`), with inline Approve / Reject actions
 * that POST `/v1/runs/{id}/gates/{id}` (AF-034). The same decision flow backs the
 * `autofounder.decideGate` command invoked from the sidebar gate node.
 */

import * as vscode from "vscode";
import { type ApiClient } from "./apiClient";
import { ApiError } from "./http";
import { type RunMonitor, type GateRequiredEvent } from "./runMonitor";
import { type GateDecision } from "./types";

interface GateTarget {
  runId: string;
  gateId: string;
  kind?: string;
}

export class GateService {
  constructor(
    private readonly api: ApiClient,
    private readonly monitor: RunMonitor,
  ) {}

  /** Banner shown when the monitor first sees a run awaiting a gate. */
  async showGateBanner(event: GateRequiredEvent): Promise<void> {
    const { run, gate } = event;
    const kind = (gate.kind || "approval").replace(/_/g, " ");
    const choice = await vscode.window.showInformationMessage(
      `AutoFounder AI — gate required: ${kind} for "${run.title ?? run.id}".`,
      "Approve",
      "Reject",
      "Open Stream",
    );
    if (choice === "Open Stream") {
      await vscode.commands.executeCommand("autofounder.openStream", run.id);
      return;
    }
    if (choice === "Approve") {
      await this.decide({ runId: run.id, gateId: gate.id, kind: gate.kind }, "approved");
    } else if (choice === "Reject") {
      await this.promptAndDecide({ runId: run.id, gateId: gate.id, kind: gate.kind }, "rejected");
    }
  }

  /** Command handler for `autofounder.decideGate` (sidebar gate node). */
  async decideGateCommand(arg?: unknown): Promise<void> {
    const target = this.resolveTarget(arg);
    if (!target) {
      vscode.window.showInformationMessage("AutoFounder AI: no pending gate to decide.");
      return;
    }

    const decision = await vscode.window.showQuickPick(
      [
        { label: "$(check) Approve", value: "approved" as const },
        { label: "$(x) Reject", value: "rejected" as const },
      ],
      {
        title: `Decide gate (${(target.kind ?? "approval").replace(/_/g, " ")})`,
        placeHolder: "Approve or reject this gate",
      },
    );
    if (!decision) return;
    await this.promptAndDecide(target, decision.value);
  }

  private resolveTarget(arg?: unknown): GateTarget | undefined {
    if (arg && typeof arg === "object") {
      const a = arg as Record<string, unknown>;
      // Direct payload from the gate TreeItem's command arguments.
      if (typeof a.runId === "string" && typeof a.gateId === "string") {
        return {
          runId: a.runId,
          gateId: a.gateId,
          kind: typeof a.kind === "string" ? a.kind : undefined,
        };
      }
      // Tree node passed by an inline context-menu button: { kind:"gate", run, gate }.
      const run = a.run as Record<string, unknown> | undefined;
      const gate = a.gate as Record<string, unknown> | undefined;
      if (run && gate && typeof run.id === "string" && typeof gate.id === "string") {
        return {
          runId: run.id,
          gateId: gate.id,
          kind: typeof gate.kind === "string" ? gate.kind : undefined,
        };
      }
    }
    const pending = this.monitor.getRuns().find((r) => r.activeGate?.state === "pending");
    if (pending?.activeGate) {
      return { runId: pending.id, gateId: pending.activeGate.id, kind: pending.activeGate.kind };
    }
    return undefined;
  }

  private async promptAndDecide(target: GateTarget, decision: GateDecision): Promise<void> {
    const note = await vscode.window.showInputBox({
      title: `${decision === "approved" ? "Approve" : "Reject"} gate`,
      prompt: "Optional note for the audit log (leave empty to skip).",
      ignoreFocusOut: true,
    });
    if (note === undefined) return; // user pressed Escape
    await this.decide(target, decision, note.trim() === "" ? undefined : note.trim());
  }

  private async decide(target: GateTarget, decision: GateDecision, note?: string): Promise<void> {
    try {
      await this.api.decideGate(target.runId, target.gateId, decision, note);
      vscode.window.showInformationMessage(`AutoFounder AI: gate ${decision}.`);
      await this.monitor.refresh();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        vscode.window.showWarningMessage(`AutoFounder AI: this gate was already decided.`);
        await this.monitor.refresh();
        return;
      }
      const message = err instanceof Error ? err.message : String(err);
      vscode.window.showErrorMessage(`AutoFounder AI: failed to ${decision} gate — ${message}`);
    }
  }
}

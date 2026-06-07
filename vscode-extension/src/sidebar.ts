/**
 * AF-073 — Sidebar tree view.
 *
 * Renders the run list with status icons, a pillar-progress child, a live cost
 * badge, and (when present) the active HITL gate as an actionable child node.
 * Data comes from the {@link RunMonitor} cache; `refresh()` is driven by the
 * monitor's `onDidChangeRuns`.
 */

import * as vscode from "vscode";
import {
  formatCost,
  gateTreeLabel,
  pillarLabel,
  runTreeDescription,
  runTreeLabel,
  statusVisual,
} from "./format";
import { type RunMonitor } from "./runMonitor";
import { type Gate, type RunSummary } from "./types";

type TreeNode =
  | { kind: "run"; run: RunSummary }
  | { kind: "detail"; icon: string; label: string }
  | { kind: "gate"; run: RunSummary; gate: Gate };

export class RunTreeProvider implements vscode.TreeDataProvider<TreeNode> {
  private readonly changeEmitter = new vscode.EventEmitter<TreeNode | undefined>();
  readonly onDidChangeTreeData = this.changeEmitter.event;

  constructor(private readonly monitor: RunMonitor) {}

  refresh(): void {
    this.changeEmitter.fire(undefined);
  }

  getTreeItem(node: TreeNode): vscode.TreeItem {
    switch (node.kind) {
      case "run":
        return this.runItem(node.run);
      case "gate":
        return this.gateItem(node.run, node.gate);
      case "detail": {
        const item = new vscode.TreeItem(node.label, vscode.TreeItemCollapsibleState.None);
        item.iconPath = new vscode.ThemeIcon(node.icon);
        return item;
      }
    }
  }

  getChildren(element?: TreeNode): TreeNode[] {
    if (!element) {
      return this.monitor.getRuns().map((run) => ({ kind: "run", run }));
    }
    if (element.kind === "run") {
      const { run } = element;
      const children: TreeNode[] = [
        { kind: "detail", icon: "layers", label: pillarLabel(run.pillar) },
        { kind: "detail", icon: "credit-card", label: `Cost: ${formatCost(run.costUsd)}` },
      ];
      if (run.activeGate) {
        children.unshift({ kind: "gate", run, gate: run.activeGate });
      }
      return children;
    }
    return [];
  }

  private runItem(run: RunSummary): vscode.TreeItem {
    const item = new vscode.TreeItem(runTreeLabel(run), vscode.TreeItemCollapsibleState.Collapsed);
    item.id = run.id;
    item.description = runTreeDescription(run);
    item.contextValue = "run";
    const visual = statusVisual(run.status);
    item.iconPath = new vscode.ThemeIcon(
      visual.icon,
      visual.color ? new vscode.ThemeColor(visual.color) : undefined,
    );
    item.tooltip = new vscode.MarkdownString(
      [
        `**${runTreeLabel(run)}**`,
        "",
        `- Status: \`${run.status}\``,
        `- ${pillarLabel(run.pillar)}`,
        `- Cost: ${formatCost(run.costUsd)}`,
        run.createdAt ? `- Created: ${run.createdAt}` : undefined,
      ]
        .filter((l): l is string => l !== undefined)
        .join("\n"),
    );
    item.command = {
      command: "autofounder.openStream",
      title: "Open Live Stream",
      arguments: [run.id],
    };
    return item;
  }

  private gateItem(run: RunSummary, gate: Gate): vscode.TreeItem {
    const item = new vscode.TreeItem(gateTreeLabel(gate), vscode.TreeItemCollapsibleState.None);
    item.contextValue = "gate";
    item.iconPath = new vscode.ThemeIcon(
      "warning",
      new vscode.ThemeColor("notificationsWarningIcon.foreground"),
    );
    item.command = {
      command: "autofounder.decideGate",
      title: "Approve / Reject Gate",
      arguments: [{ runId: run.id, gateId: gate.id, kind: gate.kind }],
    };
    return item;
  }
}

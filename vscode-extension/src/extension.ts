/**
 * AF-072 — Extension activation core.
 *
 * Wires the AutoFounder AI clients and surfaces: Supabase PKCE auth (-> SecretStorage),
 * the typed REST client, the run monitor, the sidebar tree (AF-073), gate
 * notifications (AF-074), code-gen commands (AF-075), the live stream panel (AF-076),
 * and artifact quick-open (AF-077). Everything is registered as a disposable on the
 * extension context so deactivation is clean.
 */

import * as vscode from "vscode";
import { ApiClient } from "./apiClient";
import { ArtifactService } from "./artifacts";
import { AuthManager } from "./auth";
import { CodeGenService } from "./codegen";
import { onConfigChange, readConfig } from "./config";
import { formatCost, shortId } from "./format";
import { ApiError, toWebSocketBase } from "./http";
import { GateService } from "./gates";
import { RunMonitor } from "./runMonitor";
import { RunStream } from "./runStream";
import { RunTreeProvider } from "./sidebar";
import { StreamPanel, type StreamFactory } from "./streamPanel";
import { type RunSummary } from "./types";

const LAST_RUN_KEY = "autofounder.lastRunId";

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const auth = new AuthManager(context.secrets, readConfig);
  const api = new ApiClient({ baseUrl: () => readConfig().apiBaseUrl, auth });

  const monitor = new RunMonitor({
    getApi: () => api,
    getIntervalMs: () => readConfig().pollIntervalMs,
    isAuthenticated: () => auth.isAuthenticated(),
  });

  const tree = new RunTreeProvider(monitor);
  const treeView = vscode.window.createTreeView("autofounder.runs", {
    treeDataProvider: tree,
    showCollapseAll: true,
  });

  const gates = new GateService(api, monitor);
  const codegen = new CodeGenService(api);
  const artifacts = new ArtifactService({
    api,
    monitor,
    state: context.globalState,
    getBaseUrl: () => readConfig().apiBaseUrl,
    getToken: () => auth.getAccessToken(),
  });

  const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBar.command = "autofounder.refreshRuns";

  const createStream: StreamFactory = (runId) =>
    new RunStream({
      runId,
      wsBase: toWebSocketBase(readConfig().apiBaseUrl),
      api,
      getToken: () => auth.getAccessToken(),
      pollIntervalMs: readConfig().pollIntervalMs,
    });

  const updateStatusBar = (): void => {
    const runs = monitor.getRuns();
    const total = runs.reduce((sum, r) => sum + (r.costUsd || 0), 0);
    statusBar.text = `$(rocket) AutoFounder ${formatCost(total)}`;
    statusBar.tooltip = `${runs.length} run(s) · total cost ${formatCost(total)}`;
    statusBar.show();
  };

  const syncAuthState = async (): Promise<void> => {
    const authed = await auth.isAuthenticated();
    await vscode.commands.executeCommand("setContext", "autofounder.authenticated", authed);
    if (authed) {
      monitor.start();
    } else {
      await monitor.refresh();
    }
    updateStatusBar();
  };

  context.subscriptions.push(
    auth,
    monitor,
    treeView,
    statusBar,
    monitor.onDidChangeRuns(() => {
      tree.refresh();
      updateStatusBar();
    }),
    monitor.onGateRequired((event) => void gates.showGateBanner(event)),
    auth.onDidChangeAuth(() => void syncAuthState()),
    vscode.window.registerUriHandler({ handleUri: (uri) => auth.handleUri(uri) }),
    onConfigChange(() => monitor.restart()),

    register("autofounder.signIn", async () => {
      if (await auth.signIn()) await syncAuthState();
    }),
    register("autofounder.signInWithToken", async () => {
      if (await auth.signInWithToken()) await syncAuthState();
    }),
    register("autofounder.signOut", async () => {
      await auth.signOut();
      await syncAuthState();
    }),
    register("autofounder.refreshRuns", () => monitor.refresh()),
    register("autofounder.submitIdea", () => submitIdea(api, monitor, auth)),
    register("autofounder.openStream", async (arg: unknown) => {
      const runId = coerceRunId(arg) ?? (await pickRun(monitor));
      if (!runId) return;
      await context.globalState.update(LAST_RUN_KEY, runId);
      StreamPanel.show(runId, createStream);
    }),
    register("autofounder.decideGate", (arg: unknown) => gates.decideGateCommand(arg)),
    register("autofounder.cancelRun", (arg: unknown) => cancelRun(arg, api, monitor)),
    register("autofounder.generateComponent", () => codegen.generateComponent()),
    register("autofounder.generateApiEndpoint", () => codegen.generateApiEndpoint()),
    register("autofounder.openLeanCanvas", () => artifacts.openLeanCanvas()),
    register("autofounder.openErd", () => artifacts.openErd()),
    register("autofounder.openOpenApiSpec", () => artifacts.openOpenApiSpec()),
    register("autofounder.openArtifact", () => artifacts.openAny()),
  );

  await syncAuthState();
}

export function deactivate(): void {
  StreamPanel.disposeAll();
}

// ── helpers ──────────────────────────────────────────────────────────────────

function register(command: string, handler: (...args: unknown[]) => unknown): vscode.Disposable {
  return vscode.commands.registerCommand(command, handler);
}

/** Accept a runId from a string arg, a tree node, or a `{runId}` payload. */
function coerceRunId(arg: unknown): string | undefined {
  if (typeof arg === "string") return arg;
  if (arg && typeof arg === "object") {
    const rec = arg as Record<string, unknown>;
    if (typeof rec.runId === "string") return rec.runId;
    if (typeof rec.id === "string" && rec.kind === "run") return rec.id;
    const run = rec.run as Record<string, unknown> | undefined;
    if (run && typeof run.id === "string") return run.id;
  }
  return undefined;
}

async function pickRun(monitor: RunMonitor): Promise<string | undefined> {
  const runs = monitor.getRuns();
  if (runs.length === 0) {
    vscode.window.showInformationMessage("AutoFounder AI: no runs available.");
    return undefined;
  }
  if (runs.length === 1) return runs[0].id;
  const pick = await vscode.window.showQuickPick(
    runs.map((r: RunSummary) => ({ label: r.title ?? r.id, description: r.status, id: r.id })),
    { title: "Select a run", placeHolder: "Pick a run" },
  );
  return pick?.id;
}

async function submitIdea(api: ApiClient, monitor: RunMonitor, auth: AuthManager): Promise<void> {
  const text = await vscode.window.showInputBox({
    title: "AutoFounder: Submit New Idea",
    prompt: "Describe the software business you want to build.",
    placeHolder: "e.g. A booking platform for independent yoga instructors",
    ignoreFocusOut: true,
    validateInput: (v) =>
      v.trim().length >= 8 ? undefined : "Add a little more detail (min 8 chars).",
  });
  if (!text) return;
  try {
    const run = await api.submitIdea(text.trim());
    vscode.window.showInformationMessage(`AutoFounder AI: run ${shortId(run.id)} created.`);
    await monitor.refresh();
  } catch (err) {
    await reportApiError(err, auth);
  }
}

async function cancelRun(arg: unknown, api: ApiClient, monitor: RunMonitor): Promise<void> {
  const runId = coerceRunId(arg) ?? (await pickRun(monitor));
  if (!runId) return;
  const confirm = await vscode.window.showWarningMessage(
    `Cancel run ${shortId(runId)}? This stops all in-flight agents.`,
    { modal: true },
    "Cancel Run",
  );
  if (confirm !== "Cancel Run") return;
  try {
    await api.cancelRun(runId);
    vscode.window.showInformationMessage(`AutoFounder AI: run ${shortId(runId)} cancelled.`);
    await monitor.refresh();
  } catch (err) {
    vscode.window.showErrorMessage(
      `AutoFounder AI: failed to cancel run — ${err instanceof Error ? err.message : String(err)}`,
    );
  }
}

async function reportApiError(err: unknown, auth: AuthManager): Promise<void> {
  if (err instanceof ApiError && err.isAuth) {
    const choice = await vscode.window.showWarningMessage(
      "AutoFounder AI: your session has expired. Sign in again.",
      "Sign In",
    );
    if (choice === "Sign In") await auth.signIn();
    return;
  }
  vscode.window.showErrorMessage(
    `AutoFounder AI: ${err instanceof Error ? err.message : String(err)}`,
  );
}

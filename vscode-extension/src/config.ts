/** Typed access to the `autofounder.*` workspace settings. */

import * as vscode from "vscode";

export interface ExtensionConfig {
  apiBaseUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
  authProvider: string;
  pollIntervalMs: number;
}

export function readConfig(): ExtensionConfig {
  const cfg = vscode.workspace.getConfiguration("autofounder");
  return {
    apiBaseUrl: cfg.get<string>("apiBaseUrl", "http://localhost:8000"),
    supabaseUrl: cfg.get<string>("supabaseUrl", "").trim(),
    supabaseAnonKey: cfg.get<string>("supabaseAnonKey", "").trim(),
    authProvider: cfg.get<string>("authProvider", "github"),
    pollIntervalMs: Math.max(3, cfg.get<number>("pollIntervalSeconds", 8)) * 1000,
  };
}

/** Fires whenever any `autofounder.*` setting changes. */
export function onConfigChange(listener: () => void): vscode.Disposable {
  return vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration("autofounder")) listener();
  });
}

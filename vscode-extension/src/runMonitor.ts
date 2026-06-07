/**
 * Polls the run list on an interval, caches the result for the sidebar (AF-073),
 * and raises `onGateRequired` the first time a run enters a pending-gate state
 * (AF-074). This is the realtime-independent path: it keeps the sidebar and gate
 * banners working even while AF-031 Supabase Realtime is unavailable.
 */

import * as vscode from "vscode";
import { ApiError } from "./http";
import { type ApiClient } from "./apiClient";
import { type Gate, type RunSummary } from "./types";

export interface GateRequiredEvent {
  run: RunSummary;
  gate: Gate;
}

export class RunMonitor implements vscode.Disposable {
  private readonly getApi: () => ApiClient;
  private readonly getIntervalMs: () => number;
  private readonly isAuthenticated: () => Promise<boolean>;

  private runs: RunSummary[] = [];
  private timer: ReturnType<typeof setInterval> | undefined;
  private readonly notifiedGates = new Set<string>();
  private refreshing = false;

  private readonly runsEmitter = new vscode.EventEmitter<void>();
  private readonly gateEmitter = new vscode.EventEmitter<GateRequiredEvent>();
  readonly onDidChangeRuns: vscode.Event<void> = this.runsEmitter.event;
  readonly onGateRequired: vscode.Event<GateRequiredEvent> = this.gateEmitter.event;

  constructor(deps: {
    getApi: () => ApiClient;
    getIntervalMs: () => number;
    isAuthenticated: () => Promise<boolean>;
  }) {
    this.getApi = deps.getApi;
    this.getIntervalMs = deps.getIntervalMs;
    this.isAuthenticated = deps.isAuthenticated;
  }

  start(): void {
    this.stopTimer();
    void this.refresh();
    this.timer = setInterval(() => void this.refresh(), this.getIntervalMs());
  }

  /** Restart the interval (e.g. after the poll-interval setting changed). */
  restart(): void {
    this.start();
  }

  getRuns(): readonly RunSummary[] {
    return this.runs;
  }

  async refresh(): Promise<void> {
    if (this.refreshing) return;
    this.refreshing = true;
    try {
      if (!(await this.isAuthenticated())) {
        if (this.runs.length > 0) {
          this.runs = [];
          this.runsEmitter.fire();
        }
        return;
      }

      const runs = await this.getApi().listRuns();
      this.runs = runs;
      this.runsEmitter.fire();
      this.detectGates(runs);
    } catch (err) {
      if (err instanceof ApiError && err.isAuth) {
        this.runs = [];
        this.runsEmitter.fire();
      }
      // Transient errors keep the last good cache; the next tick retries.
    } finally {
      this.refreshing = false;
    }
  }

  private detectGates(runs: readonly RunSummary[]): void {
    for (const run of runs) {
      const gate = run.activeGate;
      if (gate && gate.state === "pending" && !this.notifiedGates.has(gate.id)) {
        this.notifiedGates.add(gate.id);
        this.gateEmitter.fire({ run, gate });
      }
    }
  }

  private stopTimer(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
  }

  dispose(): void {
    this.stopTimer();
    this.runsEmitter.dispose();
    this.gateEmitter.dispose();
  }
}

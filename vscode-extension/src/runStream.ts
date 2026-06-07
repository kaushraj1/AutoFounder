/**
 * AF-076 transport — a live event stream for a single run.
 *
 * Primary transport is the documented WebSocket upgrade `GET /v1/runs/{id}/stream`
 * (api-design.md §WebSocket), authenticated with the bearer token and resumed with
 * `Last-Event-ID` on reconnect. If the socket cannot be established after a few
 * attempts it falls back to REST polling of `GET /v1/runs/{id}` — the plan's
 * "AF-031 Realtime not ready -> poll on interval" fallback — synthesising events
 * from observed state changes so the UI keeps updating either way.
 */

import * as vscode from "vscode";
import WebSocket from "ws";
import { type ApiClient } from "./apiClient";
import { parseStreamFrame } from "./streamEvents";
import { type RunSummary, type StreamEvent } from "./types";

export type StreamStatus = "connecting" | "live" | "polling" | "closed";

const MAX_WS_ATTEMPTS = 3;
const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 15_000;

export interface RunStreamOptions {
  runId: string;
  /** ws(s)://host/v1 origin (from `toWebSocketBase`). */
  wsBase: string;
  api: ApiClient;
  getToken: () => Promise<string | undefined>;
  pollIntervalMs: number;
}

export class RunStream implements vscode.Disposable {
  private readonly opts: RunStreamOptions;
  private socket: WebSocket | undefined;
  private pollTimer: ReturnType<typeof setInterval> | undefined;
  private reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  private attempts = 0;
  private lastEventId: string | undefined;
  private lastStatus: string | undefined;
  private gateNotified = new Set<string>();
  private closed = false;
  /** Set once a terminal run.completed/run.failed event is seen — stops transport. */
  private finished = false;

  private readonly eventEmitter = new vscode.EventEmitter<StreamEvent>();
  private readonly statusEmitter = new vscode.EventEmitter<StreamStatus>();
  readonly onEvent: vscode.Event<StreamEvent> = this.eventEmitter.event;
  readonly onStatus: vscode.Event<StreamStatus> = this.statusEmitter.event;

  constructor(opts: RunStreamOptions) {
    this.opts = opts;
  }

  start(): void {
    if (this.closed || this.finished) return;
    void this.connect();
  }

  dispose(): void {
    this.closed = true;
    this.teardownSocket();
    if (this.pollTimer) clearInterval(this.pollTimer);
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.statusEmitter.fire("closed");
    this.eventEmitter.dispose();
    this.statusEmitter.dispose();
  }

  // ── WebSocket ────────────────────────────────────────────────────────────

  private async connect(): Promise<void> {
    if (this.closed || this.finished) return;
    this.statusEmitter.fire("connecting");

    let token: string | undefined;
    try {
      token = await this.opts.getToken();
    } catch {
      token = undefined;
    }
    if (this.closed) return;

    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (this.lastEventId) headers["Last-Event-ID"] = this.lastEventId;

    const url = `${this.opts.wsBase}/runs/${encodeURIComponent(this.opts.runId)}/stream`;
    let socket: WebSocket;
    try {
      socket = new WebSocket(url, { headers });
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.socket = socket;

    socket.on("open", () => {
      this.attempts = 0;
      this.statusEmitter.fire("live");
    });
    socket.on("message", (data: WebSocket.RawData) => this.handleMessage(data.toString()));
    socket.on("error", () => {
      /* surfaced via the subsequent close event */
    });
    socket.on("close", () => {
      if (this.socket === socket) this.socket = undefined;
      this.scheduleReconnect();
    });
  }

  private handleMessage(raw: string): void {
    const event = parseStreamFrame(raw);
    if (!event) return;
    if (event.stepId) this.lastEventId = event.stepId;
    this.emit(event);
  }

  private teardownSocket(): void {
    const socket = this.socket;
    this.socket = undefined;
    if (!socket) return;
    socket.removeAllListeners();
    try {
      socket.close();
    } catch {
      /* already closed */
    }
  }

  private scheduleReconnect(): void {
    if (this.closed || this.finished || this.pollTimer) return;
    this.teardownSocket();
    this.attempts += 1;
    if (this.attempts > MAX_WS_ATTEMPTS) {
      this.startPolling();
      return;
    }
    const delay = Math.min(RECONNECT_BASE_MS * 2 ** (this.attempts - 1), RECONNECT_MAX_MS);
    this.reconnectTimer = setTimeout(() => void this.connect(), delay);
  }

  // ── Polling fallback ──────────────────────────────────────────────────────

  private startPolling(): void {
    if (this.closed || this.finished || this.pollTimer) return;
    this.statusEmitter.fire("polling");
    void this.pollOnce();
    this.pollTimer = setInterval(() => void this.pollOnce(), this.opts.pollIntervalMs);
  }

  private async pollOnce(): Promise<void> {
    if (this.closed || this.finished) return;
    let run: RunSummary;
    try {
      run = await this.opts.api.getRun(this.opts.runId);
    } catch {
      return;
    }
    if (this.closed || this.finished) return;

    if (run.activeGate && run.activeGate.state === "pending") {
      const gate = run.activeGate;
      if (!this.gateNotified.has(gate.id)) {
        this.gateNotified.add(gate.id);
        this.emit({
          type: "gate.required",
          runId: run.id,
          gateId: gate.id,
          gateKind: gate.kind,
          payload: gate.payload,
          raw: {},
        });
      }
    }

    if (run.status !== this.lastStatus) {
      this.lastStatus = run.status;
      if (run.status === "completed") {
        this.emit({ type: "run.completed", runId: run.id, costUsd: run.costUsd, raw: {} });
      } else if (run.status === "failed") {
        this.emit({ type: "run.failed", runId: run.id, error: "Run failed", raw: {} });
      } else {
        this.emit({
          type: "unknown",
          runId: run.id,
          pillar: run.pillar,
          content: `Status: ${run.status}`,
          raw: {},
        });
      }
    }
  }

  private emit(event: StreamEvent): void {
    if (this.closed) return;
    this.eventEmitter.fire(event);
    if (event.type === "run.completed" || event.type === "run.failed") {
      this.finish();
    }
  }

  /** Stop transport on a terminal run state; keep emitters alive until dispose(). */
  private finish(): void {
    if (this.finished) return;
    this.finished = true;
    this.teardownSocket();
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = undefined;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }
  }
}

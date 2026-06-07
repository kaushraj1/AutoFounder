/**
 * AF-076 — Live token-streaming panel.
 *
 * A `WebviewPanel` that follows one run's live step/token stream (via {@link RunStream}).
 * One panel per run (re-revealed if reopened). The webview is locked down with a
 * strict CSP + per-load nonce; the extension host pushes parsed events to it over
 * `postMessage` (no remote content, no inline event handlers).
 */

import * as vscode from "vscode";
import { randomUrlSafe } from "./pkce";
import { type RunStream, type StreamStatus } from "./runStream";
import { shortId } from "./format";
import { type StreamEvent } from "./types";

export type StreamFactory = (runId: string) => RunStream;

export class StreamPanel {
  private static readonly panels = new Map<string, StreamPanel>();

  static show(runId: string, createStream: StreamFactory): void {
    const existing = StreamPanel.panels.get(runId);
    if (existing) {
      existing.panel.reveal(vscode.ViewColumn.Active);
      return;
    }
    StreamPanel.panels.set(runId, new StreamPanel(runId, createStream));
  }

  static disposeAll(): void {
    for (const panel of [...StreamPanel.panels.values()]) panel.dispose();
  }

  private readonly panel: vscode.WebviewPanel;
  private readonly stream: RunStream;
  private readonly disposables: vscode.Disposable[] = [];

  private constructor(
    private readonly runId: string,
    createStream: StreamFactory,
  ) {
    this.panel = vscode.window.createWebviewPanel(
      "autofounder.stream",
      `Run ${shortId(runId)}`,
      vscode.ViewColumn.Active,
      { enableScripts: true, retainContextWhenHidden: true },
    );
    this.panel.iconPath = new vscode.ThemeIcon("pulse");
    this.panel.webview.html = this.renderHtml(this.panel.webview);

    this.stream = createStream(runId);
    this.disposables.push(
      this.stream.onEvent((event) => this.post({ type: "event", event })),
      this.stream.onStatus((status) => this.post({ type: "status", status })),
      this.panel.onDidDispose(() => this.dispose()),
    );
    this.stream.start();
  }

  private post(
    message: { type: "event"; event: StreamEvent } | { type: "status"; status: StreamStatus },
  ): void {
    void this.panel.webview.postMessage(message);
  }

  dispose(): void {
    StreamPanel.panels.delete(this.runId);
    this.stream.dispose();
    for (const d of this.disposables) d.dispose();
    this.panel.dispose();
  }

  private renderHtml(webview: vscode.Webview): string {
    const nonce = randomUrlSafe(16);
    const csp = [
      "default-src 'none'",
      `style-src ${webview.cspSource} 'nonce-${nonce}'`,
      `script-src 'nonce-${nonce}'`,
    ].join("; ");

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="${csp}" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AutoFounder Run ${escapeHtml(shortId(this.runId))}</title>
  <style nonce="${nonce}">
    :root { color-scheme: light dark; }
    body { font-family: var(--vscode-editor-font-family, monospace); font-size: 13px;
      color: var(--vscode-foreground); background: var(--vscode-editor-background);
      margin: 0; padding: 0; }
    header { position: sticky; top: 0; padding: 8px 12px; display: flex; gap: 10px;
      align-items: center; background: var(--vscode-sideBar-background);
      border-bottom: 1px solid var(--vscode-panel-border); }
    .badge { padding: 1px 8px; border-radius: 10px; font-size: 11px;
      background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); }
    .badge.live { background: var(--vscode-testing-iconPassed, #2ea043); color: #fff; }
    .badge.polling { background: var(--vscode-charts-yellow, #cca700); color: #000; }
    .badge.closed, .badge.connecting { background: var(--vscode-charts-gray, #888); color: #fff; }
    #log { padding: 8px 12px; white-space: pre-wrap; word-break: break-word; }
    .step { margin: 6px 0; padding-left: 8px; border-left: 2px solid var(--vscode-panel-border); }
    .meta { color: var(--vscode-descriptionForeground); font-size: 11px; }
    .gate { color: var(--vscode-notificationsWarningIcon-foreground, #cca700); font-weight: 600; }
    .ok { color: var(--vscode-testing-iconPassed, #2ea043); font-weight: 600; }
    .err { color: var(--vscode-testing-iconFailed, #f14c4c); font-weight: 600; }
    .empty { color: var(--vscode-descriptionForeground); padding: 16px 12px; }
  </style>
</head>
<body>
  <header>
    <strong>Live run stream</strong>
    <span class="badge connecting" id="status">connecting</span>
    <span class="meta" id="run">${escapeHtml(this.runId)}</span>
  </header>
  <div id="log"><div class="empty">Waiting for events…</div></div>
  <script nonce="${nonce}">
    const log = document.getElementById('log');
    const statusEl = document.getElementById('status');
    let current = null;
    let cleared = false;

    function clearEmpty() {
      if (!cleared) { log.innerHTML = ''; cleared = true; }
    }
    function el(cls, text) {
      const d = document.createElement('div');
      if (cls) d.className = cls;
      if (text !== undefined) d.textContent = text;
      return d;
    }
    function atBottom() {
      return window.innerHeight + window.scrollY >= document.body.scrollHeight - 40;
    }
    function scroll() { window.scrollTo(0, document.body.scrollHeight); }

    function render(ev) {
      clearEmpty();
      const stick = atBottom();
      switch (ev.type) {
        case 'step.started': {
          current = el('step');
          const head = el('meta', '▶ ' + (ev.agentId || 'agent') + (ev.pillar ? ' · pillar ' + ev.pillar : ''));
          current.appendChild(head);
          current.appendChild(el('body-text', ''));
          log.appendChild(current);
          break;
        }
        case 'token': {
          if (!current) { current = el('step'); log.appendChild(current); }
          current.appendChild(document.createTextNode(ev.content || ''));
          break;
        }
        case 'tool.call':
          log.appendChild(el('meta', '🛠 tool: ' + (ev.toolName || 'unknown')));
          break;
        case 'step.completed':
          current = null;
          break;
        case 'gate.required':
          log.appendChild(el('gate', '⏸ Gate required: ' + (ev.gateKind || 'approval')));
          break;
        case 'run.completed':
          log.appendChild(el('ok', '✓ Run completed' + (ev.costUsd != null ? ' · $' + ev.costUsd.toFixed(2) : '')));
          break;
        case 'run.failed':
          log.appendChild(el('err', '✗ Run failed: ' + (ev.error || 'unknown error')));
          break;
        default:
          if (ev.content) log.appendChild(el('meta', ev.content));
      }
      if (stick) scroll();
    }

    window.addEventListener('message', (e) => {
      const msg = e.data;
      if (msg.type === 'status') {
        statusEl.textContent = msg.status;
        statusEl.className = 'badge ' + msg.status;
      } else if (msg.type === 'event') {
        render(msg.event);
      }
    });
  </script>
</body>
</html>`;
  }
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

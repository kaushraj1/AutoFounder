/**
 * AF-077 — Artifact quick-open.
 *
 * `AutoFounder: Open Lean Canvas / ERD / OpenAPI Spec` (and a generic picker)
 * resolve the target run, fetch its artifacts via `GET /v1/runs/{id}/artifacts`,
 * and preview the chosen artifact in an editor — Markdown (with preview) for the
 * canvas, a fenced `mermaid` block for the ERD, JSON/YAML for the OpenAPI spec.
 */

import * as vscode from "vscode";
import { type ApiClient } from "./apiClient";
import { isSameOrigin } from "./http";
import { type RunMonitor } from "./runMonitor";
import { runTreeLabel } from "./format";
import { type Artifact } from "./types";

const LAST_RUN_KEY = "autofounder.lastRunId";

type ArtifactKind = "lean_canvas" | "erd" | "openapi";

const KIND_MATCHERS: Record<ArtifactKind, RegExp> = {
  lean_canvas: /canvas|lean/i,
  erd: /erd|entity|schema.?diagram/i,
  openapi: /openapi|swagger|api.?spec/i,
};

export interface ArtifactServiceDeps {
  api: ApiClient;
  monitor: RunMonitor;
  state: vscode.Memento;
  getBaseUrl: () => string;
  getToken: () => Promise<string | undefined>;
}

export class ArtifactService {
  constructor(private readonly deps: ArtifactServiceDeps) {}

  openLeanCanvas = (): Promise<void> => this.open("lean_canvas");
  openErd = (): Promise<void> => this.open("erd");
  openOpenApiSpec = (): Promise<void> => this.open("openapi");
  openAny = (): Promise<void> => this.open(undefined);

  private async open(kind: ArtifactKind | undefined): Promise<void> {
    const runId = await this.resolveRunId();
    if (!runId) return;

    let artifacts: Artifact[];
    try {
      artifacts = await this.deps.api.listArtifacts(runId);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      vscode.window.showErrorMessage(`AutoFounder AI: failed to load artifacts — ${message}`);
      return;
    }

    if (artifacts.length === 0) {
      vscode.window.showInformationMessage("AutoFounder AI: this run has no artifacts yet.");
      return;
    }

    const artifact = kind ? this.matchKind(artifacts, kind) : await this.pickArtifact(artifacts);
    if (!artifact) {
      if (kind) {
        vscode.window.showInformationMessage(
          `AutoFounder AI: no ${kind.replace("_", " ")} artifact for this run yet.`,
        );
      }
      return;
    }

    await this.preview(artifact);
  }

  private matchKind(artifacts: Artifact[], kind: ArtifactKind): Artifact | undefined {
    const matcher = KIND_MATCHERS[kind];
    return artifacts.find((a) => matcher.test(a.kind) || (a.title ? matcher.test(a.title) : false));
  }

  private async pickArtifact(artifacts: Artifact[]): Promise<Artifact | undefined> {
    const pick = await vscode.window.showQuickPick(
      artifacts.map((a) => ({ label: a.title ?? a.kind, description: a.kind, artifact: a })),
      { title: "Open artifact", placeHolder: "Select an artifact to preview" },
    );
    return pick?.artifact;
  }

  private async resolveRunId(): Promise<string | undefined> {
    const runs = this.deps.monitor.getRuns();
    if (runs.length === 0) {
      vscode.window.showInformationMessage("AutoFounder AI: no runs available.");
      return undefined;
    }
    if (runs.length === 1) {
      await this.deps.state.update(LAST_RUN_KEY, runs[0].id);
      return runs[0].id;
    }

    const last = this.deps.state.get<string>(LAST_RUN_KEY);
    const items = runs.map((r) => ({
      label: runTreeLabel(r),
      description: `${r.status} · ${r.id === last ? "last viewed" : r.id}`,
      id: r.id,
    }));
    const pick = await vscode.window.showQuickPick(items, {
      title: "Select a run",
      placeHolder: "Which run's artifacts do you want to open?",
    });
    if (pick) await this.deps.state.update(LAST_RUN_KEY, pick.id);
    return pick?.id;
  }

  private async preview(artifact: Artifact): Promise<void> {
    const content = await this.loadContent(artifact);
    const kind = this.classify(artifact);

    if (kind === "erd") {
      const body = /```mermaid|erDiagram|classDiagram/.test(content)
        ? content
        : `# ${artifact.title ?? "ERD"}\n\n\`\`\`mermaid\n${content}\n\`\`\`\n`;
      await this.openMarkdown(body);
      return;
    }
    if (kind === "lean_canvas") {
      await this.openMarkdown(content.startsWith("#") ? content : `# Lean Canvas\n\n${content}`);
      return;
    }
    if (kind === "openapi") {
      const language = content.trim().startsWith("{") ? "json" : "yaml";
      await this.openDocument(content, language);
      return;
    }
    await this.openDocument(content, languageForMime(artifact.mimeType));
  }

  private classify(artifact: Artifact): ArtifactKind | "other" {
    for (const kind of Object.keys(KIND_MATCHERS) as ArtifactKind[]) {
      if (
        KIND_MATCHERS[kind].test(artifact.kind) ||
        (artifact.title && KIND_MATCHERS[kind].test(artifact.title))
      ) {
        return kind;
      }
    }
    return "other";
  }

  private async loadContent(artifact: Artifact): Promise<string> {
    if (artifact.content && artifact.content.length > 0) return artifact.content;
    const uri = artifact.uri;
    if (!uri) return JSON.stringify(artifact, null, 2);

    const isAbsolute = /^https?:\/\//i.test(uri);
    const baseUrl = this.deps.getBaseUrl().replace(/\/+$/, "");
    const target = isAbsolute ? uri : `${baseUrl}${uri.startsWith("/") ? "" : "/"}${uri}`;

    // Attach the bearer token ONLY to a genuinely same-origin target. A string
    // prefix match would leak the JWT to a backend-supplied look-alike host
    // (e.g. https://api.example.com.attacker.com), so compare parsed origins.
    const sameOrigin = isSameOrigin(target, baseUrl);

    try {
      const headers: Record<string, string> = {};
      if (sameOrigin) {
        const token = await this.deps.getToken();
        if (token) headers.Authorization = `Bearer ${token}`;
      }
      const res = await fetch(target, { headers });
      if (!res.ok) return `Could not load artifact (HTTP ${res.status}).\nSource: ${target}`;
      return await res.text();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return `Could not load artifact: ${message}\nSource: ${target}`;
    }
  }

  private async openMarkdown(content: string): Promise<void> {
    const doc = await vscode.workspace.openTextDocument({ language: "markdown", content });
    await vscode.window.showTextDocument(doc, { preview: false });
    await vscode.commands.executeCommand("markdown.showPreviewToSide", doc.uri);
  }

  private async openDocument(content: string, language: string): Promise<void> {
    const doc = await vscode.workspace.openTextDocument({ language, content });
    await vscode.window.showTextDocument(doc, { preview: false });
  }
}

function languageForMime(mime: string | undefined): string {
  if (!mime) return "plaintext";
  if (mime.includes("json")) return "json";
  if (mime.includes("yaml")) return "yaml";
  if (mime.includes("markdown")) return "markdown";
  if (mime.includes("html")) return "html";
  return "plaintext";
}

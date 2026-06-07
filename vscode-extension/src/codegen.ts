/**
 * AF-075 — Code-generation commands.
 *
 * `AutoFounder: Generate Component` and `Generate API Endpoint` prompt for a spec,
 * open a fresh editor tab, and stream the Coder Agent's (AF-041) tokens into it.
 * Until AF-041 is wired, `ApiClient.streamCodeGen` yields a labelled placeholder,
 * so the command is fully usable today and unchanged once the backend lands.
 */

import * as vscode from "vscode";
import { type ApiClient } from "./apiClient";
import { type CodeGenRequest } from "./types";

export class CodeGenService {
  constructor(private readonly api: ApiClient) {}

  async generateComponent(): Promise<void> {
    await this.generate("component");
  }

  async generateApiEndpoint(): Promise<void> {
    await this.generate("api_endpoint");
  }

  private async generate(kind: CodeGenRequest["kind"]): Promise<void> {
    const noun = kind === "component" ? "component" : "API endpoint";
    const spec = await vscode.window.showInputBox({
      title: `AutoFounder: Generate ${noun === "component" ? "Component" : "API Endpoint"}`,
      prompt: `Describe the ${noun} to generate.`,
      placeHolder:
        kind === "component"
          ? "e.g. A pricing table with three tiers and a monthly/annual toggle"
          : "e.g. POST /v1/subscriptions that creates a Stripe subscription",
      ignoreFocusOut: true,
      validateInput: (v) =>
        v.trim().length >= 3 ? undefined : "Please describe what to generate.",
    });
    if (!spec) return;

    const language = kind === "component" ? "typescriptreact" : "python";
    const doc = await vscode.workspace.openTextDocument({ language, content: "" });
    const editor = await vscode.window.showTextDocument(doc, { preview: false });

    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `AutoFounder: generating ${noun}…`,
        cancellable: true,
      },
      async (_progress, cancel) => {
        try {
          for await (const token of this.api.streamCodeGen({ kind, spec: spec.trim() })) {
            if (cancel.isCancellationRequested) break;
            await appendToEditor(editor, token);
          }
        } catch (err) {
          const message = err instanceof Error ? err.message : String(err);
          vscode.window.showErrorMessage(`AutoFounder AI: code generation failed — ${message}`);
        }
      },
    );
  }
}

async function appendToEditor(editor: vscode.TextEditor, text: string): Promise<void> {
  const doc = editor.document;
  const end = doc.lineAt(doc.lineCount - 1).range.end;
  await editor.edit((builder) => builder.insert(end, text), {
    undoStopBefore: false,
    undoStopAfter: false,
  });
}

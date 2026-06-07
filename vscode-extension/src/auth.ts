/**
 * AF-072 — Authentication.
 *
 * Implements the Supabase Auth PKCE flow and persists the resulting session in
 * VS Code SecretStorage (never settings, never logs — Decision D1). A dev-token
 * fallback (`signInWithToken`) lets you paste a JWT when the hosted Supabase
 * project isn't configured yet, matching the plan's fallback matrix.
 *
 * The PKCE verifier lives only in memory between launching the browser and the
 * redirect callback; only the exchanged JWT (+ refresh token) is stored.
 */

import * as vscode from "vscode";
import { type AuthTokenProvider } from "./apiClient";
import { type ExtensionConfig } from "./config";
import { createPkcePair, createState } from "./pkce";

const SECRET_KEY = "autofounder.session";
const PUBLISHER_ID = "euron-autofounder.autofounder-ai";

interface StoredSession {
  accessToken: string;
  refreshToken?: string;
  /** Epoch seconds. */
  expiresAt?: number;
  mode: "pkce" | "token";
}

interface PendingLogin {
  state: string;
  verifier: string;
  resolve: (code: string) => void;
  reject: (err: Error) => void;
}

export class AuthManager implements AuthTokenProvider {
  private readonly secrets: vscode.SecretStorage;
  private getConfig: () => ExtensionConfig;
  private session: StoredSession | undefined;
  private loaded = false;
  private pending: PendingLogin | undefined;
  /** In-flight refresh, shared by concurrent callers (single-flight). */
  private refreshing: Promise<void> | undefined;

  private readonly changeEmitter = new vscode.EventEmitter<boolean>();
  /** Fires `true` when signed in, `false` when signed out. */
  readonly onDidChangeAuth: vscode.Event<boolean> = this.changeEmitter.event;

  constructor(secrets: vscode.SecretStorage, getConfig: () => ExtensionConfig) {
    this.secrets = secrets;
    this.getConfig = getConfig;
  }

  /** Handles the `vscode://…/auth-callback?code&state` redirect. */
  handleUri(uri: vscode.Uri): void {
    const params = new URLSearchParams(uri.query);
    const code = params.get("code");
    const state = params.get("state");
    const errorDescription = params.get("error_description") ?? params.get("error");
    if (!this.pending) return;

    if (errorDescription) {
      this.pending.reject(new Error(errorDescription));
      return;
    }
    if (!code || state !== this.pending.state) {
      this.pending.reject(new Error("Sign-in callback was missing a valid authorization code."));
      return;
    }
    this.pending.resolve(code);
  }

  async isAuthenticated(): Promise<boolean> {
    await this.ensureLoaded();
    return this.session !== undefined;
  }

  /** {@link AuthTokenProvider} — a valid bearer token, refreshing if needed. */
  async getAccessToken(): Promise<string | undefined> {
    await this.ensureLoaded();
    if (!this.session) return undefined;

    const { expiresAt, refreshToken, mode } = this.session;
    const needsRefresh = expiresAt !== undefined && Date.now() / 1000 > expiresAt - 60;
    if (needsRefresh && mode === "pkce" && refreshToken) {
      try {
        // Single-flight: concurrent callers near expiry share one refresh so the
        // single-use rotating refresh token is only spent once.
        if (!this.refreshing) {
          this.refreshing = this.refresh(refreshToken).finally(() => {
            this.refreshing = undefined;
          });
        }
        await this.refreshing;
      } catch (err) {
        log("Token refresh failed", err);
        // Fall through and return the (possibly stale) token; the API call will
        // surface a 401 and the user will be prompted to sign in again.
      }
    }
    return this.session?.accessToken;
  }

  /** AF-072 — launch the Supabase PKCE sign-in flow in the system browser. */
  async signIn(): Promise<boolean> {
    const cfg = this.getConfig();
    if (!cfg.supabaseUrl || !cfg.supabaseAnonKey) {
      const pick = await vscode.window.showWarningMessage(
        "Supabase project not configured. Set 'autofounder.supabaseUrl' and 'autofounder.supabaseAnonKey', or sign in with a token for local dev.",
        "Open Settings",
        "Sign In with Token",
      );
      if (pick === "Open Settings") {
        await vscode.commands.executeCommand(
          "workbench.action.openSettings",
          "autofounder.supabaseUrl",
        );
      } else if (pick === "Sign In with Token") {
        return this.signInWithToken();
      }
      return false;
    }

    const pkce = createPkcePair();
    const state = createState();
    const redirectUri = await this.callbackUri();

    const authorizeUrl = new URL(`${trimSlash(cfg.supabaseUrl)}/auth/v1/authorize`);
    authorizeUrl.searchParams.set("provider", cfg.authProvider);
    authorizeUrl.searchParams.set("redirect_to", redirectUri.toString(true));
    authorizeUrl.searchParams.set("code_challenge", pkce.challenge);
    authorizeUrl.searchParams.set("code_challenge_method", "s256");
    authorizeUrl.searchParams.set("state", state);

    return vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "AutoFounder AI: signing in…",
        cancellable: true,
      },
      async (_progress, cancel) => {
        let timer: ReturnType<typeof setTimeout> | undefined;
        const codePromise = new Promise<string>((resolve, reject) => {
          this.pending = { state, verifier: pkce.verifier, resolve, reject };
          timer = setTimeout(
            () => reject(new Error("Sign-in timed out after 5 minutes.")),
            5 * 60_000,
          );
          cancel.onCancellationRequested(() => reject(new Error("Sign-in cancelled.")));
        });

        try {
          await vscode.env.openExternal(vscode.Uri.parse(authorizeUrl.toString()));
          const code = await codePromise;
          await this.exchangeCode(code, pkce.verifier);
          await this.persist();
          vscode.window.showInformationMessage("AutoFounder AI: signed in.");
          return true;
        } catch (err) {
          if (!cancel.isCancellationRequested) {
            vscode.window.showErrorMessage(
              `AutoFounder AI sign-in failed: ${err instanceof Error ? err.message : String(err)}`,
            );
          }
          return false;
        } finally {
          if (timer) clearTimeout(timer);
          this.pending = undefined;
        }
      },
    );
  }

  /** Dev fallback — store a pasted Supabase JWT directly in SecretStorage. */
  async signInWithToken(): Promise<boolean> {
    const token = await vscode.window.showInputBox({
      title: "AutoFounder AI: Sign In with Token",
      prompt: "Paste a Supabase access token (JWT). Stored in SecretStorage, never in settings.",
      password: true,
      ignoreFocusOut: true,
      validateInput: (value) =>
        value.trim().split(".").length === 3
          ? undefined
          : "Expected a JWT (three dot-separated segments).",
    });
    if (!token) return false;

    this.session = {
      accessToken: token.trim(),
      expiresAt: decodeJwtExp(token.trim()),
      mode: "token",
    };
    await this.persist();
    vscode.window.showInformationMessage("AutoFounder AI: signed in with token.");
    return true;
  }

  async signOut(): Promise<void> {
    this.session = undefined;
    this.loaded = true;
    await this.secrets.delete(SECRET_KEY);
    this.changeEmitter.fire(false);
  }

  dispose(): void {
    this.changeEmitter.dispose();
    this.pending?.reject(new Error("Extension deactivated"));
  }

  // ── internals ──────────────────────────────────────────────────────────────

  private async callbackUri(): Promise<vscode.Uri> {
    const base = vscode.Uri.parse(`${vscode.env.uriScheme}://${PUBLISHER_ID}/auth-callback`);
    return vscode.env.asExternalUri(base);
  }

  private async exchangeCode(authCode: string, verifier: string): Promise<void> {
    const cfg = this.getConfig();
    const res = await fetch(`${trimSlash(cfg.supabaseUrl)}/auth/v1/token?grant_type=pkce`, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: cfg.supabaseAnonKey },
      body: JSON.stringify({ auth_code: authCode, code_verifier: verifier }),
    });
    this.session = await this.sessionFromTokenResponse(res, "pkce");
  }

  private async refresh(refreshToken: string): Promise<void> {
    const cfg = this.getConfig();
    const res = await fetch(
      `${trimSlash(cfg.supabaseUrl)}/auth/v1/token?grant_type=refresh_token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json", apikey: cfg.supabaseAnonKey },
        body: JSON.stringify({ refresh_token: refreshToken }),
      },
    );
    this.session = await this.sessionFromTokenResponse(res, "pkce");
    await this.persist();
  }

  private async sessionFromTokenResponse(
    res: Response,
    mode: "pkce" | "token",
  ): Promise<StoredSession> {
    if (!res.ok) {
      throw new Error(`Supabase token endpoint returned ${res.status}.`);
    }
    const body = (await res.json()) as {
      access_token?: string;
      refresh_token?: string;
      expires_at?: number;
      expires_in?: number;
    };
    if (!body.access_token) {
      throw new Error("Supabase token response did not include an access token.");
    }
    const expiresAt =
      body.expires_at ??
      (body.expires_in ? Math.floor(Date.now() / 1000) + body.expires_in : undefined);
    return {
      accessToken: body.access_token,
      refreshToken: body.refresh_token,
      expiresAt,
      mode,
    };
  }

  private async ensureLoaded(): Promise<void> {
    if (this.loaded) return;
    const stored = await this.secrets.get(SECRET_KEY);
    if (stored) {
      try {
        this.session = JSON.parse(stored) as StoredSession;
      } catch {
        await this.secrets.delete(SECRET_KEY);
      }
    }
    this.loaded = true;
  }

  private async persist(): Promise<void> {
    this.loaded = true;
    if (this.session) {
      await this.secrets.store(SECRET_KEY, JSON.stringify(this.session));
      this.changeEmitter.fire(true);
    }
  }
}

function trimSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

/** Best-effort exp (epoch seconds) from a JWT payload, for display/refresh hints. */
function decodeJwtExp(jwt: string): number | undefined {
  const parts = jwt.split(".");
  if (parts.length !== 3) return undefined;
  try {
    const payload = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8")) as {
      exp?: number;
    };
    return typeof payload.exp === "number" ? payload.exp : undefined;
  } catch {
    return undefined;
  }
}

function log(message: string, err: unknown): void {
  // Never log token material — only the failure reason.
  const reason = err instanceof Error ? err.message : "unknown error";
  console.error(`[autofounder.auth] ${message}: ${reason}`);
}

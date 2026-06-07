/**
 * PKCE (RFC 7636) helpers for the Supabase Auth sign-in flow.
 *
 * Pure crypto only (no `vscode`), so the verifier/challenge derivation is unit
 * testable. The verifier is held in memory by `AuthManager` between launching the
 * browser and the redirect callback; only the resulting JWT is persisted (to
 * SecretStorage), never the verifier.
 */

import { createHash, randomBytes } from "node:crypto";

/** RFC 4648 §5 base64url encoding with no padding. */
export function base64UrlEncode(buffer: Buffer): string {
  return buffer.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** A high-entropy URL-safe random string (default 32 bytes -> 43 chars). */
export function randomUrlSafe(bytes = 32): string {
  return base64UrlEncode(randomBytes(bytes));
}

export interface PkcePair {
  /** Secret, sent only on the token exchange. 43–128 chars per RFC 7636. */
  verifier: string;
  /** Public, sent on the authorize redirect. */
  challenge: string;
  method: "S256";
}

export function createPkcePair(): PkcePair {
  const verifier = randomUrlSafe(48);
  const challenge = base64UrlEncode(createHash("sha256").update(verifier).digest());
  return { verifier, challenge, method: "S256" };
}

/** Opaque CSRF/state token correlating the authorize redirect with its callback. */
export function createState(): string {
  return randomUrlSafe(16);
}

/**
 * Response-envelope handling for the AutoFounder AI REST contract.
 *
 * Success:  { "data": ... , "meta": { request_id, timestamp } }
 * Error:    { "error": { code, message, details }, "meta": {...} }
 *
 * The backend is mid-migration, so `unwrapData` also accepts a bare resource/array
 * (no envelope) and returns it as-is.
 */

import { asRecord } from "./normalize";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** True when the caller should re-authenticate. */
  get isAuth(): boolean {
    return this.status === 401 || this.code === "AF_ERR_UNAUTHORIZED";
  }
}

/** Unwrap the `data` field from a success envelope, tolerating bare payloads. */
export function unwrapData(body: unknown): unknown {
  if (body !== null && typeof body === "object" && "data" in (body as object)) {
    return (body as { data: unknown }).data;
  }
  return body;
}

/** Build an {@link ApiError} from a failed HTTP response body. */
export function parseApiError(status: number, body: unknown): ApiError {
  const rec = asRecord(body);
  const err = asRecord(rec.error);
  const message =
    typeof err.message === "string" && err.message.length > 0
      ? err.message
      : `Request failed with status ${status}`;
  const code = typeof err.code === "string" && err.code.length > 0 ? err.code : defaultCode(status);
  const details =
    err.details !== null && typeof err.details === "object"
      ? (err.details as Record<string, unknown>)
      : undefined;
  return new ApiError(message, status, code, details);
}

function defaultCode(status: number): string {
  switch (status) {
    case 400:
      return "AF_ERR_VALIDATION";
    case 401:
      return "AF_ERR_UNAUTHORIZED";
    case 403:
      return "AF_ERR_FORBIDDEN";
    case 404:
      return "AF_ERR_NOT_FOUND";
    case 409:
      return "AF_ERR_CONFLICT";
    case 422:
      return "AF_ERR_UNPROCESSABLE";
    case 429:
      return "AF_ERR_RATE_LIMITED";
    case 503:
      return "AF_ERR_UNAVAILABLE";
    default:
      return "AF_ERR_INTERNAL";
  }
}

/** Normalize a configured base URL: trim, strip trailing slash + a trailing `/v1`. */
export function normalizeBaseUrl(raw: string): string {
  let url = raw.trim().replace(/\/+$/, "");
  url = url.replace(/\/v1$/, "");
  return url;
}

/** Derive the `ws(s)://…/v1` origin for the live run stream from an http base URL. */
export function toWebSocketBase(baseUrl: string): string {
  const normalized = normalizeBaseUrl(baseUrl);
  if (normalized.startsWith("https://")) return `wss://${normalized.slice("https://".length)}/v1`;
  if (normalized.startsWith("http://")) return `ws://${normalized.slice("http://".length)}/v1`;
  return `${normalized}/v1`;
}

/**
 * True only when both URLs parse to the exact same origin (scheme + host + port).
 * Used to decide whether to attach the bearer token to a backend-supplied artifact
 * URL — a string-prefix check would leak the token to a look-alike host
 * (e.g. `https://api.example.com.attacker.com`).
 */
export function isSameOrigin(target: string, baseUrl: string): boolean {
  try {
    return new URL(target).origin === new URL(baseUrl).origin;
  } catch {
    return false;
  }
}

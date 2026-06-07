import test from "node:test";
import assert from "node:assert/strict";
import {
  ApiError,
  isSameOrigin,
  normalizeBaseUrl,
  parseApiError,
  toWebSocketBase,
  unwrapData,
} from "../../http";

test("unwrapData returns the data field from a success envelope", () => {
  assert.deepEqual(unwrapData({ data: { id: "x" }, meta: {} }), { id: "x" });
});

test("unwrapData passes through a bare payload (no envelope)", () => {
  assert.deepEqual(unwrapData([{ id: "x" }]), [{ id: "x" }]);
  assert.equal(unwrapData(undefined), undefined);
});

test("parseApiError reads the error envelope", () => {
  const err = parseApiError(409, {
    error: { code: "AF_ERR_CONFLICT", message: "already decided", details: { gate_id: "g1" } },
  });
  assert.ok(err instanceof ApiError);
  assert.equal(err.status, 409);
  assert.equal(err.code, "AF_ERR_CONFLICT");
  assert.equal(err.message, "already decided");
  assert.deepEqual(err.details, { gate_id: "g1" });
});

test("parseApiError falls back to a status-derived code", () => {
  assert.equal(parseApiError(404, {}).code, "AF_ERR_NOT_FOUND");
  assert.equal(parseApiError(401, undefined).code, "AF_ERR_UNAUTHORIZED");
});

test("ApiError.isAuth is true for 401", () => {
  assert.equal(parseApiError(401, {}).isAuth, true);
  assert.equal(parseApiError(500, {}).isAuth, false);
});

test("normalizeBaseUrl strips trailing slash and /v1", () => {
  assert.equal(normalizeBaseUrl("http://localhost:8000/"), "http://localhost:8000");
  assert.equal(normalizeBaseUrl("https://api.autofounder.ai/v1"), "https://api.autofounder.ai");
  assert.equal(normalizeBaseUrl("  http://x:8000/v1/  "), "http://x:8000");
});

test("toWebSocketBase maps http(s) to ws(s) with a /v1 suffix", () => {
  assert.equal(toWebSocketBase("http://localhost:8000"), "ws://localhost:8000/v1");
  assert.equal(toWebSocketBase("https://api.autofounder.ai/v1"), "wss://api.autofounder.ai/v1");
});

test("isSameOrigin accepts same origin and rejects look-alike hosts", () => {
  assert.equal(isSameOrigin("https://api.x.com/runs/1", "https://api.x.com"), true);
  assert.equal(isSameOrigin("http://localhost:8000/v1/runs/1", "http://localhost:8000"), true);
  // Token-leak vectors a prefix match would wrongly accept:
  assert.equal(isSameOrigin("https://api.x.com.attacker.com/steal", "https://api.x.com"), false);
  assert.equal(isSameOrigin("https://api.x.com@attacker.com/steal", "https://api.x.com"), false);
  assert.equal(isSameOrigin("https://api.x.com:8443/x", "https://api.x.com"), false);
  assert.equal(isSameOrigin("not a url", "https://api.x.com"), false);
});

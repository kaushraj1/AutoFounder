import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { base64UrlEncode, createPkcePair, createState, randomUrlSafe } from "../../pkce";

test("base64UrlEncode is URL-safe and unpadded", () => {
  const encoded = base64UrlEncode(Buffer.from([251, 255, 191, 0]));
  assert.ok(!/[+/=]/.test(encoded), "must not contain +, / or =");
});

test("randomUrlSafe yields distinct high-entropy values", () => {
  const a = randomUrlSafe(32);
  const b = randomUrlSafe(32);
  assert.notEqual(a, b);
  assert.ok(a.length >= 40);
});

test("createPkcePair challenge is the S256 hash of the verifier", () => {
  const pair = createPkcePair();
  assert.equal(pair.method, "S256");
  const expected = base64UrlEncode(createHash("sha256").update(pair.verifier).digest());
  assert.equal(pair.challenge, expected);
  // RFC 7636: verifier length between 43 and 128 chars.
  assert.ok(pair.verifier.length >= 43 && pair.verifier.length <= 128);
});

test("createState returns a non-empty token", () => {
  assert.ok(createState().length > 0);
});

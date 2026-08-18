# Thin context — reject-non-finite-numeric-input

**Touched files (expected):** `src/server.ts` only.

**Why thin:** existing validation-rule addition, HTTP-layer only. No new
endpoint, no new response field, no `openapi/openapi.yaml` or `contracts/*.ocl`
change.

**Bug:** `JSON.parse('{"a":1e400}')` yields `a === Infinity` (valid JSON
number literal, out-of-range magnitude collapses to Infinity per the
ECMAScript Number grammar). `typeof Infinity === "number"` so the existing
`typeof a !== "number"` check accepts it. The handler then computes a
non-finite result and `JSON.stringify({ result: Infinity })` silently
serializes to `{"result":null}` in an HTTP 200 response instead of the
already-documented 400 "Invalid request" path.

**Fix:** add a `Number.isFinite(...)` check alongside each existing
`typeof ... !== "number"` check in the `/calculate`, `/memory/add`, and
`/memory/subtract` handlers in `src/server.ts`; reuse the existing 400
error-response shape (`{ "error": "invalid request: require op, a, b" }` /
`{ "error": "invalid request: require value" }`) — no new error shape.

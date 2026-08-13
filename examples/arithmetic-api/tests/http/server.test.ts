/**
 * HTTP-level integration test for POST /calculate.
 *
 * Closes the gap identified by critique-integration-verification-report.json
 * for change `add-power-operation`: every other test in this repo calls
 * Calculator/Memory methods directly, so the request-validation whitelist in
 * src/server.ts (`OPERATIONS`, used by `isOperation()`) was never actually
 * exercised. That whitelist is the real runtime gate deciding whether a
 * live `POST /calculate` request with `op:"pow"` is dispatched to
 * `Calculator.pow` or rejected with 400 — a regression there (e.g. "pow"
 * missing from `OPERATIONS`) would ship invisibly, since no test hit the
 * HTTP layer. This test starts the real request listener from
 * src/server.ts on an ephemeral port and drives it with real HTTP requests.
 */
import { createServer, type Server } from "node:http";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { requestListener } from "../../src/server.js";

let server: Server;
let baseUrl: string;

beforeAll(async () => {
  server = createServer(requestListener);
  await new Promise<void>((resolve) => {
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  if (address === null || typeof address === "string") {
    throw new Error("expected server to bind to an ephemeral TCP port");
  }
  baseUrl = `http://127.0.0.1:${address.port}`;
});

afterAll(async () => {
  await new Promise<void>((resolve, reject) => {
    server.close((err) => (err ? reject(err) : resolve()));
  });
});

describe("POST /calculate (real HTTP layer)", () => {
  it("dispatches op:pow through the OPERATIONS whitelist and returns 200 {result}", async () => {
    const response = await fetch(`${baseUrl}/calculate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ op: "pow", a: 2, b: 10 }),
    });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ result: 1024 });
  });

  it("dispatches op:avg through the OPERATIONS whitelist and returns 200 {result}", async () => {
    const response = await fetch(`${baseUrl}/calculate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ op: "avg", a: 2, b: 10 }),
    });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ result: 6 });
  });

  it("still dispatches a pre-existing op (add) through the same whitelist", async () => {
    const response = await fetch(`${baseUrl}/calculate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ op: "add", a: 2, b: 3 }),
    });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ result: 5 });
  });

  it("rejects an op the whitelist does not recognize with 400", async () => {
    const response = await fetch(`${baseUrl}/calculate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ op: "not-a-real-op", a: 2, b: 10 }),
    });

    expect(response.status).toBe(400);
  });
});

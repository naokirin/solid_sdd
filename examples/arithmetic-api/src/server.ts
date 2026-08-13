import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { pathToFileURL } from "node:url";
import { Calculator, PreconditionError, type Operation } from "./calculator.js";
import { Memory } from "./memory.js";

const PORT = Number(process.env.PORT ?? 3000);

const OPERATIONS = new Set<Operation>(["add", "sub", "mul", "div", "mod", "pow", "avg"]);

/** Shared memory register for the process lifetime. */
const memory = new Memory();

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function readJson(req: IncomingMessage): Promise<unknown> {
  const raw = await readBody(req);
  if (!raw) {
    throw new PreconditionError("request body is required");
  }
  return JSON.parse(raw) as unknown;
}

/** Parse optional JSON body; empty body yields null (no error). */
async function readOptionalJson(req: IncomingMessage): Promise<unknown | null> {
  const raw = await readBody(req);
  if (!raw) {
    return null;
  }
  return JSON.parse(raw) as unknown;
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

function isOperation(value: unknown): value is Operation {
  return typeof value === "string" && OPERATIONS.has(value as Operation);
}

/**
 * The actual HTTP request-routing logic, exported so integration tests can
 * exercise it directly over a real ephemeral-port server (via
 * `createServer(requestListener).listen(0)`) without depending on the
 * fixed PORT this module binds to when run as the main entrypoint.
 */
export async function requestListener(req: IncomingMessage, res: ServerResponse): Promise<void> {
  try {
    if (req.method === "POST" && req.url === "/calculate") {
      const body = (await readJson(req)) as Record<string, unknown>;
      const { op, a, b } = body;

      if (!isOperation(op) || typeof a !== "number" || typeof b !== "number") {
        sendJson(res, 400, { error: "invalid request: require op, a, b" });
        return;
      }

      const result = Calculator[op](a, b);
      sendJson(res, 200, { result });
      return;
    }

    if (req.method === "POST" && req.url === "/memory/clear") {
      await readOptionalJson(req);
      const value = memory.clear();
      sendJson(res, 200, { memory: value });
      return;
    }

    if (req.method === "POST" && req.url === "/memory/recall") {
      await readOptionalJson(req);
      const value = memory.recall();
      sendJson(res, 200, { memory: value });
      return;
    }

    if (req.method === "POST" && req.url === "/memory/add") {
      const body = (await readJson(req)) as Record<string, unknown>;
      if (typeof body?.value !== "number") {
        sendJson(res, 400, { error: "invalid request: require value" });
        return;
      }
      const value = memory.add(body.value);
      sendJson(res, 200, { memory: value });
      return;
    }

    if (req.method === "POST" && req.url === "/memory/subtract") {
      const body = (await readJson(req)) as Record<string, unknown>;
      if (typeof body?.value !== "number") {
        sendJson(res, 400, { error: "invalid request: require value" });
        return;
      }
      const value = memory.subtract(body.value);
      sendJson(res, 200, { memory: value });
      return;
    }

    sendJson(res, 404, { error: "not found" });
  } catch (err) {
    if (err instanceof PreconditionError) {
      sendJson(res, 400, { error: err.message });
      return;
    }
    if (err instanceof SyntaxError) {
      sendJson(res, 400, { error: "invalid JSON" });
      return;
    }
    sendJson(res, 500, { error: "internal error" });
  }
}

/** True only when this module is executed directly (e.g. `npm start`), not when imported by a test. */
function isMainModule(): boolean {
  return process.argv[1] != null && import.meta.url === pathToFileURL(process.argv[1]).href;
}

if (isMainModule()) {
  createServer(requestListener).listen(PORT, () => {
    console.log(`arithmetic-api listening on http://localhost:${PORT}`);
  });
}

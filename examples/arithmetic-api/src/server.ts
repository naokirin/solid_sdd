import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { Calculator, PreconditionError, type Operation } from "./calculator.js";

const PORT = Number(process.env.PORT ?? 3000);

const OPERATIONS = new Set<Operation>(["add", "sub", "mul", "div"]);

async function readJson(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const raw = Buffer.concat(chunks).toString("utf8");
  if (!raw) {
    throw new PreconditionError("request body is required");
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

createServer(async (req, res) => {
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
}).listen(PORT, () => {
  console.log(`arithmetic-api listening on http://localhost:${PORT}`);
});

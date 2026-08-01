import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { createRootValue, executeGraphql, loadSchema } from "./schema.js";

const PORT = Number(process.env.PORT ?? 4000);
const schema = loadSchema();
const rootValue = createRootValue();

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

createServer(async (req, res) => {
  try {
    if (req.method === "POST" && req.url === "/graphql") {
      const raw = await readBody(req);
      const body = JSON.parse(raw) as {
        query?: string;
        variables?: Record<string, unknown>;
      };
      if (typeof body.query !== "string") {
        sendJson(res, 400, { errors: [{ message: "query is required" }] });
        return;
      }
      const result = await executeGraphql(
        schema,
        rootValue,
        body.query,
        body.variables,
      );
      sendJson(res, 200, result);
      return;
    }

    sendJson(res, 404, { errors: [{ message: "not found" }] });
  } catch (err) {
    if (err instanceof SyntaxError) {
      sendJson(res, 400, { errors: [{ message: "invalid JSON" }] });
      return;
    }
    sendJson(res, 500, { errors: [{ message: "internal error" }] });
  }
}).listen(PORT, () => {
  console.log(`arithmetic-graphql listening on http://localhost:${PORT}/graphql`);
});

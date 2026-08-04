import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import {
  InsufficientStockError,
  PreconditionError,
  ReservationService,
  UnauthorizedError,
} from "./reservation.js";

const PORT = Number(process.env.PORT ?? 3000);

/** Sample seed so a fresh process can exercise authorized reserve. */
ReservationService.seedStock("SKU-1", 100);

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

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

function errorPayload(err: {
  message: string;
  errorType?: string;
  name?: string;
}): { error: string; errorType: string } {
  return {
    error: err.message,
    errorType: err.errorType ?? err.name ?? "PreconditionError",
  };
}

function principalFrom(req: IncomingMessage): string | undefined {
  const principalHeader = req.headers["x-principal-id"];
  return Array.isArray(principalHeader) ? principalHeader[0] : principalHeader;
}

const lookupPath = /^\/reservations\/([^/]+)$/;
const releasePath = /^\/reservations\/([^/]+)\/release$/;
const expirePath = /^\/reservations\/([^/]+)\/expire$/;

createServer(async (req, res) => {
  try {
    if (req.method === "POST" && req.url === "/reservations") {
      const principal = principalFrom(req);
      if (!principal) {
        sendJson(res, 403, {
          error: "X-Principal-Id header is required",
          errorType: "UnauthorizedError",
        });
        return;
      }

      const body = (await readJson(req)) as Record<string, unknown>;
      const sku = body.sku;
      const quantity = body.quantity;
      const ttlSeconds = body.ttlSeconds;

      if (typeof sku !== "string" || typeof quantity !== "number") {
        sendJson(res, 400, {
          error: "invalid request: require sku (string) and quantity (integer)",
          errorType: "PreconditionError",
        });
        return;
      }

      const hold =
        typeof ttlSeconds === "number"
          ? ReservationService.reserve(principal, sku, quantity, ttlSeconds)
          : ReservationService.reserve(principal, sku, quantity);

      sendJson(res, 200, {
        holdId: hold.holdId,
        sku: hold.sku,
        quantity: hold.quantity,
        expiresAt: hold.expiresAt,
        availableStock: hold.availableStock,
      });
      return;
    }

    const pathOnly = req.url?.split("?")[0] ?? "";

    // OpenAPI: GET /reservations — authorized full-dump list (before /{holdId})
    if (req.method === "GET" && pathOnly === "/reservations") {
      const principal = principalFrom(req);
      if (!principal) {
        sendJson(res, 403, {
          error: "X-Principal-Id header is required",
          errorType: "UnauthorizedError",
        });
        return;
      }
      const holds = ReservationService.list(principal);
      sendJson(
        res,
        200,
        holds.map((hold) => ({
          holdId: hold.holdId,
          sku: hold.sku,
          quantity: hold.quantity,
          expiresAt: hold.expiresAt,
          availableStock: hold.availableStock,
        })),
      );
      return;
    }

    // OpenAPI: GET /reservations/{holdId} — authorized lookup (read-only)
    const lookupMatch =
      req.method === "GET" ? lookupPath.exec(pathOnly) : null;
    if (lookupMatch) {
      const principal = principalFrom(req);
      if (!principal) {
        sendJson(res, 403, {
          error: "X-Principal-Id header is required",
          errorType: "UnauthorizedError",
        });
        return;
      }
      const holdId = decodeURIComponent(lookupMatch[1] ?? "");
      const hold = ReservationService.lookup(principal, holdId);
      sendJson(res, 200, {
        holdId: hold.holdId,
        sku: hold.sku,
        quantity: hold.quantity,
        expiresAt: hold.expiresAt,
        availableStock: hold.availableStock,
      });
      return;
    }

    const releaseMatch =
      req.method === "POST" ? releasePath.exec(pathOnly) : null;
    if (releaseMatch) {
      const principal = principalFrom(req);
      if (!principal) {
        sendJson(res, 403, {
          error: "X-Principal-Id header is required",
          errorType: "UnauthorizedError",
        });
        return;
      }
      const holdId = decodeURIComponent(releaseMatch[1] ?? "");
      ReservationService.release(principal, holdId);
      res.writeHead(204);
      res.end();
      return;
    }

    // OpenAPI: POST /reservations/{holdId}/expire — no AuthZ header
    const expireMatch =
      req.method === "POST" ? expirePath.exec(pathOnly) : null;
    if (expireMatch) {
      const holdId = decodeURIComponent(expireMatch[1] ?? "");
      ReservationService.expire(holdId);
      res.writeHead(204);
      res.end();
      return;
    }

    sendJson(res, 404, { error: "not found", errorType: "PreconditionError" });
  } catch (err) {
    if (err instanceof UnauthorizedError) {
      sendJson(res, 403, errorPayload(err));
      return;
    }
    if (err instanceof InsufficientStockError) {
      sendJson(res, 400, errorPayload(err));
      return;
    }
    if (err instanceof PreconditionError) {
      sendJson(res, 400, errorPayload(err));
      return;
    }
    if (err instanceof SyntaxError) {
      sendJson(res, 400, {
        error: "invalid JSON",
        errorType: "PreconditionError",
      });
      return;
    }
    sendJson(res, 500, {
      error: "internal error",
      errorType: "PreconditionError",
    });
  }
}).listen(PORT, () => {
  console.log(`inventory-reservation listening on http://localhost:${PORT}`);
});

/** Named domain errors shared with OpenAPI errorType enum. */

export class PreconditionError extends Error {
  readonly errorType = "PreconditionError" as const;
  constructor(message: string) {
    super(message);
    this.name = "PreconditionError";
  }
}

export class InsufficientStockError extends Error {
  readonly errorType = "InsufficientStockError" as const;
  constructor(message: string) {
    super(message);
    this.name = "InsufficientStockError";
  }
}

export class UnauthorizedError extends Error {
  readonly errorType = "UnauthorizedError" as const;
  constructor(message: string) {
    super(message);
    this.name = "UnauthorizedError";
  }
}

export type Hold = {
  holdId: string;
  sku: string;
  quantity: number;
  expiresAt: string;
  availableStock: number;
};

const DEFAULT_TTL_SECONDS = 300;
const AUTHORIZED_PRINCIPALS = new Set(["principal-authorized"]);

let stockBySku = new Map<string, number>();
let holdsById = new Map<string, Hold>();
let holdSeq = 0;
/** Injectable service clock (OCL self.now()); null → Date.now(). */
let clockMs: number | null = null;

function isAuthorized(principal: string): boolean {
  return AUTHORIZED_PRINCIPALS.has(principal);
}

function nowMs(): number {
  return clockMs ?? Date.now();
}

export const ReservationService = {
  reset(): void {
    stockBySku = new Map();
    holdsById = new Map();
    holdSeq = 0;
    clockMs = null;
  },

  /**
   * Set the service clock used by OCL self.now() / HoldPastTtl.
   * Pass null to restore wall-clock Date.now().
   */
  setNow(ms: number | Date | null): void {
    if (ms === null) {
      clockMs = null;
      return;
    }
    clockMs = typeof ms === "number" ? ms : ms.getTime();
  },

  /** Current service clock millis (OCL self.now()). */
  now(): number {
    return nowMs();
  },

  seedStock(sku: string, available: number): void {
    if (available < 0) {
      throw new PreconditionError("seed stock must be non-negative");
    }
    stockBySku.set(sku, available);
  },

  availableStock(sku: string): number {
    return stockBySku.get(sku) ?? 0;
  },

  holds(): Hold[] {
    return [...holdsById.values()];
  },

  /**
   * Soft-hold quantity against a SKU for a TTL.
   * OCL: Reservation::reserve
   */
  reserve(
    principal: string,
    sku: string,
    quantity: number,
    ttlSeconds: number = DEFAULT_TTL_SECONDS,
  ): Hold {
    // pre PrincipalAuthorized
    if (!isAuthorized(principal)) {
      throw new UnauthorizedError("principal is not authorized");
    }
    // pre QuantityPositive
    if (!Number.isInteger(quantity) || quantity <= 0) {
      throw new PreconditionError("quantity must be a positive integer");
    }
    if (!sku || typeof sku !== "string") {
      throw new PreconditionError("sku is required");
    }
    if (!Number.isInteger(ttlSeconds) || ttlSeconds <= 0) {
      throw new PreconditionError("ttlSeconds must be a positive integer");
    }

    const available = stockBySku.get(sku) ?? 0;
    // pre SufficientAvailableStock
    if (available < quantity) {
      throw new InsufficientStockError(
        `insufficient stock for ${sku}: available ${available}, requested ${quantity}`,
      );
    }

    const nextAvailable = available - quantity;
    stockBySku.set(sku, nextAvailable);

    holdSeq += 1;
    const holdId = `hold-${holdSeq}`;
    const expiresAt = new Date(nowMs() + ttlSeconds * 1000).toISOString();
    const hold: Hold = {
      holdId,
      sku,
      quantity,
      expiresAt,
      availableStock: nextAvailable,
    };
    holdsById.set(holdId, hold);
    return hold;
  },

  /**
   * Look up an existing visible soft-hold by id. Read-only: stock and holds
   * unchanged. Unauthorized → UnauthorizedError; missing hold →
   * PreconditionError (W2 elevation-ready named channels).
   * OCL: Reservation::lookup
   */
  lookup(principal: string, holdId: string): Hold {
    // pre PrincipalAuthorized
    if (!isAuthorized(principal)) {
      throw new UnauthorizedError("principal is not authorized");
    }
    if (!holdId || typeof holdId !== "string") {
      throw new PreconditionError("holdId is required");
    }

    // pre HoldExists → named PreconditionError
    const hold = holdsById.get(holdId);
    if (!hold) {
      throw new PreconditionError(`hold not found: ${holdId}`);
    }

    // post ResultIsHoldDetails (current availableStock, not reserve-time snapshot);
    // AvailableStockUnchanged; HoldsUnchanged
    return {
      ...hold,
      availableStock: ReservationService.availableStock(hold.sku),
    };
  },

  /**
   * Full dump of currently visible soft-holds. Read-only: stock and holds
   * unchanged. Unauthorized → UnauthorizedError; empty array when none.
   * Each item uses current availableStock (LookupResponse-equivalent).
   * OCL: Reservation::list
   */
  list(principal: string): Hold[] {
    // pre PrincipalAuthorized
    if (!isAuthorized(principal)) {
      throw new UnauthorizedError("principal is not authorized");
    }

    // post ResultIsFullDumpOfVisibleHolds / EmptyCollectionWhenNoneVisible;
    // HoldsUnchanged; AvailableStockUnchanged
    return [...holdsById.values()].map((hold) => ({
      ...hold,
      availableStock: ReservationService.availableStock(hold.sku),
    }));
  },

  /**
   * Release a soft-hold. Unauthorized callers fail with named UnauthorizedError
   * and leave stock/holds unchanged (W3). Authorized success restores held
   * quantity to available stock and removes the hold (W4: HoldExists,
   * AvailableStockRestored, HoldRemoved).
   * OCL: Reservation::release
   */
  release(principal: string, holdId: string): void {
    // pre PrincipalAuthorized
    if (!isAuthorized(principal)) {
      throw new UnauthorizedError("principal is not authorized");
    }
    if (!holdId || typeof holdId !== "string") {
      throw new PreconditionError("holdId is required");
    }

    // pre HoldExists → named PreconditionError
    const hold = holdsById.get(holdId);
    if (!hold) {
      throw new PreconditionError(`hold not found: ${holdId}`);
    }

    // post AvailableStockRestored
    const available = stockBySku.get(hold.sku) ?? 0;
    stockBySku.set(hold.sku, available + hold.quantity);
    // post HoldRemoved
    holdsById.delete(holdId);
  },

  /**
   * Treat a soft-hold past TTL as expired: restore held quantity and remove
   * the hold. No principal / AuthZ (service-side). HoldPastTtl uses the
   * injectable service clock (setNow / now); tests may also mutate expiresAt
   * to the past so comparison against Date.now() succeeds without sleep.
   * OCL: Reservation::expire
   */
  expire(holdId: string): void {
    if (!holdId || typeof holdId !== "string") {
      throw new PreconditionError("holdId is required");
    }

    // pre HoldExists → named PreconditionError
    const hold = holdsById.get(holdId);
    if (!hold) {
      throw new PreconditionError(`hold not found: ${holdId}`);
    }

    // pre HoldPastTtl: expiresAt < self.now()
    const expiresAtMs = Date.parse(hold.expiresAt);
    if (!(expiresAtMs < nowMs())) {
      throw new PreconditionError("hold TTL has not elapsed");
    }

    // post AvailableStockRestoredOnExpiry
    const available = stockBySku.get(hold.sku) ?? 0;
    stockBySku.set(hold.sku, available + hold.quantity);
    // post HoldRemoved
    holdsById.delete(holdId);
  },
};

# inventory-reservation

solid_sdd end-to-end evaluation sample: TypeScript HTTP API + OpenAPI + UML OCL + Vitest.

Produced by a fresh `solidsdd-run` for change `initial-reservation` (soft-hold inventory with opaque-principal authZ and TTL). Framing / Brief / WorkPlan / per-item loop artifacts live under `.solidsdd/`.

## Scenario

| Behavior | HTTP (summary) | Domain error |
|----------|----------------|--------------|
| Authorized reserve | `POST /reservations` | — |
| Stock below request | same | `InsufficientStockError` |
| Unauthorized reserve/release/lookup | reserve / release / get | `UnauthorizedError` |
| Authorized release | `POST /reservations/{id}/release` | — |
| TTL expire | `POST /reservations/{id}/expire` | — |
| Authorized lookup | `GET /reservations/{holdId}` | — |
| Missing / not-visible hold | same GET | `PreconditionError` |

Stock and holds are **in-process** (sample bound). AuthZ is opaque principal allow/deny only—not a full IAM product.

## Contract locations

| Kind | Path |
|------|------|
| Gherkin | `requirements/reservation.feature` |
| OpenAPI | `openapi/openapi.yaml` |
| OCL | `contracts/Reservation.ocl` |
| Contract tests | `tests/contracts/reservation.test.ts` |
| Change SoT | `.solidsdd/changes/initial-reservation/` |

## Setup

```bash
npm install
npm test
npm start
```

## Lint (from solid_sdd checkout)

```bash
../../scripts/solidsdd-lint.sh --project-root .
```

## How this sample was built (cost note)

This tree is a **live `solidsdd-run` replay** artifact (high cost). The first WorkPlan put all five property items `ready` with identical `touches`, which forced five serial full loops over shared OpenAPI/OCL/src — correct under older “independent items” defaults, but expensive for greenfield.

**Do not** copy that WorkPlan shape for new greenfield runs. Prefer foundation → properties (`depends_on`), narrow `touches`, and keep each loop step as its own Task on the run parent (see [docs/run-cost.md](../../docs/run-cost.md) and [work-decomposition.md](../../reference-src/work-decomposition.md)).

Historical isolation notes in `run-state.json` record where whole-loop Tasks / combined verify+critique were used; those patterns are now **disallowed** by the execution model.

## Out of scope (this sample)

Payments, multi-warehouse, full IAM, UI, notifications, backorders beyond hard-fail, durable shared DB, formal (TLA+) concurrency proofs.

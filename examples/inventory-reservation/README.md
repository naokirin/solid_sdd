# inventory-reservation

solid_sdd end-to-end evaluation sample: TypeScript HTTP API + OpenAPI + UML OCL + Vitest.

Produced by a fresh `solidsdd-run` for change `initial-reservation` (soft-hold inventory with opaque-principal authZ and TTL). Framing / Brief / WorkPlan / per-item loop artifacts live under `.solidsdd/`.

## Scenario

| Behavior | HTTP (summary) | Domain error |
|----------|----------------|--------------|
| Authorized reserve | `POST /reservations` | — |
| Stock below request | same | `InsufficientStockError` |
| Unauthorized reserve/release | reserve / release | `UnauthorizedError` |
| Authorized release | `POST /reservations/{id}/release` | — |
| TTL expire | `POST /reservations/{id}/expire` | — |

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

## Out of scope (this sample)

Payments, multi-warehouse, full IAM, UI, notifications, backorders beyond hard-fail, durable shared DB, formal (TLA+) concurrency proofs.

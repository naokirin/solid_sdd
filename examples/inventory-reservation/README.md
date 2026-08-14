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
| Authorized lookup | `GET /reservations/{holdId}` | — (includes `availableStock`) |
| Missing / not-visible hold | same GET | `PreconditionError` |

Stock and holds are **in-process** (sample bound). AuthZ is opaque principal allow/deny only—not a full IAM product. That AuthZ stance is also recorded as durable knowledge [`knowledge/policies/POL-OPAQUE-PRINCIPAL-AUTHZ.md`](knowledge/policies/POL-OPAQUE-PRINCIPAL-AUTHZ.md) (harvested via `solidsdd-run` on `add-lookup-available-stock`).

## Contract locations

| Kind | Path |
|------|------|
| Gherkin | `requirements/reservation.feature`, `requirements/reservation-lookup.feature`, `requirements/reservation-lookup-available-stock.feature` |
| OpenAPI | `openapi/openapi.yaml` |
| OCL | `contracts/Reservation.ocl` |
| Contract tests | `tests/contracts/reservation.test.ts` |
| Change SoT | `.solidsdd/changes/` (`initial-reservation`, `add-reservation-lookup`, `add-lookup-available-stock`) |
| Knowledge | `knowledge/` + `.solidsdd/kg/` |

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

## Architecture design (Structurizr DSL Architecture Model)

`.solidsdd/architecture/{workspace.dsl,invariants.yaml}` is a **persistent, whole-project Architecture Model** (Structurizr DSL subset — see [reference-src/structurizr-dsl.md](../../reference-src/structurizr-dsl.md)), accumulated across two structural changes below. Neither touches `src/` — the sample's implementation intentionally remains a single `src/reservation.ts` file (see "Out of scope" below); each change's `status.json` stays `"active"`. `architecture-plan.json` under each change directory is a **generated projection** (`scripts/solidsdd-architecture/project.py`), not hand-authored — see [docs/architecture.md](../../docs/architecture.md).

- [`.solidsdd/changes/tweak-hold-log-wording/`](.solidsdd/changes/tweak-hold-log-wording/) — **No Architecture Change** example: an internal log-message wording change; `solidsdd-architecture` emits `architecture-plan.json` with `status: unchanged` and a one-line summary directly (Level 0, [architecture-depth.md](../../reference-src/architecture-depth.md)) — no `workspace.dsl`/`invariants.yaml`/`architecture-reasoning.md` edit, and critique(architecture_plan) is skipped entirely (see `adversarial-critique.md`'s "architecture_plan ... only when it wrote status: changed").
- [`.solidsdd/changes/structure-inventory-reservation-split/`](.solidsdd/changes/structure-inventory-reservation-split/) — **Boundary Split** example: `solidsdd-architecture` splits an `inventory` module (stock ownership) out of `reservation` (hold lifecycle), with a `reservation -> inventory` dependency and a `forbid_dependency: inventory -> reservation` constraint. Rationale is in [`architecture-reasoning.md`](.solidsdd/changes/structure-inventory-reservation-split/architecture-reasoning.md). A human-readable `solidsdd-report` snapshot (Brief, NFRs, ArchitecturePlan detail) is at [report.md](.solidsdd/changes/structure-inventory-reservation-split/report.md) / [report.html](.solidsdd/changes/structure-inventory-reservation-split/report.html) (predates the DSL migration; module/dependency/constraint content is unchanged).
- [`.solidsdd/changes/add-notification-module/`](.solidsdd/changes/add-notification-module/) — **New Module** example: adds a `notification` module (hold-expiry delivery) that depends on `reservation`, with a `forbid_dependency: reservation -> notification` constraint so hold-lifecycle rules stay independent of delivery mechanics. Rationale is in [`architecture-reasoning.md`](.solidsdd/changes/add-notification-module/architecture-reasoning.md).

Together these demonstrate that the Architecture Model records different information than Gherkin/OpenAPI/OCL/TLA+: module responsibilities, dependency direction, ownership, and structural constraints — not behavior or API shape. See [reference-src/architecture-axes.md](../../reference-src/architecture-axes.md). A **Dependency Inversion** example (Domain → Infrastructure becoming Domain → Port ← Infrastructure) lives in a separate minimal sample: [`examples/architecture-dependency-inversion/`](../architecture-dependency-inversion/).

## Knowledge layer

`.solidsdd/kg/` + `knowledge/` hold **durable cross-cutting** policies/concepts (not a living ChangeBrief). `solidsdd-run` **consults** before framing and **harvests** candidates after integration verify (human-gated; no auto-promote). See [reference-src/knowledge.md](../../reference-src/knowledge.md).

## Out of scope (this sample)

Payments, multi-warehouse, full IAM, UI, notifications, backorders beyond hard-fail, durable shared DB, formal (TLA+) concurrency proofs.

# Change context: add-lookup-available-stock

## 1. Demand and problem

After `add-reservation-lookup`, authorized callers can GET a soft-hold by id and receive hold details (`holdId`, `sku`, `quantity`, `expiresAt`), but the success payload does **not** include current available stock for that SKU. Operators and clients still need a second observation (or informal inspection) to know remaining availability alongside the hold. This change additively includes `availableStock` on the authorized lookup success response, keeps existing hold detail fields, preserves named `UnauthorizedError` / `PreconditionError` failure channels, and mutates neither stock nor holds on any path.

## 2. Drivers and constraints (from stakeholders / environment)

- Follow-on to `add-reservation-lookup` (`status: done`) and `initial-reservation` (`status: done`); inherit TypeScript/Node, OpenAPI, OCL, Vitest layout.
- Working language: **en** (project rule + explicit user request).
- Keep prior Features in force (do not silently contradict):
  - `requirements/reservation.feature` — reserve / insufficient-stock / unauthorized / release / TTL expire behaviors
  - `requirements/reservation-lookup.feature` — authorized get-by-id returns hold details without mutation; missing/not-visible and unauthorized fail with named domain errors without mutation
- Prior Brief `out_of_scope` themes remain in force: payments/checkout, multi-warehouse, full IAM beyond opaque-principal allow/deny, UI, notifications, backorders beyond hard-fail, durable shared DB, formal TLA+, TTL extend, list-by-SKU aggregates.
- Demand and error names settled by human: additive `availableStock` on `GET /reservations/{holdId}` success; `UnauthorizedError` / `PreconditionError`; no mutation.
- Knowledge: `.solidsdd/kg/` exists (schema/config/links); `knowledge/` is empty (no policies/decisions/concepts yet) — consult may follow; do not invent policy bodies.

## 3. Functional intent (summary)

- Authorized opaque principal `GET /reservations/{holdId}` success includes existing hold fields **plus** current `availableStock` for the hold’s SKU.
- Unauthorized → `UnauthorizedError`; missing/not-visible → `PreconditionError`; no stock/hold mutation on success or failure.
- Detail and acceptance live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | Authorized GET success includes holdId, sku, quantity, expiresAt + availableStock for hold’s SKU; missing/not-visible → PreconditionError; no mutation | Additive stock observation on lookup | Threshold: success returns all five fields; missing/not-visible always PreconditionError, no mutation. Measurement: OCL-derived Vitest + OpenAPI |
| NFR2 | security | in_scope | Unauthorized → UnauthorizedError; no mutation | Extends settled opaque-principal authZ | Threshold: unauthorized never mutates; authorized can look up when visible. Measurement: contract tests + OpenAPI + OCL pre |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput targets | Sample workload | — |
| NFR4 | operability | in_scope | Checkable HTTP/API (OpenAPI) + module DbC (OCL) + Vitest for additive field | solid_sdd evaluate path | OpenAPI + `contracts/**/*.ocl` + passing `tests/contracts/**` covering availableStock + errors |
| NFR5 | compatibility | in_scope | Additive OpenAPI on LookupResponse; keep prior fields and reserve/release/expire/lookup surface | Follow-on; prior clients stay | Structural OpenAPI validity; prior ops + required lookup fields remain; availableStock added |
| NFR6 | maintainability | in_scope | UML OCL SoT; Vitest under `tests/contracts/**` | Inherited adapter layout | `contracts/**/*.ocl` + derived Vitest for additive success + named failures |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|-------------------------|-----------|--------|
| Language / runtime | TypeScript / Node HTTP API | New runtime, separate service | Inherit working sample; no stack migration asked | `repo_existing` / `user` |
| API style | HTTP + OpenAPI 3.x at `openapi/openapi.yaml` (additive `availableStock` on existing GET) | GraphQL, new endpoint for stock | Same SoT path; additive field on existing lookup | `repo_existing` / `user` |
| Module contracts | UML OCL `contracts/Reservation.ocl` → Vitest `tests/contracts/**` | Language-native asserts only | Inherited DbC + test layout | `repo_existing` / `user` |
| Persistence | Process-local / in-memory stock + holds (unchanged) | Durable shared DB | Prior sample bound; durable DB still out of scope | `repo_existing` |
| Formal methods | Not applied this change | TLA+ for concurrent races | Formal concurrency still out of scope | `repo_existing` / `user` |
| Auth mechanism | Opaque principal credential (sample-scale allow/deny) | Full OAuth/SSO/IAM | User excludes full IAM; same authZ pattern | `repo_existing` / `user` |

## 6. Key judgments and trade-offs

- Delta only: **add `availableStock` to authorized lookup success**; do not re-scope reserve/release/expire or rewrite prior Scenarios beyond necessary additive acceptance.
- Keep existing hold detail fields; additive field only — not a breaking rename/removal.
- Preserve named domain errors: unauthorized → `UnauthorizedError`; missing/not-visible → `PreconditionError`; no mutation on any path.
- AuthZ mirrors prior opaque-principal allow/deny — not a new IAM product.
- Payments, multi-warehouse, full IAM, UI, notifications, backorders, durable DB, formal TLA+, TTL extend, and list aggregates stay out of this change.
- Leave contract **density / adapter apply** to `solidsdd-judge`; do not over-specify implementation internals here.
- Working language: en (from project rule)

## 7. Open questions and deferred decisions

- Exact numeric semantics of `availableStock` relative to other concurrent holds (e.g. process-local available after all soft-holds): deferred to Brief/OCL if needed; default is current available stock for the hold’s SKU as already used on reserve success.
- Whether LookupResponse shares a schema component with ReserveResponse or stays a distinct schema with an added required property: deferred to OpenAPI apply (non-blocking; field presence is required).
- No blocking open questions for Brief scope honesty.

## 8. Links

- NFR SoT: `.solidsdd/changes/add-lookup-available-stock/nfr.json`
- Change Context gate: `.solidsdd/changes/add-lookup-available-stock/change-context-gate.json`
- ChangeBrief: `.solidsdd/changes/add-lookup-available-stock/change-brief.json` (pending)
- WorkPlan: `.solidsdd/changes/add-lookup-available-stock/work-plan.json` (pending)
- Prior change (done): `.solidsdd/changes/add-reservation-lookup/`
- Prior change (done): `.solidsdd/changes/initial-reservation/`
- Prior Features (in force): `requirements/reservation.feature`, `requirements/reservation-lookup.feature`
- Prior Brief out_of_scope: `.solidsdd/changes/add-reservation-lookup/change-brief.json`, `.solidsdd/changes/initial-reservation/change-brief.json`
- OpenAPI: `openapi/openapi.yaml` (LookupResponse currently lacks `availableStock`)
- OCL: `contracts/Reservation.ocl`
- Contract tests: `tests/contracts/**`
- Knowledge graph config: `.solidsdd/kg/` (present); durable `knowledge/` nodes: empty for now

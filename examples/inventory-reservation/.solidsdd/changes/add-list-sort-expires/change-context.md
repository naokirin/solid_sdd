# Change context: add-list-sort-expires

## 1. Demand and problem

Authorized soft-hold collection list already returns a full dump of currently visible soft-holds (same visibility universe as get-by-id, LookupResponse-equivalent items, no filters/paging). Callers still cannot rely on a **deterministic expiry order**: the dump must be sorted by `expiresAt` ascending (earlier expiry first). Equal `expiresAt` may use any stable order. Unauthorized list remains `UnauthorizedError` with no mutation. Filters, paging, and DTO shape must not change. Prior reserve / release / expire / lookup / concurrent behavior stays unchanged.

## 2. Drivers and constraints (from stakeholders / environment)

- LIGHT follow-on to `add-list-holds` (`status: done`); also inherits done prior changes: `add-concurrent-last-unit-safety`, `add-lookup-available-stock`, `add-reservation-lookup`, `initial-reservation`.
- Stack: TypeScript/Node, OpenAPI, UML OCL, Vitest — inherit; no migration.
- Working language: **en** (project rule + explicit user ask).
- User ask settled (no Grill): sort-only delta on existing list; reuse AuthZ + shared visibility Means; no filters/paging/DTO changes.
- Keep prior Features in force (do not silently contradict):
  - `requirements/reservation.feature` — reserve / insufficient-stock / unauthorized / release / TTL expire
  - `requirements/reservation-lookup.feature` — authorized get-by-id; UnauthorizedError / PreconditionError; no mutation
  - `requirements/reservation-lookup-available-stock.feature` — LookupResponse includes `availableStock`
  - `requirements/reservation-concurrent-safety.feature` — concurrent last-unit / shared InsufficientStockError
  - `requirements/reservation-list-holds.feature` — authorized full dump + UnauthorizedError on list (this change **adds** sort obligation; does not drop prior list properties)
- Knowledge: cite **`POL-OPAQUE-PRINCIPAL-AUTHZ`** (`maturity: canonical`, facet `decider`) — opaque-principal allow/deny only; unauthorized → named `UnauthorizedError`, no mutation. List AuthZ already covered; this change does not invent new AuthZ Means.
- Follow-on cost: prefer a single co-delivered property slice (sorted success + UnauthorizedError unchanged) — no vocabulary-only foundation item (OpenAPI/OCL already exist for list).

## 3. Functional intent (summary)

- Authorized opaque principal lists currently visible soft-holds as today, with items ordered by `expiresAt` ascending (earlier first); equal `expiresAt` → any stable order.
- Unauthorized → named `UnauthorizedError`; no stock/hold mutation.
- Do **not** add filters, paging, or DTO field changes; do not re-scope reserve/release/expire/lookup/concurrent.
- Detail and acceptance live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | Authorized list full dump sorted by expiresAt ascending; ties any stable order; no mutation; no filters/paging/DTO changes | Sort is the sole success-path delta | Threshold: expiresAt non-decreasing on authorized dump; never mutates. Measurement: OCL-derived Vitest + OpenAPI |
| NFR2 | security | in_scope | Reuse POL-OPAQUE-PRINCIPAL-AUTHZ; unauthorized → UnauthorizedError; no mutation | AuthZ unchanged | Threshold: unauthorized never mutates; authorized sees shared visibility sorted. Measurement: existing UnauthorizedError tests + cite POL |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput targets | In-memory sample dump | — |
| NFR4 | operability | in_scope | Sorted list checkable via OpenAPI and/or OCL + Vitest | solid_sdd evaluate path | OpenAPI and/or `contracts/**/*.ocl` + passing `tests/contracts/**` for sorted success + UnauthorizedError |
| NFR5 | compatibility | in_scope | Additive sort on existing GET /reservations; do not break prior surfaces or list AuthZ/visibility/DTO | LIGHT follow-on | Prior ops + list shape remain; only ordering added |
| NFR6 | maintainability | in_scope | UML OCL SoT; Vitest under `tests/contracts/**` for sorted list | Inherited adapter layout | `contracts/**/*.ocl` + derived Vitest for sorted success + UnauthorizedError |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|-------------------------|-----------|--------|
| Language / runtime | TypeScript / Node HTTP API | New runtime | Inherit working sample | `repo_existing` |
| API style | HTTP + OpenAPI 3.x at `openapi/openapi.yaml` (document sort on existing GET `/reservations`) | New path/operation | List surface already exists from `add-list-holds` | `repo_existing` |
| HTTP list wire | Keep **GET `/reservations`** / `Reservation::list` | New endpoint for “sorted list” | Sort is behavior on the existing collection read | `user` / `repo_existing` |
| Module contracts | UML OCL `contracts/Reservation.ocl` → Vitest `tests/contracts/**` | Language-native asserts only | Inherited DbC + test layout | `repo_existing` |
| Persistence | Process-local / in-memory (unchanged) | Durable shared DB | Prior sample bound | `repo_existing` |
| Formal methods | Not applied this change | Extend TLA+ for list order | Concurrent safety owns formal; sort is a read-order property | `repo_existing` / `user` |
| Auth mechanism | Opaque principal (POL-OPAQUE-PRINCIPAL-AUTHZ) — reuse | New AuthZ / ownership scoping | Explicit user ask: reuse existing AuthZ Means | `user` / `repo_existing` |
| Sort Means | `expiresAt` ascending; equal expiry → any stable order | Descending; secondary keys required | Settled user ask | `user` |
| Filters / paging / DTO | Unchanged from `add-list-holds` | Add filters, paging, or field changes | Explicit out of this delta | `user` |

## 6. Key judgments and trade-offs

- Delta only: **sort authorized list dump by `expiresAt` ascending**; do not re-scope list AuthZ, visibility, filters, paging, or DTO.
- Visibility Means (**confirmed**, prior change): same universe as get-by-id — unchanged.
- AuthZ Means (**canonical**): **`POL-OPAQUE-PRINCIPAL-AUTHZ`** — reuse; unauthorized → `UnauthorizedError`; no mutation.
- Tie-break (**confirmed**, user): equal `expiresAt` → any **stable** order OK (no secondary key mandated).
- Leave contract **density / adapter apply** to `solidsdd-judge` / apply; prefer extending existing list contracts, not a new operation.
- Follow-on cost: expect **N ≈ 1** WorkPlan item co-delivering sorted success with existing UnauthorizedError coverage (no vocabulary-only foundation).
- Working language: en (from project rule)

## 7. Open questions and deferred decisions

- None blocking. Exact secondary sort key when `expiresAt` ties is intentionally unspecified (any stable order).
- Whether OpenAPI prose must mention sort order vs OCL/tests alone: deferred to judge/apply (non-blocking; property must be checkable).

## 8. Links

- NFR SoT: `.solidsdd/changes/add-list-sort-expires/nfr.json`
- Change Context gate: `.solidsdd/changes/add-list-sort-expires/change-context-gate.json`
- Policy cite: `knowledge/policies/POL-OPAQUE-PRINCIPAL-AUTHZ.md`
- Prior knowledge consult (list framing): `.solidsdd/changes/add-list-holds/knowledge-consult.md`
- ChangeBrief: `.solidsdd/changes/add-list-sort-expires/change-brief.json` (pending)
- WorkPlan: `.solidsdd/changes/add-list-sort-expires/work-plan.json` (pending)
- Prior change (immediate predecessor, done): `.solidsdd/changes/add-list-holds/`
- Prior changes (done): `.solidsdd/changes/add-concurrent-last-unit-safety/`, `.solidsdd/changes/add-lookup-available-stock/`, `.solidsdd/changes/add-reservation-lookup/`, `.solidsdd/changes/initial-reservation/`
- Prior Features (in force): `requirements/reservation.feature`, `requirements/reservation-lookup.feature`, `requirements/reservation-lookup-available-stock.feature`, `requirements/reservation-concurrent-safety.feature`, `requirements/reservation-list-holds.feature`
- OpenAPI: `openapi/openapi.yaml` (`GET /reservations` already present)
- OCL: `contracts/Reservation.ocl`
- Contract tests: `tests/contracts/**`

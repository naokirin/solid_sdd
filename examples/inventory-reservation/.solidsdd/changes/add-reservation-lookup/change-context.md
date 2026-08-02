# Change context: add-reservation-lookup

## 1. Demand and problem

After `initial-reservation`, callers can soft-hold, release, and expire holds but cannot read an existing soft-hold by id. Operators and client tests need a bounded, authorized **get-by-id** so they can confirm hold state without inventing informal inspection. Missing or not-visible holds must fail with a **named domain error**. Payments, multi-warehouse, full IAM, UI, notifications, and list/aggregate queries remain out of this demand.

## 2. Drivers and constraints (from stakeholders / environment)

- Follow-on to `initial-reservation` (`status: done`); inherit TypeScript/Node, OpenAPI, OCL, Vitest layout.
- Working language: **en** (project rule + explicit user request).
- Keep prior Features at `requirements/reservation.feature` in force (do not silently contradict):
  - Authorized reserve creates soft-hold and reduces available stock
  - Reserve fails when stock insufficient (named domain error; no hold; stock unchanged)
  - Unauthorized reserve/release fails (named domain error; no mutation)
  - Authorized release restores held quantity
  - Hold past TTL expires and restores available stock
- Prior Brief `out_of_scope` remains in force (plus this delta’s exclusions): payments/checkout, multi-warehouse, full IAM beyond opaque-principal allow/deny, UI, notifications, backorders beyond hard-fail, durable shared DB, formal concurrency; also **TTL extend** and **list-by-SKU aggregates** (not in this change).
- Stack and demand settled by human: additive authorized lookup by hold id; OpenAPI + OCL + Vitest stay checkable.

## 3. Functional intent (summary)

- Authorized opaque principal can **GET / look up** an existing soft-hold **by id** and receive hold details.
- Hold does not exist or is not visible → fail with a **named domain error**; no stock/hold mutation.
- Unauthorized caller → named domain error (same opaque-principal pattern); no mutation.
- Detail and acceptance live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | Authorized lookup by id returns existing visible soft-hold; missing/not-visible → named domain error; no mutation | Lookup correctness + stable failure vocabulary | Threshold: success returns hold; missing/not-visible always named error, no mutation. Measurement: OCL-derived Vitest + OpenAPI error channel |
| NFR2 | security | in_scope | Only authorized opaque principal may look up; unauthorized → named domain error; no mutation | Extends settled sample authZ to read API | Threshold: unauthorized never mutates; authorized can look up when visible. Measurement: contract tests + OpenAPI + OCL pre |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput targets | Sample workload | — |
| NFR4 | operability | in_scope | Checkable HTTP/API (OpenAPI) + module DbC (OCL) + Vitest for lookup | solid_sdd evaluate path | OpenAPI + `contracts/**/*.ocl` + passing `tests/contracts/**` covering lookup |
| NFR5 | compatibility | in_scope | Additive OpenAPI at `openapi/openapi.yaml`; do not break prior reserve/release/expire surface | Follow-on; prior clients stay | Structural OpenAPI validity; prior operations remain |
| NFR6 | maintainability | in_scope | UML OCL SoT; Vitest under `tests/contracts/**` for lookup | Inherited adapter layout | `contracts/**/*.ocl` + derived Vitest for get-by-id |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|-------------------------|-----------|--------|
| Language / runtime | TypeScript / Node HTTP API | New runtime, separate service | Inherit working sample; no stack migration asked | `repo_existing` |
| API style | HTTP + OpenAPI 3.x at `openapi/openapi.yaml` (additive lookup) | GraphQL, ad-hoc JSON-RPC | Same SoT path; additive read operation | `repo_existing` / `user` |
| Module contracts | UML OCL `contracts/Reservation.ocl` → Vitest `tests/contracts/**` | Language-native asserts only | Inherited DbC + test layout | `repo_existing` / `user` |
| Persistence | Process-local / in-memory stock + holds (unchanged) | Durable shared DB | Prior sample bound; durable DB still out of scope | `repo_existing` |
| Formal methods | Not applied this change | TLA+ for concurrent races | Formal concurrency still out of scope | `repo_existing` |
| Auth mechanism | Opaque principal credential (sample-scale allow/deny) | Full OAuth/SSO/IAM | User excludes full IAM; lookup uses same authZ pattern | `repo_existing` / `user` |

## 6. Key judgments and trade-offs

- Delta only: **get soft-hold by id**; do not re-scope reserve/release/expire or rewrite prior Scenarios.
- Prefer a **named domain error** for missing/not-visible holds so OpenAPI, OCL, and Vitest share one failure vocabulary (same style as insufficient-stock / unauthorized).
- AuthZ for lookup mirrors prior opaque-principal allow/deny — not a new IAM product.
- List-by-SKU, aggregates, TTL extend, and durable shared DB stay out of this change.
- Leave contract **density / adapter apply** to `solidsdd-judge`; do not over-specify field lists here.
- Working language: en (from project rule)

## 7. Open questions and deferred decisions

- Exact HTTP path/method shape for lookup (e.g. `GET /reservations/{id}` vs equivalent): deferred to OpenAPI apply (non-blocking; behavior is get-by-id).
- Exact “not visible” policy beyond “does not exist or not visible → named domain error” (e.g. expired-hold visibility): deferred to Brief/OCL if needed; default treat missing and not-visible as the same named failure unless Brief narrows it.
- Error JSON / status code for the new named domain error: deferred to OpenAPI apply (named error required).

## 8. Links

- NFR SoT: `.solidsdd/changes/add-reservation-lookup/nfr.json`
- Change Context gate: `.solidsdd/changes/add-reservation-lookup/change-context-gate.json`
- ChangeBrief: `.solidsdd/changes/add-reservation-lookup/change-brief.json` (pending)
- WorkPlan: `.solidsdd/changes/add-reservation-lookup/work-plan.json` (pending)
- Prior change (done): `.solidsdd/changes/initial-reservation/`
- Prior Features (in force): `requirements/reservation.feature`
- Prior Brief out_of_scope: `.solidsdd/changes/initial-reservation/change-brief.json`
- OpenAPI: `openapi/openapi.yaml`
- OCL: `contracts/Reservation.ocl`
- Contract tests: `tests/contracts/**`

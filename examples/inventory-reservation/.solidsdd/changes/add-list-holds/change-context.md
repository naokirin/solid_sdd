# Change context: add-list-holds

## 1. Demand and problem

After reserve, release, expire, get-by-id lookup (with `availableStock`), and concurrent last-unit safety, callers still cannot **list** currently visible soft-holds. Operators and client tests need a bounded, authorized **collection read** over the same visibility universe as get-by-id—without inventing ownership, roles, filters, or paging. Unauthorized callers must fail with named `UnauthorizedError` and must not mutate stock or holds. Payments, multi-warehouse, full IAM, UI, notifications, TTL extend, and list-by-SKU / filter dimensions remain outside this demand.

## 2. Drivers and constraints (from stakeholders / environment)

- Follow-on to `add-concurrent-last-unit-safety`, `add-lookup-available-stock`, `add-reservation-lookup`, and `initial-reservation` (all `status: done`); inherit TypeScript/Node, OpenAPI, OCL, Vitest layout.
- Working language: **en** (project rule + explicit sample rule).
- Keep prior Features in force (do not silently contradict):
  - `requirements/reservation.feature` — reserve / insufficient-stock / unauthorized / release / TTL expire
  - `requirements/reservation-lookup.feature` — authorized get-by-id; named UnauthorizedError / PreconditionError; no mutation
  - `requirements/reservation-lookup-available-stock.feature` — LookupResponse includes `availableStock`
  - `requirements/reservation-concurrent-safety.feature` — concurrent last-unit / shared InsufficientStockError channel
- Prior Brief `out_of_scope` themes remain in force **except** unfiltered collection list of currently visible soft-holds, which this change intentionally elevates: payments/checkout, multi-warehouse, full IAM beyond opaque-principal allow/deny, UI, notifications, backorders beyond hard-fail, durable shared DB productization, TTL extend, **list-by-SKU / filter dimensions / paging**, Alloy/other formal langs beyond what concurrent safety already added.
- Grill resolved Means (clarifications Q1–Q3, all A): shared visibility with get-by-id; no filter dimensions; full dump, LookupResponse-equivalent items including `availableStock`; empty OK; unauthorized → `UnauthorizedError`; no mutation.
- Knowledge: cite **`POL-OPAQUE-PRINCIPAL-AUTHZ`** (`maturity: canonical`, facet `decider`) — opaque-principal allow/deny only; full IAM out of scope; unauthorized → named `UnauthorizedError`, no mutation. Policy text today names reserve/release/expire/lookup; list uses the same Means (wording harvest may follow later).

## 3. Functional intent (summary)

- Authorized opaque principal **lists** all currently visible soft-holds (same visibility universe as get-by-id); no sku/status/time filters in this change.
- Success: one full dump (no paging); each item LookupResponse-equivalent (`holdId`, `sku`, `quantity`, `expiresAt`, `availableStock`); empty collection when none visible.
- Unauthorized → named `UnauthorizedError`; no stock/hold mutation on any path.
- Detail and acceptance live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | Authorized list returns full currently visible set; LookupResponse-equivalent items incl. availableStock; empty OK; no mutation | List correctness + checkable success shape | Threshold: full dump of visible set with five fields per item; empty when none; never mutates. Measurement: OCL-derived Vitest + OpenAPI |
| NFR2 | security | in_scope | Opaque-principal AuthZ only (POL-OPAQUE-PRINCIPAL-AUTHZ); unauthorized → UnauthorizedError; no mutation | Extends canonical AuthZ Means to list | Threshold: unauthorized never mutates; authorized sees shared visibility universe. Measurement: tests + OpenAPI + OCL; cite POL-OPAQUE-PRINCIPAL-AUTHZ |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput targets | Sample full dump; no SLI | — |
| NFR4 | operability | in_scope | Checkable HTTP/API (OpenAPI) + module DbC (OCL) + Vitest for list | solid_sdd evaluate path | OpenAPI + `contracts/**/*.ocl` + passing `tests/contracts/**` covering list + UnauthorizedError |
| NFR5 | compatibility | in_scope | Additive OpenAPI collection list; do not break prior reserve/lookup/release/expire/concurrent surfaces | Follow-on; prior clients stay | Structural OpenAPI validity; prior operations remain |
| NFR6 | maintainability | in_scope | UML OCL SoT; Vitest under `tests/contracts/**` for list | Inherited adapter layout | `contracts/**/*.ocl` + derived Vitest for full-dump success + UnauthorizedError |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|-------------------------|-----------|--------|
| Language / runtime | TypeScript / Node HTTP API | New runtime, separate service | Inherit working sample; no stack migration asked | `repo_existing` |
| API style | HTTP + OpenAPI 3.x at `openapi/openapi.yaml` (additive collection list) | GraphQL, ad-hoc JSON-RPC | Same SoT path; additive read operation | `repo_existing` |
| HTTP list wire | **GET `/reservations`** (collection method alongside existing `POST /reservations` and `GET /reservations/{holdId}`) | Different path/method (e.g. `/holds`, `/reservations/list`); defer entirely | Natural collection sibling; OpenAPI today has only `POST` on `/reservations` and `GET` on `/{holdId}` — **no method/path conflict**. Grill Q4 non-blocking; preferred default | `agent_default` (Grill Q4; no repo conflict) |
| Module contracts | UML OCL `contracts/Reservation.ocl` → Vitest `tests/contracts/**` | Language-native asserts only | Inherited DbC + test layout | `repo_existing` |
| Persistence | Process-local / in-memory stock + holds (unchanged) | Durable shared DB | Prior sample bound; durable DB still out of scope | `repo_existing` |
| Formal methods | Not applied this change | Extend TLA+ for list | Concurrent safety already owns formal; list is a read dump | `repo_existing` / `user` |
| Auth mechanism | Opaque principal credential (POL-OPAQUE-PRINCIPAL-AUTHZ allow/deny) | Full OAuth/SSO/IAM; principal-scoped ownership | User + Grill Q1 keep opaque Means; no ownership/IAM | `user` / `repo_existing` (cite POL-OPAQUE-PRINCIPAL-AUTHZ) |
| List delivery | Full dump, no paging; items LookupResponse-equivalent including `availableStock` | Paging; thinner DTO without availableStock | Grill Q3 option A confirmed | `user` (Grill) |
| Filter dimensions | None this change (unfiltered visible set only) | sku / status / TTL filters | Grill Q2 option A confirmed; prior list-by-SKU stays deferred | `user` (Grill) |

## 6. Key judgments and trade-offs

- Delta only: **list currently visible soft-holds**; do not re-scope reserve/release/expire/lookup/concurrent or rewrite prior Scenarios beyond additive acceptance.
- Visibility Means (**confirmed**, Grill Q1): same universe as get-by-id; any authorized opaque principal lists all currently visible holds — not self-only / ownership / tenant admin views.
- AuthZ Means (**canonical**): **`POL-OPAQUE-PRINCIPAL-AUTHZ`** — opaque-principal allow/deny only; full IAM out of scope; unauthorized → named `UnauthorizedError`; no stock/hold mutation.
- Filters (**confirmed**, Grill Q2): unfiltered only; prior **list-by-SKU aggregates** remain out of this change.
- Response Means (**confirmed**, Grill Q3): full dump, no paging; LookupResponse-equivalent items including `availableStock`; empty collection OK.
- HTTP path (**agent_default**, Grill Q4): `GET /reservations` — no conflict with existing `POST /reservations`.
- Leave contract **density / adapter apply** and exact JSON envelope (bare array vs `{ items: [] }`) to `solidsdd-judge` / OpenAPI apply.
- Working language: en (from project rule)

## 7. Open questions and deferred decisions

- Exact success JSON envelope (bare JSON array vs single wrapper with `items[]`): deferred to OpenAPI apply (non-blocking; Q3 requires either; item fields fixed).
- Whether to harvest an updated wording of `POL-OPAQUE-PRINCIPAL-AUTHZ` to name **list** beside lookup: deferred to knowledge harvest after delivery (non-blocking; Means already apply).
- No blocking open questions for Brief scope honesty. Clarifications Q1–Q3 resolved; Q4 settled in §5 as `GET /reservations`.

## 8. Links

- NFR SoT: `.solidsdd/changes/add-list-holds/nfr.json`
- Change Context gate: `.solidsdd/changes/add-list-holds/change-context-gate.json`
- Clarifications: `.solidsdd/changes/add-list-holds/clarifications/open.json`
- Knowledge consult: `.solidsdd/changes/add-list-holds/knowledge-consult.md`
- Policy cite: `knowledge/policies/POL-OPAQUE-PRINCIPAL-AUTHZ.md`
- ChangeBrief: `.solidsdd/changes/add-list-holds/change-brief.json` (pending)
- WorkPlan: `.solidsdd/changes/add-list-holds/work-plan.json` (pending)
- Prior changes (done): `.solidsdd/changes/add-concurrent-last-unit-safety/`, `.solidsdd/changes/add-lookup-available-stock/`, `.solidsdd/changes/add-reservation-lookup/`, `.solidsdd/changes/initial-reservation/`
- Prior Features (in force): `requirements/reservation.feature`, `requirements/reservation-lookup.feature`, `requirements/reservation-lookup-available-stock.feature`, `requirements/reservation-concurrent-safety.feature`
- Prior Brief out_of_scope (list-by-SKU still deferred): `.solidsdd/changes/add-reservation-lookup/change-brief.json`, `.solidsdd/changes/add-lookup-available-stock/change-brief.json`
- OpenAPI: `openapi/openapi.yaml` (`POST /reservations`, `GET /reservations/{holdId}`; no collection GET yet)
- OCL: `contracts/Reservation.ocl`
- Contract tests: `tests/contracts/**`

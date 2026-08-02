# Change context: initial-reservation

## 1. Demand and problem

Teams evaluating solid_sdd need a bounded HTTP sample that soft-holds inventory: an authorized opaque principal reserves quantity against a SKU for a TTL (reducing available stock), fails cleanly when stock is insufficient or the caller is unauthorized (named domain errors; no hold; stock unchanged), and restores availability on authorized release or TTL expiry. Payments, multi-warehouse routing, full IAM, UI, and notifications are not part of this demand.

## 2. Drivers and constraints (from stakeholders / environment)

- End-to-end solid_sdd evaluation sample (contracts must be machine-checkable).
- Greenfield repo: README, `.gitignore`, project rule only — no package.json, Features, OpenAPI, or OCL yet.
- Working language: **en** (project rule + explicit user request).
- Out of scope (explicit): payments/checkout, multi-warehouse routing, full IAM product (SSO/OAuth UI), UI clients, notifications, backorders beyond hard-fail when stock is below request.
- Stack settled by human: TypeScript / Node HTTP API; OpenAPI at `openapi/openapi.yaml`; OCL under `contracts/**/*.ocl`; Vitest under `tests/contracts/**`.

## 3. Functional intent (summary)

- Authorized opaque principal can soft-hold (reserve) quantity against a SKU; available stock decreases for a TTL.
- Insufficient available stock → named domain error; no hold created; stock unchanged.
- Unauthorized caller → named domain error; no hold created; stock unchanged.
- Authorized release restores held quantity to available stock.
- Holds past TTL expire and restore availability.
- Detail and acceptance properties live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | Insufficient-stock reserve fails with named domain error (no hold; stock unchanged); authorized release and TTL expiry restore held quantity | Soft-hold correctness for callers/tests | Threshold: no hold / no stock decrease on insufficient reserve; release + TTL restore held qty. Measurement: OCL-derived Vitest + OpenAPI error channel |
| NFR2 | security | in_scope | Only authorized opaque principal may reserve or release; unauthorized → named domain error; no hold; stock unchanged | User-settled authZ for sample (not full IAM) | Threshold: unauthorized never mutates stock/holds; authorized can reserve/release. Measurement: contract tests + OpenAPI + OCL pre |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput targets | Sample workload | — |
| NFR4 | operability | in_scope | Checkable HTTP/API (OpenAPI) + module DbC (OCL) + Vitest | solid_sdd evaluate path | OpenAPI + `contracts/**/*.ocl` + passing `tests/contracts/**` |
| NFR5 | compatibility | in_scope | Additive sample API at `openapi/openapi.yaml` | Greenfield; path settled by user | OpenAPI structural lint when tooling available |
| NFR6 | maintainability | in_scope | UML OCL SoT; Vitest derived under `tests/contracts/**` | solid_sdd adapter + user layout | `contracts/**/*.ocl` + derived Vitest |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|-------------------------|-----------|--------|
| Language / runtime | TypeScript / Node HTTP API | Ruby/RSpec sample, Go, etc. | Settled by human for this evaluation sample | `user` |
| API style | HTTP + OpenAPI 3.x at `openapi/openapi.yaml` | GraphQL SDL, Protobuf | Settled path; HTTP boundary easy to lint | `user` |
| Module contracts | UML OCL under `contracts/**/*.ocl` → Vitest under `tests/contracts/**` | Language-native asserts only; RSpec | Settled DbC + test layout for solid_sdd | `user` |
| Persistence | Process-local / in-memory stock + holds | Durable DB, Redis-backed holds | Evaluation sample; multi-warehouse and durable ops out of scope; TTL soft-hold is demonstrable in-process | `agent_default` (sample bound) |
| Formal methods | Not applied this change | TLA+ for concurrent hold races | Concurrency_safety / distributed consistency not in demand | `agent_default` |
| Auth mechanism | Opaque principal credential (sample-scale check) | Full OAuth/SSO/IAM product | User excludes full IAM; requires authorized vs unauthorized named failures only | `user` (scope) |

## 6. Key judgments and trade-offs

- Treat “checkable HTTP + module contracts” as a success criterion; leave **density / adapter apply** to `solidsdd-judge` (do not over-specify OpenAPI field lists here).
- Prefer **named domain errors** for insufficient stock and unauthorized access so API, OCL, and tests share one failure vocabulary.
- Soft-hold reduces **available** stock for a TTL; release and expiry restore availability — no payments or checkout coupling.
- AuthZ is in-scope as opaque-principal allow/deny for this sample only — not SSO, OAuth UI, or a full IAM product.
- In-process persistence is a sample bound, not a product storage decision; durable inventory can be a later change.
- Working language: en (from project rule)

## 7. Open questions and deferred decisions

- Exact opaque-principal wire format (header name / token shape): deferred to OpenAPI apply (non-blocking; behavior is authorized vs unauthorized).
- Exact HTTP paths, status codes, and error JSON shape: deferred to OpenAPI apply.
- Concrete TTL default and clock/source for expiry: deferred to Brief/OCL (must be checkable; value not framed here).
- SKU seed / how initial stock is established in the sample: deferred to Brief/implementation convention.

## 8. Links

- NFR SoT: `.solidsdd/changes/initial-reservation/nfr.json`
- Change Context gate: `.solidsdd/changes/initial-reservation/change-context-gate.json`
- ChangeBrief: `.solidsdd/changes/initial-reservation/change-brief.json` (pending)
- WorkPlan: `.solidsdd/changes/initial-reservation/work-plan.json` (pending)
- Features: `requirements/` (pending)
- OpenAPI: `openapi/openapi.yaml` (pending)
- OCL: `contracts/**/*.ocl` (pending)
- Contract tests: `tests/contracts/**` (pending)

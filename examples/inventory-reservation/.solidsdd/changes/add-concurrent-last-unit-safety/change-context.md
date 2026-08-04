# Change context: add-concurrent-last-unit-safety

## 1. Demand and problem

Soft-hold reservation is already checkable for sequential insufficient stock (named `InsufficientStockError`), release, TTL expire, and authorized lookup with `availableStock`. Under **concurrent authorized reserves** against the same SKU, available stock must never go negative, and when only one unit remains, at most one concurrent reserve may create a hold. Race losers must surface the same named `InsufficientStockError` as sequential insufficient stock. Prior changes deferred formal concurrency (e.g. `initial-reservation` / lookup briefs X8); this change elevates the interleaving property to checkable OpenAPI + OCL and a bounded TLA+/TLC model under `formal/`.

## 2. Drivers and constraints (from stakeholders / environment)

- Follow-on to `add-lookup-available-stock`, `add-reservation-lookup`, and `initial-reservation` (all `status: done`); inherit TypeScript/Node, OpenAPI, OCL, Vitest layout.
- Working language: **en** (project rule).
- Keep prior Features in force (do not silently contradict):
  - `requirements/reservation.feature` — reserve / insufficient-stock / unauthorized / release / TTL expire
  - `requirements/reservation-lookup.feature` — authorized get-by-id + `availableStock`; named UnauthorizedError / PreconditionError; no mutation on lookup paths
- Prior Brief `out_of_scope` themes remain in force **except** formal concurrency, which this change intentionally lifts into scope: payments/checkout, multi-warehouse, full IAM beyond opaque-principal, UI, notifications, backorders beyond hard-fail, durable shared DB productization beyond sample bounds, TTL extend, list-by-SKU aggregates, Alloy/other formal langs.
- Demand settled by human: concurrent last-unit safety; non-negative available stock; race-loser = `InsufficientStockError`; OpenAPI + OCL + bounded TLA+/TLC under `formal/`; cite **POL-OPAQUE-PRINCIPAL-AUTHZ**; additive non-breaking; formal apply expects human gate later (Phase 3).
- Knowledge: cite `POL-OPAQUE-PRINCIPAL-AUTHZ` (opaque-principal allow/deny only; unauthorized → named UnauthorizedError, no mutation). No invent knowledge ids for concurrency invariants yet (Brief/Gherkin/contracts first).
- Formal toolchain at solid_sdd repo: `tools/tla/` (`tlc.sh`, `tla2tools.jar`); no `formal/` in this project yet — this change adds it.

## 3. Functional intent (summary)

- Concurrent authorized reserves on one SKU: available stock never negative; last unit → at most one successful soft-hold.
- Concurrent race losers fail with named `InsufficientStockError` (same channel as sequential insufficient stock).
- Keep opaque-principal AuthZ (`POL-OPAQUE-PRINCIPAL-AUTHZ`); unauthorized → `UnauthorizedError`, no mutation.
- Make the property checkable via additive OpenAPI + OCL (sequential/checkable contracts) and a bounded TLA+/TLC model under `formal/`.
- Detail and acceptance live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | Concurrent authorized reserves: available stock never negative; last unit → ≤1 hold; race losers → InsufficientStockError | Soft-hold safety under interleaving | Threshold: no negative available; with availableStock=1 at most one concurrent success; losers InsufficientStockError. Measurement: OpenAPI + OCL + Vitest; bounded TLA+/TLC under formal/ |
| NFR2 | security | in_scope | Opaque-principal AuthZ only (POL-OPAQUE-PRINCIPAL-AUTHZ); unauthorized → UnauthorizedError, no mutation | Concurrency must not weaken AuthZ | Threshold: unauthorized never mutates; authorized subject to stock/concurrency. Measurement: tests + OpenAPI + OCL; cite POL-OPAQUE-PRINCIPAL-AUTHZ |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput targets | Correctness sample, not SLI | — |
| NFR4 | operability | in_scope | Checkable OpenAPI + OCL→Vitest + bounded TLA+/TLC under formal/ | Phase 3 formal path; TLC via tools/tla/ | OpenAPI + contracts + tests/contracts + formal/*.tla (+ .cfg) TLC-checkable |
| NFR5 | compatibility | in_scope | Additive non-breaking; reuse InsufficientStockError; keep prior surfaces | Follow-on; prior clients stay | Structural OpenAPI validity; prior ops + named errors remain |
| NFR6 | maintainability | in_scope | OCL SoT + Vitest; formal/ TLA+/TLC only (no Alloy/other) | Inherited adapters + settled formal lang | contracts/ + tests/contracts/ + formal/ inspected; TLC against cfg |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|-------------------------|-----------|--------|
| Language / runtime | TypeScript / Node HTTP API | New runtime, separate service | Inherit working sample; no stack migration asked | `repo_existing` / `user` |
| API style | HTTP + OpenAPI 3.x at `openapi/openapi.yaml` (elevate concurrent/insufficient-stock channels; reuse `InsufficientStockError`) | GraphQL; new error names for race losers | Same SoT path; additive/non-breaking; same named error as sequential | `repo_existing` / `user` |
| Module contracts | UML OCL `contracts/Reservation.ocl` → Vitest `tests/contracts/**` | Language-native asserts only | Inherited DbC + test layout for sequential/checkable properties | `repo_existing` / `user` |
| Persistence | Process-local / in-memory stock + holds (sample bounds) | Durable shared DB productization | User keeps durable shared DB beyond sample bounds out of scope | `repo_existing` / `user` |
| Formal methods | Bounded TLA+/TLC under `formal/` (Phase 3; TLC via solid_sdd `tools/tla/`); human gate expected at formal **apply** | Alloy, other formal langs; defer formal again | User elevates interleaving to formal; toolchain exists; prior X8 deferred formal is lifted here | `user` (new intent) + `repo_existing` (TLC tools at solid_sdd) |
| Auth mechanism | Opaque principal credential (POL-OPAQUE-PRINCIPAL-AUTHZ) | Full OAuth/SSO/IAM | User and knowledge cite opaque-principal only | `repo_existing` / `user` / knowledge |

## 6. Key judgments and trade-offs

- Delta only: **concurrent last-unit / non-negative available stock safety** on reserve; do not re-scope lookup/release/expire beyond keeping them in force.
- Race loser uses the **same** named `InsufficientStockError` as sequential insufficient stock — not a new concurrent-only error type.
- Formal path is **in scope** for this change (bounded TLA+/TLC under `formal/`); Alloy and other formal languages stay out. Expect **human gate at formal apply** (orchestrator Phase 3), not at Change Context framing (already settled).
- Cite **POL-OPAQUE-PRINCIPAL-AUTHZ**; do not invent full IAM.
- Payments, multi-warehouse, durable shared DB productization beyond sample bounds, and unrelated product surfaces stay out.
- Leave contract **density / adapter apply** to `solidsdd-judge`; do not over-specify implementation locking strategy here beyond the checkable property.
- Working language: en (from project rule)

## 7. Open questions and deferred decisions

- Exact in-process synchronization mechanism (mutex, compare-and-swap, single-threaded queue, etc.): deferred to implement / ApplicationPlan — non-blocking for Brief scope as long as OpenAPI/OCL/TLA+ properties hold.
- Bound parameters for the TLA+ model (process counts, stock sizes): deferred to `solidsdd-apply-formal` / formal cfg — non-blocking; must remain TLC-checkable.
- No blocking open questions for Brief scope honesty.

## 8. Links

- NFR SoT: `.solidsdd/changes/add-concurrent-last-unit-safety/nfr.json`
- Change Context gate: `.solidsdd/changes/add-concurrent-last-unit-safety/change-context-gate.json`
- Knowledge consult: `.solidsdd/changes/add-concurrent-last-unit-safety/knowledge-consult.md`
- ChangeBrief: `.solidsdd/changes/add-concurrent-last-unit-safety/change-brief.json` (pending)
- WorkPlan: `.solidsdd/changes/add-concurrent-last-unit-safety/work-plan.json` (pending)
- Prior change (done): `.solidsdd/changes/add-lookup-available-stock/`
- Prior change (done): `.solidsdd/changes/add-reservation-lookup/`
- Prior change (done): `.solidsdd/changes/initial-reservation/`
- Prior Features (in force): `requirements/reservation.feature`, `requirements/reservation-lookup.feature`
- Prior Brief out_of_scope (formal deferred until this change): `.solidsdd/changes/add-lookup-available-stock/change-brief.json` X8, `.solidsdd/changes/add-reservation-lookup/change-brief.json`, `.solidsdd/changes/initial-reservation/change-brief.json`
- Policy: `knowledge/policies/POL-OPAQUE-PRINCIPAL-AUTHZ.md`
- OpenAPI: `openapi/openapi.yaml`
- OCL: `contracts/Reservation.ocl`
- Contract tests: `tests/contracts/**`
- Formal (to add): `formal/` (bounded TLA+/TLC); toolchain: solid_sdd `tools/tla/`
- Knowledge graph: `.solidsdd/kg/`; durable policy node present for opaque-principal AuthZ

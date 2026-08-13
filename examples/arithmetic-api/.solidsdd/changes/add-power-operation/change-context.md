# Change context: add-power-operation

## 1. Demand and problem

Clients of the arithmetic calculator service need to raise one number to the power of another (`a ** b`) through the same `POST /calculate` endpoint they already use for add/sub/mul/div/mod. Today there is no way to request exponentiation; callers would have to compute it client-side, which defeats the point of a single arithmetic API surface.

## 2. Drivers and constraints (from stakeholders / environment)

- This is a follow-on change to the `initial-calculator` sample (now `done`); it must extend, not rewrite, the existing OpenAPI, OCL, Gherkin, and contract-test surfaces.
- Scope is deliberately narrow: one new operation on the existing endpoint. No new routes, no memory-operation changes, no change to existing op behavior.
- Evaluation / sample service for solid_sdd — contracts must remain machine-checkable.

## 3. Functional intent (summary)

- Add `op: "pow"` to `POST /calculate`; computes `a ** b`.
- No new precondition/error case beyond the existing generic 400 on a malformed body. In particular — and this is explicit by user instruction — `pow` has **no zero-divisor-style precondition** the way `div`/`mod` do; later OCL/NFR work must not invent one (e.g. must not reject `b <= 0`, `a == 0`, or similar).
- Existing operations (`add`, `sub`, `mul`, `div`, `mod`) and memory operations are unchanged.
- Detail and acceptance properties live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | `pow` computes `a ** b` deterministically (IEEE-754 double semantics); no precondition/domain-error check is introduced for it | Must not silently inherit the div/mod zero-divisor `PreconditionError` pattern where it does not apply | Never throws `PreconditionError` for `pow`; malformed body still yields the existing generic 400 — verified via OCL-derived Vitest tests + new Gherkin Scenario |
| NFR2 | security | out_of_scope | N/A — no auth/authz surface introduced | Pure arithmetic addition to an already-unauthenticated endpoint | — |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput target | Sample workload; single native exponentiation op | — |
| NFR4 | operability | in_scope | `pow` is checkable end-to-end via HTTP/API + module contracts, like the other operations | solid_sdd evaluation path requires machine-checkable surfaces | `pow` present in OpenAPI `op` enum + passing `tests/contracts/*` |
| NFR5 | compatibility | in_scope | Additive-only change: `op` enum gains `pow`; existing ops/routes/error shapes unchanged | Explicit scope boundary from the change request | OpenAPI structural lint (Redocly `--extends=spec`) + diff review confirming additive-only enum change |
| NFR6 | maintainability | in_scope | UML OCL remains DbC source of truth for `pow`; tests derived from OCL | Consistency with existing adapter policy (`initial-calculator` NFR6) | `contracts/Calculator.ocl` documents `pow`; `tests/contracts/` exercises it |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|--------------------------|-----------|--------|
| Language / runtime | TypeScript / Node (unchanged) | — (no alternative considered; extending existing service) | Same stack as `initial-calculator`; no reason to diverge for one operation | `repo_existing` |
| API style | HTTP + OpenAPI 3.x, extend existing `POST /calculate` | New dedicated `/pow` route | User intent explicitly targets the existing `/calculate` endpoint; keeps surface uniform with other binary ops | `user` |
| Arithmetic implementation | JS `**` operator (`Math.pow` semantics) inside `Calculator.pow` | Custom power-series / BigInt-based implementation | Native operator is exact for the same numeric domain the other ops already use; no stated need for arbitrary precision | `agent_default` |
| Module contracts | UML OCL → Vitest contract tests (unchanged pattern) | Language-native contract keywords/gem | Matches `initial-calculator` NFR6 / solid_sdd adapter policy already adopted in this repo | `repo_existing` |
| Formal methods | Not applied this change | TLA+ for `pow` | Single, stateless, pure arithmetic operation; no concurrency/state property in demand | `agent_default` |

## 6. Key judgments and trade-offs

- **`pow` has no zero-divisor-style precondition.** This is stated explicitly so later NFR/OCL/DbC work does not over-generalize the div/mod `PreconditionError` pattern onto `pow`. Any `a`, `b` accepted by the existing request shape is valid input to `pow`.
- Extend the existing `op` enum and `calculate()` switch rather than introducing a parallel code path, to keep the operation set uniform and additive.
- Treat "checkable HTTP + module contracts" as the success criterion for NFR4, but leave contract density / adapter apply choices to `solidsdd-judge` — this document does not prescribe OpenAPI field-level detail.
- Out of scope, by explicit instruction: memory operations, changes to existing operation behavior, new HTTP routes.
- Working language: en (from user request — no project rule found; request is in English)

## 7. Open questions and deferred decisions

- Overflow / special-value behavior (e.g. very large exponents producing `Infinity`, `0 ** 0`, negative bases with fractional exponents producing `NaN`) is left to native JS `**` semantics unless a later change tightens it — non-blocking, matches how `initial-calculator` deferred div/mod sign conventions.
- Exact response JSON shape for `pow` results: deferred to OpenAPI apply, consistent with existing operations (no new shape expected).

## 8. Links

- NFR SoT: `.solidsdd/changes/add-power-operation/nfr.json`
- Change Context gate: `.solidsdd/changes/add-power-operation/change-context-gate.json`
- ChangeBrief: `.solidsdd/changes/add-power-operation/change-brief.json` (not yet written)
- WorkPlan: `.solidsdd/changes/add-power-operation/work-plan.json` (not yet written)
- Prior change: `.solidsdd/changes/initial-calculator/` (`status: done`) — establishes `Calculator`, `PreconditionError`, and the div/mod precondition pattern referenced in §6
- Features: `requirements/calculator.feature` (existing, to be extended with a new `pow` Scenario)
- Contracts: `contracts/Calculator.ocl` (existing, to be extended)
- OpenAPI: `openapi/openapi.yaml` (existing, `op` enum to be extended)

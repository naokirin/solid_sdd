# Change context: add-avg-operation

## 1. Demand and problem

Clients of the arithmetic calculator service need to compute the arithmetic mean of two numbers (`(a + b) / 2`) through the same `POST /calculate` endpoint they already use for add/sub/mul/div/mod/pow. Today there is no way to request an average; callers would have to compute it client-side from a separate `add` call, which defeats the point of a single arithmetic API surface.

## 2. Drivers and constraints (from stakeholders / environment)

- This is a follow-on change to the `initial-calculator` and `add-power-operation` samples (both `done`); it must extend, not rewrite, the existing OpenAPI, OCL, Gherkin, and contract-test surfaces.
- Scope is deliberately narrow: one new operation on the existing endpoint. No new routes, no memory-operation changes, no change to existing op behavior.
- Evaluation / sample service for solid_sdd — contracts must remain machine-checkable.
- `knowledge/` and `.solidsdd/kg/` are now populated (harvested from `add-power-operation`). This Change Context does not consult them — that is `solidsdd-knowledge`'s job in a later step — but their existence is noted here so the next step in the loop runs a consult pass (`knowledge-consult.md`) before Brief, given this change is close in shape to the change that produced that harvest.

## 3. Functional intent (summary)

- Add `op: "avg"` to `POST /calculate`; computes `(a + b) / 2`.
- No new precondition/error case beyond the existing generic 400 on a malformed body. In particular — and this is explicit by user instruction — `avg` has **no zero-divisor-style precondition**, the same pattern as the existing `pow` operation (unlike `div`/`mod`); later OCL/NFR work must not invent one.
- Existing operations (`add`, `sub`, `mul`, `div`, `mod`, `pow`) and memory operations are unchanged.
- Detail and acceptance properties live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | `avg` computes `(a + b) / 2` deterministically (IEEE-754 double semantics); no precondition/domain-error check is introduced for it | Same pattern as `pow`: no genuinely undefined input region exists (division is by the constant `2`), so it must not inherit the div/mod zero-divisor `PreconditionError` pattern | Never throws `PreconditionError` for `avg`; malformed body still yields the existing generic 400 — verified via OCL-derived Vitest tests + new Gherkin Scenario |
| NFR2 | security | out_of_scope | N/A — no auth/authz surface introduced | Pure arithmetic addition to an already-unauthenticated endpoint | — |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput target | Sample workload; single addition + constant division | — |
| NFR4 | operability | in_scope | `avg` is checkable end-to-end via HTTP/API + module contracts, like the other operations | solid_sdd evaluation path requires machine-checkable surfaces; module-level contract tests alone do not prove HTTP dispatch reachability | `avg` present in OpenAPI `op` enum + passing `tests/contracts/*` + a passing HTTP-level test for `avg` |
| NFR5 | compatibility | in_scope | Additive-only change: `op` enum gains `avg`; existing ops/routes/error shapes unchanged | Explicit scope boundary from the change request | OpenAPI structural lint (Redocly `--extends=spec`) + diff review confirming additive-only enum change |
| NFR6 | maintainability | in_scope | UML OCL remains DbC source of truth for `avg`; tests derived from OCL | Consistency with existing adapter policy (`initial-calculator` NFR6 / `add-power-operation` NFR6) | `contracts/Calculator.ocl` documents `avg`; `tests/contracts/` exercises it |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|--------------------------|-----------|--------|
| Language / runtime | TypeScript / Node (unchanged) | — (no alternative considered; extending existing service) | Same stack as `initial-calculator` / `add-power-operation`; no reason to diverge for one operation | `repo_existing` |
| API style | HTTP + OpenAPI 3.x, extend existing `POST /calculate` | New dedicated `/avg` route | User intent explicitly targets the existing `/calculate` endpoint; keeps surface uniform with other binary ops | `user` |
| Arithmetic implementation | `(a + b) / 2` inside `Calculator.avg` (native JS number division) | Rounding/formatting to a fixed precision; integer-only average | User specifies the plain arithmetic mean with no stated precision constraint; native double semantics already used by every other operation in this service | `agent_default` |
| Module contracts | UML OCL → Vitest contract tests (unchanged pattern) | Language-native contract keywords/gem | Matches `initial-calculator` NFR6 / `add-power-operation` §5 / solid_sdd adapter policy already adopted in this repo | `repo_existing` |
| Formal methods | Not applied this change | TLA+ for `avg` | Single, stateless, pure arithmetic operation; no concurrency/state property in demand | `agent_default` |

## 6. Key judgments and trade-offs

- **`avg` has no zero-divisor-style precondition.** Stated explicitly, by user instruction, so later NFR/OCL/DbC work does not over-generalize the div/mod `PreconditionError` pattern onto `avg`. This mirrors the precedent already set for `pow`: any `a`, `b` accepted by the existing request shape is valid input to `avg`. Means: decide each operation's precondition scope from its own domain, not by analogy to a sibling operation.
- Extend the existing `op` enum and `calculate()` switch rather than introducing a parallel code path, to keep the operation set uniform and additive.
- Treat "checkable HTTP + module contracts" as the success criterion for NFR4, but leave contract density / adapter apply choices to `solidsdd-judge` — this document does not prescribe OpenAPI field-level detail.
- Out of scope, by explicit instruction: memory operations, changes to existing operation behavior, new HTTP routes.
- Working language: en (from user request — no project-local rule file found under `examples/arithmetic-api`; request is in English; consistent with prior changes in this example)

## 7. Open questions and deferred decisions

- Rounding / precision of the result: `(a + b) / 2` is left to native JS double-precision division, unless a later change tightens it — non-blocking, matches how `initial-calculator` deferred div/mod sign conventions and `add-power-operation` deferred `pow` special-value behavior.
- Exact response JSON shape for `avg` results: deferred to OpenAPI apply, consistent with existing operations (no new shape expected).
- Whether `avg` should generalize beyond two operands (`a`, `b`) in a future change: explicitly out of scope here; current request shape is unchanged.

## 8. Links

- NFR SoT: `.solidsdd/changes/add-avg-operation/nfr.json`
- Change Context gate: `.solidsdd/changes/add-avg-operation/change-context-gate.json`
- ChangeBrief: `.solidsdd/changes/add-avg-operation/change-brief.json` (not yet written)
- WorkPlan: `.solidsdd/changes/add-avg-operation/work-plan.json` (not yet written)
- Prior change: `.solidsdd/changes/initial-calculator/` (`status: done`) — establishes `Calculator`, `PreconditionError`, and the div/mod precondition pattern
- Prior change: `.solidsdd/changes/add-power-operation/` (`status: done`) — establishes the "no precondition where none is mathematically required" pattern that `avg` follows, and its `knowledge-harvest.json`
- Knowledge (not consulted in this step; for `solidsdd-knowledge` consult before Brief): `knowledge/` (`patterns/`, `lessons/`, `policies/`, `decisions/`, `concepts/`), `.solidsdd/kg/`
- Features: `requirements/calculator.feature` (existing, to be extended with a new `avg` Scenario)
- Contracts: `contracts/Calculator.ocl` (existing, to be extended)
- OpenAPI: `openapi/openapi.yaml` (existing, `op` enum to be extended)

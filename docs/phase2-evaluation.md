# Phase 2 evaluation notes

Targets:

- `examples/arithmetic-graphql` — GraphQL SDL + OCL → Vitest
- `examples/arithmetic-ruby` — OCL → RSpec (no HTTP)

## Done

| Criterion | GraphQL | Ruby / RSpec |
|-----------|---------|--------------|
| Baseline verify green | **pass** (17 tests: OCL + SDL/boundary) | **pass** (7 examples) |
| Judge axes for stack | `api` + `adapter_hint: graphql`; `dbc` + `ocl` | `dbc` + `ocl` (no `api`); test target RSpec |
| Formal not silently dropped | concurrent memory / shared register → `formal` **defer** | N/A for Calculator-only; still allowed to emit `formal` defer if concurrency asked |
| Break → detect → repair | yes (below) | yes (below) |
| Contracts unchanged during repair | OCL / SDL / tests untouched | OCL / specs untouched |

## GraphQL — ApplicationPlan sketch (judge)

Intent: “maintain calculate + memory over GraphQL.”

```json
{
  "version": "1",
  "summary": "GraphQL boundary + OCL domain contracts; formal defer for shared memory concurrency.",
  "confidence": "high",
  "targets": [
    {
      "kind": "api",
      "location": "graphql/schema.graphql",
      "density": "standard",
      "rationale": "http_boundary via GraphQL SDL (adapter_hint graphql).",
      "adapter_hint": "graphql",
      "status": "apply",
      "signals": ["http_boundary", "stable_core"]
    },
    {
      "kind": "dbc",
      "location": "contracts/Calculator.ocl|Memory.ocl",
      "density": "standard",
      "rationale": "domain_contract for ops and memory posts.",
      "adapter_hint": "ocl",
      "status": "apply",
      "signals": ["domain_contract"]
    },
    {
      "kind": "formal",
      "location": "Memory shared register",
      "density": "thin",
      "rationale": "concurrency_safety desirable for multi-client memory; tooling Phase 3.",
      "adapter_hint": "defer-formal",
      "status": "defer",
      "signals": ["concurrency_safety"]
    }
  ]
}
```

## Ruby — ApplicationPlan sketch (judge)

Intent: “Calculator domain only; RSpec contract specs.”

```json
{
  "version": "1",
  "summary": "OCL DbC with RSpec test target; no API adapter.",
  "confidence": "high",
  "targets": [
    {
      "kind": "dbc",
      "location": "contracts/Calculator.ocl",
      "density": "standard",
      "rationale": "domain_contract; derive to spec/contracts (ruby-rspec).",
      "adapter_hint": "ocl",
      "status": "apply",
      "signals": ["domain_contract", "stable_core"]
    },
    {
      "kind": "api",
      "location": "n/a",
      "density": "thin",
      "rationale": "No HTTP/GraphQL surface in this sample.",
      "adapter_hint": "openapi",
      "status": "skip",
      "signals": []
    }
  ]
}
```

## Break / detect / repair

Same fault as MVP eval A: remove `mod` zero-divisor guard; leave OCL and derived tests unchanged.

### GraphQL (`arithmetic-graphql`)

1. Break: `Calculator.mod` no longer threw on `b === 0`.
2. Verify (`npm test`): **fail** — `pre DivisorIsNonZero` (1 failed / 17).
   - Suggested report shape: `result=fail`, `failure_class=implementation_bug`, `loop_action=retry`, `suggested_next_skills=["solidsdd-implement"]`, check kinds `graphql` + `ocl_tests`.
3. Implement: restored precondition; did not edit OCL / SDL / tests.
4. Verify: **pass** (17/17).

### Ruby (`arithmetic-ruby`)

1. Break: `Calculator.mod` omitted zero check (Ruby then raised `ZeroDivisionError` from `%`, not `PreconditionError`).
2. Verify (`bundle exec rspec`): **fail** — expected `Calculator::PreconditionError` (1 failure / 7).
   - Same suggested report shape with `ocl_tests` only (no API check).
3. Implement: restored guard; did not edit OCL / specs.
4. Verify: **pass** (7/7).

Working trees returned to green after repair (no lasting diffs).

## Skill-path notes

| Skill | GraphQL | Ruby |
|-------|---------|------|
| `solidsdd-apply-api` | `adapter_hint: graphql` → `graphql/schema.graphql` | skip |
| `solidsdd-apply-dbc` | OCL under `contracts/` | same |
| `solidsdd-derive-tests` | Vitest under `tests/contracts/` | RSpec under `spec/contracts/` (`ruby-rspec` adapter) |
| `solidsdd-verify` | SDL build + Vitest | `bundle exec rspec` |

Full `solidsdd-loop` Task-subagent re-run of a *new* feature was not repeated here; baseline + break/repair covers the Phase 2 adapter paths. OpenAPI loop evidence remains in [mvp-evaluation.md](mvp-evaluation.md).

## Remaining (deferred)

- Language-native DbC (opt-in design)
- Full Rails app sample
- `gh skill publish`
- Phase 3 formal apply tooling ([phase3.md](phase3.md))

# MVP evaluation notes

Evaluation target: `examples/arithmetic-api` (OpenAPI + OCL → Vitest contract tests).

## Done

| Criterion | Evidence |
|-----------|----------|
| Manual skill chain leaves contracts and passes verify | Added `mod` via context → judge → apply.* → derive-tests → implement → verify (7/7 pass) |
| Same change via `solidsdd.loop` | Reset tree, re-ran loop with Task subagents; verify pass; `formal` left visible as `defer` |
| Judge explains axes | ApplicationPlan with api/dbc `apply` and rationale |
| Formal not silently dropped | `defer` (or `skip` when N/A) with rationale |
| Intentional break is detected | Removed `mod` zero-divisor guard → `solidsdd-verify` **fail** (`ocl_tests`, suggested `solidsdd-implement`) → implement repair → verify **pass** |

## Break / detect / repair (eval A)

1. Break: `Calculator.mod` no longer threw on `b === 0` (OCL `pre DivisorIsNonZero` violated; contracts/tests unchanged).
2. `solidsdd-verify` (subagent): `result=fail`, `suggested_next_skills: ["solidsdd-implement"]`.
3. `solidsdd-implement` (subagent): restored precondition; did not weaken OCL/tests.
4. `solidsdd-verify` (subagent): `result=pass`.

Working tree returned to a green contract state after repair.

## Remaining (deferred)

- `gh skill publish` / GitHub remote distribution
- Optional scenario: calculator memory (M+/MR/…)
- Phase 2+ (richer judgment axes, more adapters, formal specs)

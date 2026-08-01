# MVP evaluation notes

Evaluation target: `examples/arithmetic-api` (OpenAPI + OCL → Vitest contract tests).

## Done

| Criterion | Evidence |
|-----------|----------|
| Manual skill chain leaves contracts and passes verify | Added `mod` via context → judge → apply.* → derive-tests → implement → verify (then 7/7; now 13/13 with memory) |
| Same change via `solidsdd.loop` | Reset tree, re-ran loop with Task subagents; verify pass; `formal` left visible as `defer` |
| Judge explains axes | ApplicationPlan with api/dbc `apply` and rationale |
| Formal not silently dropped | `defer` (or `skip` when N/A) with rationale |
| Intentional break is detected | Removed `mod` zero-divisor guard → `solidsdd-verify` **fail** → implement repair → verify **pass** |
| Scenario complexity: calculator memory | MC/MR/M+/M- via `/memory/*`, `Memory.ocl`, contract tests; verify **pass** (13 tests); concurrent formal **defer** |

## Break / detect / repair (eval A)

1. Break: `Calculator.mod` no longer threw on `b === 0` (OCL `pre DivisorIsNonZero` violated; contracts/tests unchanged).
2. `solidsdd-verify` (subagent): `result=fail`, `suggested_next_skills: ["solidsdd-implement"]`.
3. `solidsdd-implement` (subagent): restored precondition; did not weaken OCL/tests.
4. `solidsdd-verify` (subagent): `result=pass`.

Working tree returned to a green contract state after repair.

## Calculator memory (eval B)

1. `solidsdd-judge`: api+dbc `apply` (standard); formal concurrent memory **defer**.
2. `solidsdd-apply-api`: `POST /memory/clear|recall|add|subtract` + schemas; version 0.2.0.
3. `solidsdd-apply-dbc`: `contracts/Memory.ocl` (clear/recall/add/subtract posts).
4. `solidsdd-derive-tests`: `tests/contracts/memory.test.ts`.
5. `solidsdd-implement`: `src/memory.ts` + server wiring; `/calculate` unchanged.
6. `solidsdd-verify`: **pass** (13 tests); formal defer kept visible.

## Remaining (deferred)

- `gh skill publish` / GitHub remote distribution
- Phase 2 adapter eval: [phase2-evaluation.md](phase2-evaluation.md)
- Phase 3 formal design: [phase3.md](phase3.md); TLC sample: [phase3-evaluation.md](phase3-evaluation.md)
- Language-native DbC (opt-in)

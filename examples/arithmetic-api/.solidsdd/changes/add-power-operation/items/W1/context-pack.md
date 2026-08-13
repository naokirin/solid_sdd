# Context Pack — W1 (add-power-operation)

## Item
- `item_id`: W1
- `intent`: Design + implement + test the `pow` operation end-to-end (OpenAPI enum, OCL contract with no precondition, Gherkin Scenario already added, `Calculator.pow` + `calculate()` switch arm, contract tests).
- `acceptance_criterion` (Gherkin, already in `requirements/calculator.feature` lines 54-59):
  ```gherkin
  @R1 @R2 @R3 @R4 @R5 @SC1 @SC2 @SC3 @SC4 @SC5 @SC6
  Scenario: Power raises the base to the exponent
    Given a calculator service available to clients
    When the client raises one number to the power of another
    Then the result equals the mathematical power of those operands
    And the operation is never rejected by a precondition check
  ```
- `covers`: R1-R5, SC1-SC6
- `touches`: openapi/openapi.yaml, contracts/Calculator.ocl, requirements/calculator.feature (done), src/calculator.ts, tests/contracts/calculator.test.ts
- `depends_on`: none

## Scope authority
- ChangeBrief: `.solidsdd/changes/add-power-operation/change-brief.json`
- Change Context (NFR/tech): `.solidsdd/changes/add-power-operation/change-context.md`
- Critical constraint (Brief X4 / Context §6): `pow` has **no zero-divisor-style precondition**, unlike div/mod's `PreconditionError`. Do not add one.
- Out of scope: memory ops, changes to existing add/sub/mul/div/mod, new routes, response-shape changes, overflow/special-value tightening beyond native JS `**`.

## Toolchain (verbatim — do not rediscover)
- npm_test: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npm test`
- npm_install: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npm install`
- vitest_run: `/home/linuxbrew/.linuxbrew/bin/mise exec -- node "/home/naoki.guest/repos/github.com/naokirin/solid_sdd/examples/arithmetic-api/node_modules/vitest/vitest.mjs" run`
- openapi_lint: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npx --yes @redocly/cli@latest lint openapi/openapi.yaml --extends=spec`
- Full detail: `.solidsdd/host-toolchain.json` (ready=true)

## Existing surfaces to extend (not rewrite)
- `openapi/openapi.yaml`: `op` enum currently `[add, sub, mul, div, mod]` → add `pow`.
- `contracts/Calculator.ocl`: has `pre`/`post` contexts for div/mod (zero-divisor precondition) — `pow` needs a `post` only, no `pre`.
- `src/calculator.ts`: `Operation` union + `Calculator` object + `calculate()` switch — add `pow` consistently with existing style (see div/mod for precondition pattern to explicitly NOT copy).
- `tests/contracts/calculator.test.ts`: existing per-op test blocks — add a `pow` block in the same style.

## Cost-skip note
No B1/B3/B4/B5 conditions apply here (this item has real `touches` in `src/`, is not the only WorkPlan item context, and produces new contract-test edits) — full Plan → Implement → Verify required.

## Purpose of this run (do not let this change scope, only informs why you're being timed)
Live cost/timing measurement of solid_sdd's Canonical Consolidated Slice Model. Follow solidsdd-loop exactly; the parent is recording real wall-clock and tool-usage stats around this Task.

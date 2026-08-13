# Context Pack — W1 (add-avg-operation)

## Item
- `item_id`: W1
- `intent`: Design + implement + test the `avg` operation end-to-end (OpenAPI enum, OCL contract with no precondition, Gherkin Scenario already added, `Calculator.avg` + `calculate()` switch arm, `src/server.ts` OPERATIONS whitelist, module contract tests, and a real HTTP-dispatch test).
- `acceptance_criterion`: see `requirements/calculator.feature` — "Average returns the mean of its operands" (tags @R1-@R7 @SC1-@SC6).
- `covers`: R1-R7, SC1-SC6
- `touches`: openapi/openapi.yaml, contracts/Calculator.ocl, requirements/calculator.feature (done), src/calculator.ts, src/server.ts, tests/contracts/calculator.test.ts, tests/http/server.test.ts
- `depends_on`: none

## Scope authority
- ChangeBrief: `.solidsdd/changes/add-avg-operation/change-brief.json`
- Change Context: `.solidsdd/changes/add-avg-operation/change-context.md`
- Knowledge consult: `.solidsdd/changes/add-avg-operation/knowledge-consult.md` (2 canonical nodes applicable)
- Critical constraints: `avg` has **no precondition** (per `PAT-OPERATION-PRECONDITION-SCOPE`); the `src/server.ts` `OPERATIONS` whitelist **must** be extended and covered by a real HTTP-level test, not just module contract tests (per `LES-CONTRACT-TESTS-MISS-HTTP-DISPATCH` — this is the exact gap that caused a Failure-Driven retry cycle in the prior `pow` change; Brief R5/R7 and NFR4 already bake this in from the start this time).
- Out of scope: memory ops, changes to existing operations, new routes, rounding/precision guarantees, >2 operands.

## Plan Slice procedure
Read `/home/naoki.guest/repos/github.com/naokirin/solid_sdd/skills/solidsdd-loop/references/plan-slice-cheatsheet.md` (consolidated judge + apply-api + apply-dbc + derive-tests) instead of the four skills' individual files.

## Precedent to adapt (same-shape prior slice — parent's visual judgment: this is a clean fit)
The `add-power-operation` change (done) added `pow`, an operation of identical shape to `avg` (additive binary op on `POST /calculate`, no precondition, standard density, no gate). Adapt directly rather than re-deriving from axes:
- Judge precedent: `.solidsdd/changes/add-power-operation/items/W1/application-plan.json`
- OCL precedent: the `pow` context block in `contracts/Calculator.ocl` (no `pre`, explanatory comment)
- Test precedent: the `pow` `describe` block in `tests/contracts/calculator.test.ts`
- OpenAPI precedent: the `pow` enum entry in `openapi/openapi.yaml`
- **New this time (not present for pow)**: `avg` also needs the `src/server.ts` `OPERATIONS` whitelist entry and an HTTP-level test — `pow` did NOT have these done at Plan Slice time (they were added later via a Failure-Driven fix). Do them now, at Plan Slice / Implement Slice time, per Brief R5/R7 — do not repeat the gap.

## Toolchain (verbatim — do not rediscover)
- npm_test: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npm test`
- npm_install: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npm install`
- vitest_run: `/home/linuxbrew/.linuxbrew/bin/mise exec -- node "/home/naoki.guest/repos/github.com/naokirin/solid_sdd/examples/arithmetic-api/node_modules/vitest/vitest.mjs" run`
- openapi_lint: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npx --yes @redocly/cli@latest lint openapi/openapi.yaml --extends=spec`
- typecheck: `/home/linuxbrew/.linuxbrew/bin/mise exec -- node node_modules/.bin/tsc --noEmit -p .`
- Full detail: `.solidsdd/host-toolchain.json` (ready=true)

## Cost-skip note
No B1/B3/B5 applies (real touches in `src/`, new contract-test edits). **B4 may apply after Verify Slice**: this is the sole WorkPlan item; if its `verification-report.json` demonstrably covers `acceptance_of_whole`, tag `"acceptance_of_whole"` in a check's `covers` per `solidsdd-verify` guidance, so `scripts/solidsdd-next.sh next` can detect it and skip a duplicate integration verify.

## Purpose of this run
Real (not diagnostic/discarded) second live measurement of the improved solid_sdd framework, following up on the `add-power-operation` measurement (2026-08) and the Plan Slice diagnostics. Do the real work — this change will be kept, not reverted.

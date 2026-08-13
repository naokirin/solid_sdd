# Context Summary — arithmetic-api (for change: add-power-operation)

## Stack
- TypeScript / Node (Express-style HTTP server), package.json present, tests via Vitest.
- Toolchain (paste verbatim into every Task that runs shell commands; do not rediscover):
  - npm_test: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npm test`
  - npm_install: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npm install`
  - vitest_run: `/home/linuxbrew/.linuxbrew/bin/mise exec -- node "<repo>/examples/arithmetic-api/node_modules/vitest/vitest.mjs" run`
  - openapi_lint: `/home/linuxbrew/.linuxbrew/bin/mise exec -- npx --yes @redocly/cli@latest lint openapi/openapi.yaml --extends=spec`
  - Full detail: `.solidsdd/host-toolchain.json` (ready=true, missing=[])

## Existing change lifecycle
- Prior change `initial-calculator` is `status: done`.
- `active-change.json` currently points at `initial-calculator`; the intake step for this new change must update it to the new change_id.

## Contracts / requirements (existing, must be extended not rewritten)
- OpenAPI: `openapi/openapi.yaml` — `POST /calculate` body `{op,a,b}`, `op` enum currently `[add, sub, mul, div, mod]`.
- OCL: `contracts/Calculator.ocl`, `contracts/Memory.ocl`.
- Gherkin requirements: `requirements/calculator.feature`, `requirements/memory.feature`.
- Contract tests: `tests/contracts/*.test.ts` (Vitest).
- Source: `src/calculator.ts` (pure `Calculator` object + `calculate()` switch), `src/memory.ts`, `src/server.ts` (HTTP wiring).

## Change intent (user-supplied, fixed scope for this measurement run)
Add a new `pow` (power / exponentiation) operation to `POST /calculate`:
- `op: "pow"`, computes `a ** b`.
- No new precondition/error case is required beyond existing 400 on malformed body (unlike div/mod, pow has no zero-divisor precondition — note this explicitly so OCL isn't over-generalized).
- Must be reflected in: OpenAPI `op` enum, `contracts/Calculator.ocl`, `requirements/calculator.feature` (new Scenario), `src/calculator.ts` (`Operation` union + `Calculator.pow` + `calculate()` switch arm), `tests/contracts/*.test.ts` (or new test file) covering the new Scenario.
- Out of scope: memory operations, changing existing op behavior, new HTTP routes.

## Purpose of this run
This is a **live cost/timing measurement** of the solid_sdd Canonical Consolidated Slice Model (see `docs/run-cost.md`, `docs/execution-model.md`). The parent orchestrator (this session) is recording real wall-clock start/end timestamps around every subagent Task and Critique launch to compare against the theoretical estimates in `examples/arithmetic-api/cost-comparison.md`. Follow the standard skill procedures exactly — do not skip steps to make the measurement look better, and do not add steps beyond what the skills require.

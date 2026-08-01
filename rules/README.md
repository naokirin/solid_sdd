# solid_sdd — minimal rules for evaluation samples

## Contract artifacts

- OpenAPI: `openapi/openapi.yaml`
- OCL: `contracts/**/*.ocl`
- Derived contract tests: `tests/contracts/**/*.test.ts`

## Defaults

- API adapter: OpenAPI 3.x
- DbC adapter: OCL → contract tests (do not treat generated tests as source of truth)
- Formal specs: defer with rationale when relevant

## Verification

- Do not treat a change as done if OpenAPI or OCL-derived contract tests fail
- On verify failure, return to the suggested skill instead of weakening contracts

## Execution (orchestrator / subagent)

- `sdd.loop` is parent-only
- From an orchestrator, run apply / derive-tests / implement / verify as **explicit subagents** (Task), never inline in the parent
- Details: `docs/execution-model.md`

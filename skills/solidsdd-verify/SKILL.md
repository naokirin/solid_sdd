---
name: solidsdd-verify
description: >-
  Verify OpenAPI/GraphQL validity and OCL-derived contract tests for solid_sdd.
  When called from solidsdd-loop, must run as an explicit Task subagent. Emits
  VerificationReport with Phase 2 loop_action and failure_class on failure.
license: MIT
---

# solidsdd.verify

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task so verification is not self-graded by the implementer context. Solo user invocation may run in the current agent.

## Purpose

Emit a `VerificationReport`.

## References

- [verification-report.schema.json](references/verification-report.schema.json)
- [loop-retry.md](references/loop-retry.md)
- [openapi-adapter.md](references/openapi-adapter.md)
- [graphql-adapter.md](references/graphql-adapter.md)
- [ocl-adapter.md](references/ocl-adapter.md)
- [ruby-rspec-adapter.md](references/ruby-rspec-adapter.md)

## Constraints

- Do not modify implementation, OpenAPI/GraphQL, OCL, or tests to make checks pass
- Report only; suggest next skills on failure
- On fail, set `loop_action` and preferably `failure_class` per [loop-retry.md](references/loop-retry.md)
- Do not hide soft coverage: if OCL exists but contract tests are absent/empty, fail or skip with explicit detail (so `solidsdd-critique` on `verification_report` can escalate thin passes)
- Do not invent API lint results: only report Redocly output (or an explicit `skipped` with reason)

## API structural lint (Redocly)

When an API SoT file is present, run **@redocly/cli** with `--extends=spec` (structure / spec compliance; not style-heavy `recommended`).

Resolution order:

1. If `redocly` is on `PATH`, use it
2. Else try `npx --yes @redocly/cli@latest …`
3. If both fail (not installed, npx unavailable, network blocked), emit the API check as `result: skipped` with that reason — **do not** fail the whole report solely for missing Redocly (unlike formal TLC)

Commands (paths per [contract-layout](references/openapi-adapter.md) / project overrides):

```bash
# OpenAPI (kind: openapi)
redocly lint openapi/openapi.yaml --extends=spec
# or: npx --yes @redocly/cli@latest lint openapi/openapi.yaml --extends=spec

# GraphQL SDL (kind: graphql)
redocly lint graphql/schema.graphql --extends=spec
# or: npx --yes @redocly/cli@latest lint graphql/schema.graphql --extends=spec
```

- Non-zero exit → that check `fail`, `failure_class: contract_gap`, suggest `solidsdd-apply-api`
- Zero exit → `pass`
- Put a short command + summary in `detail` (truncate long logs)

OCL files have **no** dedicated structural CLI in MVP; rely on `ocl_tests` + critique(`dbc_contracts`).

## Steps

1. Locate API contract documents (OpenAPI and/or GraphQL per project).
2. For each present API SoT, run the Redocly lint procedure above; record one check per document (`kind: openapi` or `graphql`).
3. Run OCL-derived contract tests (MVP: project test script focusing on `tests/contracts` or `spec/contracts`).
4. Set overall `result` to `fail` if any **required** check fails (lint fail or test fail). Treat Redocly-unavailable as `skipped`, not fail.
5. On failure, fill `suggested_next_skills`, `loop_action`, and `failure_class`. Prefer setting optional `change_id` and per-check `covers` (WorkPlan item ids) when verifying a known slice.
6. Shape output per [verification-report.schema.json](references/verification-report.schema.json).
7. Return the report unchanged for the parent's follow-up `solidsdd-critique` (`subject: verification_report`).

## Success criteria

- Report lists each check with pass/fail/skipped
- When Redocly ran, API checks reflect its exit status (not agent guesswork)
- Failures include enough detail to choose the next skill and loop_action

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

## Constraints

- Do not modify implementation, OpenAPI/GraphQL, OCL, or tests to make checks pass
- Report only; suggest next skills on failure
- On fail, set `loop_action` and preferably `failure_class` per [loop-retry.md](references/loop-retry.md)

## Steps

1. Validate API contract documents present (OpenAPI and/or GraphQL per project).
2. Run OCL-derived contract tests (MVP: project test script focusing on `tests/contracts`).
3. Set overall `result` to `fail` if any required check fails.
4. On failure, fill `suggested_next_skills`, `loop_action`, and `failure_class`.
5. Shape output per [verification-report.schema.json](references/verification-report.schema.json).

## Success criteria

- Report lists each check with pass/fail/skipped
- Failures include enough detail to choose the next skill and loop_action

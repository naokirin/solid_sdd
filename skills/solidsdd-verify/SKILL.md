---
name: solidsdd-verify
description: >-
  Verify OpenAPI validity and OCL-derived contract tests for solid_sdd. When
  called from solidsdd-loop, must run as an explicit Task subagent to avoid
  self-grading. Use after implement/derive, or to check contract compliance.
license: MIT
---

# solidsdd.verify

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task so verification is not self-graded by the implementer context. Solo user invocation may run in the current agent.

## Purpose

Emit a `VerificationReport`.

## References

- [verification-report.schema.json](references/verification-report.schema.json)
- [openapi-adapter.md](references/openapi-adapter.md)
- [ocl-adapter.md](references/ocl-adapter.md)

## Constraints

- Do not modify implementation, OpenAPI, OCL, or tests to make checks pass
- Report only; suggest next skills on failure

## Steps

1. Validate OpenAPI document structure (see [openapi-adapter.md](references/openapi-adapter.md)).
2. Run OCL-derived contract tests (MVP: project test script focusing on `tests/contracts`).
3. Set overall `result` to `fail` if any required check fails.
4. On failure, suggest next skills (`solidsdd-apply-api`, `solidsdd-apply-dbc`, `solidsdd-derive-tests`, `solidsdd-implement`).
5. Shape output per [verification-report.schema.json](references/verification-report.schema.json).

## Success criteria

- Report lists each check with pass/fail/skipped
- Failures include enough detail to choose the next skill

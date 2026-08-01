---
name: solidsdd-verify
description: >-
  Verify OpenAPI validity and OCL-derived contract tests for solid_sdd. When
  called from solidsdd-loop, must run as an explicit Task subagent to avoid
  self-grading. Use after implement/derive, or to check contract compliance.
---

# solidsdd.verify

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task so verification is not self-graded by the implementer context. Solo user invocation may run in the current agent. See [docs/execution-model.md](../../docs/execution-model.md).

## Purpose

Emit a `VerificationReport` (`schemas/verification-report.schema.json`).

## Constraints

- Do not modify implementation, OpenAPI, OCL, or tests to make checks pass
- Report only; suggest next skills on failure

## Steps

1. Validate OpenAPI document structure (and contract alignment checks available in the project).
2. Run OCL-derived contract tests (MVP: project test script focusing on `tests/contracts`).
3. Set overall `result` to `fail` if any required check fails.
4. On failure, suggest next skills (`solidsdd-apply-api`, `solidsdd-apply-dbc`, `solidsdd-derive-tests`, `solidsdd-implement`).

## Success criteria

- Report lists each check with pass/fail/skipped
- Failures include enough detail to choose the next skill

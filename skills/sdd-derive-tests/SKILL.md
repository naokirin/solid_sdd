---
name: sdd-derive-tests
description: >-
  Generate contract tests from UML OCL for solid_sdd. Must run as an explicit
  Task subagent when called from sdd-loop. Use after OCL changes, or when asked
  to derive tests from contracts.
---

# sdd.derive.tests

## Execution

**subagent required** when invoked from `sdd.loop` (or any orchestrator chaining multiple phases). This is the core isolation boundary: OCL→tests must not share context with implement/verify. Parent must use Task. Solo user invocation may run in the current agent. See [docs/execution-model.md](../../docs/execution-model.md).

## Purpose

Generate or refresh contract tests from OCL. Tests are dependents of OCL.

## Defaults

- OCL: `contracts/**/*.ocl`
- Tests (MVP TypeScript): `tests/contracts/**/*.test.ts` with Vitest
- Adapter notes: `adapters/ocl/README.md`

## Constraints

- Derive tests only
- Do not change product implementation except minimal import/path fixes required for tests to compile
- Do not weaken or rewrite OCL/OpenAPI to make testing easier

## Subagent instructions

1. Read all relevant `.ocl` files.
2. For each operation:
   - happy-path assertions for `post` conditions
   - rejection cases for failed `pre` conditions
3. Map to the project's public API (domain function or HTTP) consistently with existing tests.
4. Do not invent behaviors absent from OCL (and OpenAPI if used for HTTP status mapping).
5. Prefer regenerating whole contract test files over drifting patches.

## Success criteria

- Every OCL `pre`/`post` has corresponding test coverage intent
- Tests are runnable with the project test script
- Return summary + list of changed test files to the parent

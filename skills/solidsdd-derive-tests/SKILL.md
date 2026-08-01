---
name: solidsdd-derive-tests
description: >-
  Generate contract tests from UML OCL for solid_sdd. Must run as an explicit
  Task subagent when called from solidsdd-loop. Use after OCL changes, or when
  asked to derive tests from contracts.
license: MIT
---

# solidsdd.derive.tests

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). This is the core isolation boundary: OCL→tests must not share context with implement/verify. Parent must use Task. Solo user invocation may run in the current agent.

## Purpose

Generate or refresh contract tests from OCL. Tests are dependents of OCL.

## References

- [ocl-adapter.md](references/ocl-adapter.md)
- [ruby-rspec-adapter.md](references/ruby-rspec-adapter.md) — when the project test target is RSpec

## Defaults

- OCL: `contracts/**/*.ocl`
- Tests (MVP TypeScript): `tests/contracts/**/*.test.ts` with Vitest
- Specs (Ruby): `spec/contracts/**/*_spec.rb` with RSpec — see [ruby-rspec-adapter.md](references/ruby-rspec-adapter.md)

## Constraints

- Derive tests only
- Do not change product implementation except minimal import/path fixes required for tests to compile
- Do not weaken or rewrite OCL/OpenAPI/GraphQL to make testing easier
- Do not introduce language-native contract gems unless the project already opted in

## Subagent instructions

Follow the "Subagent brief (ocl-to-tests)" section in [ocl-adapter.md](references/ocl-adapter.md). For Ruby targets, also follow [ruby-rspec-adapter.md](references/ruby-rspec-adapter.md).

1. Read all relevant `.ocl` files.
2. Detect test target from project layout (`tests/contracts` → Vitest, `spec/contracts` → RSpec) or explicit hint.
3. For each operation:
   - happy-path assertions for `post` conditions
   - rejection cases for failed `pre` conditions
4. Map to the project's public API (domain function or HTTP/GraphQL) consistently with existing tests.
5. Do not invent behaviors absent from OCL (and API contracts if used for status/error mapping).
6. Prefer regenerating whole contract test files over drifting patches.

## Success criteria

- Every OCL `pre`/`post` has corresponding test coverage intent
- Tests are runnable with the project test script
- Return summary + list of changed test files to the parent

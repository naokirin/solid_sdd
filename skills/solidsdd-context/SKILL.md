---
name: solidsdd-context
description: >-
  Gather repository stack, existing OpenAPI/GraphQL/OCL/formal contracts, and
  test layout for solid_sdd. Use before judge/apply/loop/run or when asked for
  SDD context.
license: MIT
---

# solidsdd.context

## Execution

**orchestrator** — run in the parent (`solidsdd.run`, `solidsdd.loop`, or the user-invoked agent). When `solidsdd-run` or `solidsdd-loop` is installed, follow that skill’s execution-model reference.

## Purpose

Produce a concise context summary so later skills do not rediscover the stack.

## References

- [contract-layout.md](references/contract-layout.md)

## Steps

1. Detect language/runtime (TypeScript/Node, Ruby, …).
2. Locate API contracts:
   - OpenAPI: `openapi/openapi.yaml` (or project-rule overrides)
   - GraphQL: `graphql/schema.graphql` if present → prefer `adapter_hint: graphql` later
3. Locate OCL: `contracts/**/*.ocl`
4. Locate derived tests:
   - Vitest: `tests/contracts/**`
   - RSpec: `spec/contracts/**`
5. Locate formal artifacts: `formal/**/*.tla` (+ `.cfg`); note whether TLC tooling is documented/available
6. Note package/verify commands (`npm test`, `bundle exec rspec`, `./verify.sh`, `tools/tla/tlc.sh`, …)
7. Flag gaps (missing API SoT, OCL, tests, or formal tooling when `formal/` exists)

## Output

Write a short markdown summary with:

- stack
- contract artifact paths (api / dbc / formal) and test target (vitest / rspec)
- gaps
- suggested next skill (`solidsdd-judge`, `solidsdd-loop` for one slice, or `solidsdd-run` for multi-criterion requirements)

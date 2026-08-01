---
name: solidsdd-context
description: >-
  Gather repository stack, existing OpenAPI/OCL contracts, and test layout for
  solid_sdd. Use before judge/apply/loop or when asked for SDD context.
---

# solidsdd.context

## Execution

**orchestrator** — run in the parent (`solidsdd.loop` or the user-invoked agent). See [docs/execution-model.md](../../docs/execution-model.md).

## Purpose

Produce a concise context summary so later skills do not rediscover the stack.

## Steps

1. Detect language/runtime (MVP focus: TypeScript/Node).
2. Locate OpenAPI docs (`openapi/openapi.yaml` or rule overrides).
3. Locate OCL contracts (`contracts/**/*.ocl`).
4. Locate contract tests (`tests/contracts/**`).
5. Note package scripts used for test/verify.

## Output

Write a short markdown summary with:

- stack
- contract artifact paths
- gaps (missing OpenAPI, OCL, or tests)
- suggested next skill (`solidsdd-judge` or `solidsdd-loop`)

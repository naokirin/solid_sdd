---
name: solidsdd-apply-api
description: >-
  Add or update OpenAPI 3.x API contracts for solid_sdd. When called from
  solidsdd-loop, must run as an explicit Task subagent. Use for ApplicationPlan
  kind=api with adapter_hint=openapi, or when asked to update API specs.
license: MIT
---

# solidsdd.apply.api

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task; do not edit OpenAPI inline in the parent. Solo user invocation may run in the current agent.

## Purpose

Maintain the OpenAPI document as the HTTP boundary contract.

## References

- [openapi-adapter.md](references/openapi-adapter.md)

## Constraints

- Edit OpenAPI artifacts only (plus tiny path fixes required to keep the doc valid)
- Do not change implementation, OCL, or contract tests

## Defaults

Follow [openapi-adapter.md](references/openapi-adapter.md) (`openapi/openapi.yaml`).

## Steps

1. Read `ApplicationPlan` targets with `kind=api` and `status=apply`.
2. Update paths, schemas, and error responses without breaking unrelated operations.
3. Keep `operationId` stable unless the operation is intentionally replaced.
4. Call out breaking changes explicitly in the summary.

## Success criteria

- OpenAPI reflects the intended HTTP behavior
- Document remains structurally valid OpenAPI 3.x

---
name: sdd-apply-api
description: >-
  Add or update OpenAPI 3.x API contracts for solid_sdd. When called from
  sdd-loop, must run as an explicit Task subagent. Use for ApplicationPlan
  kind=api with adapter_hint=openapi, or when asked to update API specs.
---

# sdd.apply.api

## Execution

**subagent required** when invoked from `sdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task; do not edit OpenAPI inline in the parent. Solo user invocation may run in the current agent. See [docs/execution-model.md](../../docs/execution-model.md).

## Purpose

Maintain the OpenAPI document as the HTTP boundary contract.

## Constraints

- Edit OpenAPI artifacts only (plus tiny path fixes required to keep the doc valid)
- Do not change implementation, OCL, or contract tests

## Defaults

Follow `adapters/openapi/README.md` (`openapi/openapi.yaml`).

## Steps

1. Read `ApplicationPlan` targets with `kind=api` and `status=apply`.
2. Update paths, schemas, and error responses without breaking unrelated operations.
3. Keep `operationId` stable unless the operation is intentionally replaced.
4. Call out breaking changes explicitly in the summary.

## Success criteria

- OpenAPI reflects the intended HTTP behavior
- Document remains structurally valid OpenAPI 3.x

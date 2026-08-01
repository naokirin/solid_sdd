---
name: solidsdd-apply-api
description: >-
  Add or update API boundary contracts (OpenAPI 3.x or GraphQL SDL) for solid_sdd.
  When called from solidsdd-loop, must run as an explicit Task subagent. Use for
  ApplicationPlan kind=api with adapter_hint openapi|graphql, or when asked to
  update API specs.
license: MIT
---

# solidsdd.apply.api

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task; do not edit API contracts inline in the parent. Solo user invocation may run in the current agent.

## Purpose

Maintain the HTTP/API boundary contract (OpenAPI or GraphQL SDL).

## References

- [openapi-adapter.md](references/openapi-adapter.md) — default for `adapter_hint: openapi`
- [graphql-adapter.md](references/graphql-adapter.md) — `adapter_hint: graphql` (Phase 2 skeleton)

## Constraints

- Edit API contract artifacts only (plus tiny path fixes required to keep the doc valid)
- Do not change implementation, OCL, or contract tests
- Honor `adapter_hint` from the ApplicationPlan target

## Defaults

- OpenAPI: [openapi-adapter.md](references/openapi-adapter.md) (`openapi/openapi.yaml`)
- GraphQL: [graphql-adapter.md](references/graphql-adapter.md) (`graphql/schema.graphql`)

## Steps

1. Read `ApplicationPlan` targets with `kind=api` and `status=apply`.
2. Choose adapter from `adapter_hint` (`openapi` or `graphql`; default `openapi` if omitted).
3. Update operations/types without breaking unrelated surface area.
4. Keep identifiers stable (`operationId` / GraphQL field names) unless intentionally replaced.
5. Call out breaking changes explicitly in the summary (and expect judge to have set `breaking` / `human_gate`).

## Success criteria

- Chosen adapter artifact reflects the intended API behavior
- Document remains structurally valid (OpenAPI 3.x or GraphQL SDL)

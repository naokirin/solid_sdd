---
name: solidsdd-apply-dbc
description: >-
  Add or update UML OCL Design-by-Contract specs for solid_sdd. When called from
  solidsdd-loop, must run as an explicit Task subagent. Use for ApplicationPlan
  kind=dbc with adapter_hint=ocl, or when asked for OCL.
license: MIT
---

# solidsdd.apply.dbc

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task; do not edit OCL inline in the parent. Solo user invocation may run in the current agent.

## Purpose

Maintain OCL as the source of truth for module contracts.

## References

- [ocl-adapter.md](references/ocl-adapter.md)
- [ruby-rspec-adapter.md](references/ruby-rspec-adapter.md) — alternate test-target layout (do not edit specs here)

## Constraints

- Edit `.ocl` only
- Do not edit generated contract tests (that is `solidsdd-derive-tests`)
- Do not change implementation or API contracts (OpenAPI / GraphQL)

## Defaults

Follow [ocl-adapter.md](references/ocl-adapter.md) (`contracts/**/*.ocl`).

## Steps

1. Read `ApplicationPlan` targets with `kind=dbc` and `status=apply`.
2. Write or update `pre` / `post` / `inv` in OCL for the domain operations.
3. Keep HTTP/GraphQL concerns out of OCL when an API adapter already covers them; focus on domain meaning.
4. Do not hand-edit generated contract tests here—that is `solidsdd-derive-tests`.

## Success criteria

- OCL captures preconditions and postconditions for targeted operations
- Naming and context match the domain module (e.g. `Calculator`)

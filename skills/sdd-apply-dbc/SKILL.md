---
name: sdd-apply-dbc
description: >-
  Add or update UML OCL Design-by-Contract specs for solid_sdd. When called from
  sdd-loop, must run as an explicit Task subagent. Use for ApplicationPlan
  kind=dbc with adapter_hint=ocl, or when asked for OCL.
---

# sdd.apply.dbc

## Execution

**subagent required** when invoked from `sdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task; do not edit OCL inline in the parent. Solo user invocation may run in the current agent. See [docs/execution-model.md](../../docs/execution-model.md).

## Purpose

Maintain OCL as the source of truth for module contracts.

## Constraints

- Edit `.ocl` only
- Do not edit generated contract tests (that is `sdd-derive-tests`)
- Do not change implementation or OpenAPI

## Defaults

Follow `adapters/ocl/README.md` (`contracts/**/*.ocl`).

## Steps

1. Read `ApplicationPlan` targets with `kind=dbc` and `status=apply`.
2. Write or update `pre` / `post` / `inv` in OCL for the domain operations.
3. Keep HTTP concerns out of OCL when OpenAPI already covers them; focus on domain meaning.
4. Do not hand-edit generated contract tests here—that is `sdd-derive-tests`.

## Success criteria

- OCL captures preconditions and postconditions for targeted operations
- Naming and context match the domain module (e.g. `Calculator`)

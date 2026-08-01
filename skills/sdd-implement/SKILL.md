---
name: sdd-implement
description: >-
  Implement or update code to satisfy OpenAPI and OCL contracts in solid_sdd.
  When called from sdd-loop, must run as an explicit Task subagent. Use after
  apply/derive skills, or when verification fails due to implementation.
---

# sdd.implement

## Execution

**subagent required** when invoked from `sdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task so implementation cannot rewrite contracts in the same context. Solo user invocation may run in the current agent. See [docs/execution-model.md](../../docs/execution-model.md).

## Purpose

Make implementation satisfy OpenAPI and OCL-derived expectations.

## Constraints

- Change implementation (and non-contract app tests if needed) only
- Do not weaken or edit OCL / OpenAPI / derived contract tests to force a pass
- If the spec is wrong, stop and tell the parent to re-run apply skills

## Steps

1. Read OpenAPI and OCL (and existing contract tests).
2. Update domain logic and HTTP wiring to meet contracts.
3. Do not weaken OCL or OpenAPI to make tests pass—fix implementation or return to apply skills if the spec is wrong.
4. Keep changes scoped to the planned targets.

## Success criteria

- Implementation matches contracts
- Ready for `sdd-verify`

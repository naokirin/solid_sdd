---
name: solidsdd-implement
description: >-
  Implement or update code to satisfy OpenAPI and OCL contracts in solid_sdd.
  When called from solidsdd-loop, must run as an explicit Task subagent. Use after
  apply/derive skills, or when verification fails due to implementation.
license: MIT
---

# solidsdd.implement

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task so implementation cannot rewrite contracts in the same context. Solo user invocation may run in the current agent.

## Purpose

Make implementation satisfy OpenAPI and OCL-derived expectations.

## References

- [openapi-adapter.md](references/openapi-adapter.md)
- [ocl-adapter.md](references/ocl-adapter.md)
- [contract-layout.md](references/contract-layout.md)

## Constraints

- Change implementation (and non-contract app tests if needed) only
- Do not weaken or edit OCL / OpenAPI / derived contract tests to force a pass
- If the spec is wrong, stop and tell the parent to re-run apply skills

## Steps

1. Read OpenAPI and OCL (and existing contract tests) using paths in [contract-layout.md](references/contract-layout.md).
2. Update domain logic and HTTP wiring to meet contracts.
3. Do not weaken OCL or OpenAPI to make tests pass—fix implementation or return to apply skills if the spec is wrong.
4. Keep changes scoped to the planned targets.

## Success criteria

- Implementation matches contracts
- Ready for `solidsdd-verify`

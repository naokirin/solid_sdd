---
name: solidsdd-apply-formal
description: >-
  Add or update formal specifications (TLA+/Alloy/…) for solid_sdd Phase 3.
  When called from solidsdd-loop, must run as an explicit Task subagent after
  human_gate approval. Use for ApplicationPlan kind=formal with status=apply.
license: MIT
---

# solidsdd.apply.formal

## Execution

**subagent required** when invoked from `solidsdd.loop`. Parent must use Task; do not edit formal specs inline in the parent. Solo user invocation may run in the current agent **only if** a human already approved the gate.

## Purpose

Maintain formal specs for narrow concurrency / safety properties.

## References

- [formal-adapter.md](references/formal-adapter.md) — apply conditions, TLC setup, artifact layout

## Constraints

- Edit formal artifacts only (`formal/**` by default)
- Do not edit OpenAPI/GraphQL, OCL, derived tests, or implementation here
- Do not expand scope beyond the ApplicationPlan location
- Refuse to proceed if `human_gate` was required and not approved

## Defaults

Follow [formal-adapter.md](references/formal-adapter.md).

## Steps

1. Confirm plan target `kind=formal`, `status=apply`, and human approval.
2. Choose concrete notation from `adapter_hint` (`tla`, `alloy`, …).
3. Write or update the model for the stated property only.
4. Summarize properties checked and any deferred checker wiring.

## Success criteria

- Formal artifact exists at the planned location
- Scope and properties match the judge rationale
- Return summary + changed files to the parent

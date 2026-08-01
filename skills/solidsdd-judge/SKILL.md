---
name: solidsdd-judge
description: >-
  Decide where to apply OpenAPI, OCL DbC, or defer formal specs for a change.
  When called from solidsdd-loop, must run as an explicit Task subagent to avoid
  implementation-cost bias. Use when planning SDD application or before apply.
license: MIT
---

# solidsdd.judge

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining multiple phases). Parent must use Task and must not re-judge or thin the returned plan inline. Solo user invocation may run in the current agent.

## Purpose

Emit an `ApplicationPlan`.

## References

- [application-plan.schema.json](references/application-plan.schema.json)
- [judgment-axes.md](references/judgment-axes.md)

## Constraints

- Produce the ApplicationPlan only (no OpenAPI / OCL / implementation / test edits)
- Judge from risk and boundary axes, not from how hard implementation would be
- Never silently drop formal needs—use `defer` with rationale

## Steps

1. Read change intent and current context (`solidsdd-context` output if available).
2. Apply axes in [judgment-axes.md](references/judgment-axes.md).
3. List targets with kind, location, density, rationale, adapter_hint, status.
4. Validate against [application-plan.schema.json](references/application-plan.schema.json).

## Output

JSON conforming to the ApplicationPlan schema, plus a one-paragraph summary. Return these artifacts to the parent unchanged in meaning.

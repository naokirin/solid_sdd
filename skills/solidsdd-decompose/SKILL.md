---
name: solidsdd-decompose
description: >-
  Split a requirement into a WorkPlan of items each with one verifiable
  acceptance criterion. When called from solidsdd-run, must run as an explicit
  Task subagent. Does not emit ApplicationPlan or edit contracts.
license: MIT
---

# solidsdd.decompose

## Execution

**subagent required** when invoked from `solidsdd.run` (or any outer orchestrator). Parent must use Task and must not thin or rewrite the returned WorkPlan inline. Solo user invocation may run in the current agent.

## Purpose

Emit a `WorkPlan` so `solidsdd-run` can drive one `solidsdd-loop` per item.

## References

- [work-plan.schema.json](references/work-plan.schema.json)
- [work-decomposition.md](references/work-decomposition.md) — **slice rules (required)**
- [human-gates.md](references/human-gates.md)

## Constraints

- Produce the WorkPlan only (no OpenAPI / OCL / formal / implementation / test edits)
- Do **not** emit an ApplicationPlan or choose contract kinds/densities
- Exactly **one** verifiable acceptance criterion per item
- Do not silently drop parts of the requirement—cover them in items and/or `acceptance_of_whole`

## Steps

1. Read change intent / requirement and context (`solidsdd-context` output if available).
2. Apply slice rules in [work-decomposition.md](references/work-decomposition.md).
3. List items with id, intent, acceptance_criterion, depends_on, status (plus optional confidence / human_gate).
4. Set `acceptance_of_whole` for the final integration `solidsdd-verify`.
5. Apply gate rules in [human-gates.md](references/human-gates.md) when ambiguity warrants a gate.
6. Validate against [work-plan.schema.json](references/work-plan.schema.json).

## Output

JSON conforming to the WorkPlan schema, plus a one-paragraph summary. Return these artifacts to the parent unchanged in meaning.

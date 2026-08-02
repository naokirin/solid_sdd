---
name: solidsdd-judge
description: >-
  Decide where to apply OpenAPI/GraphQL API contracts, OCL DbC, or defer formal
  specs. When called from solidsdd-loop, must run as an explicit Task subagent.
  Emits ApplicationPlan with Phase 2 signals, confidence, and human_gate fields.
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
- [human-gates.md](references/human-gates.md)
- [change-brief.md](references/change-brief.md) — when `.solidsdd/change-brief.json` exists

## Constraints

- Produce the ApplicationPlan only (no OpenAPI / OCL / implementation / test edits)
- Judge from risk and boundary axes, not from how hard implementation would be
- Never silently drop formal needs—use `defer` with rationale, or `apply` only under Phase 3 formal conditions in [judgment-axes.md](references/judgment-axes.md)
- Populate `signals` on targets when known; set `human_gate` / `breaking` / `confidence` per Phase 2+ rules

## Steps

1. Read change intent, ChangeBrief (`.solidsdd/change-brief.json` when present), and current context (`solidsdd-context` output if available). When unsure whether a boundary is in scope, prefer the Brief over inventing scope.
2. Apply axes in [judgment-axes.md](references/judgment-axes.md).
3. Apply gate rules in [human-gates.md](references/human-gates.md).
4. List targets with kind, location, density, rationale, adapter_hint, status (plus optional Phase 2 fields).
5. Validate against [application-plan.schema.json](references/application-plan.schema.json).

## Output

JSON conforming to the ApplicationPlan schema, plus a one-paragraph summary. Return these artifacts to the parent unchanged in meaning.

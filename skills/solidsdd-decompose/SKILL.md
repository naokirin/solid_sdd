---
name: solidsdd-decompose
description: >-
  Split a ChangeBrief (preferred) or requirement into a WorkPlan of items each
  with one property-level Gherkin Scenario. When called from solidsdd-run, must
  run as an explicit Task subagent. Does not emit ApplicationPlan or edit
  API/OCL/formal contracts.
license: MIT
---

# solidsdd.decompose

## Execution

**subagent required** when invoked from `solidsdd.run` (or any outer orchestrator). Parent must use Task and must not thin or rewrite the returned WorkPlan inline. Solo user invocation may run in the current agent.

## Purpose

Emit a `WorkPlan` so `solidsdd-run` can drive one `solidsdd-loop` per item. Normalize acceptance into **property-level Gherkin** Scenarios guided by the ChangeBrief.

## References

- [work-plan.schema.json](references/work-plan.schema.json)
- [work-decomposition.md](references/work-decomposition.md) — **slice rules (required)**
- [gherkin-requirements.md](references/gherkin-requirements.md) — **requirement format (required)**
- [change-brief.md](references/change-brief.md) — scope premise when Brief exists
- [change-lifecycle.md](references/change-lifecycle.md) — active Brief / WorkPlan paths
- [active-change.schema.json](references/active-change.schema.json)
- [human-gates.md](references/human-gates.md)

## Constraints

- Produce the WorkPlan only (plus optional `requirements/**/*.feature` normalization)
- Write WorkPlan to `.solidsdd/changes/<change_id>/work-plan.json` for the active change
- No ChangeBrief overwrite, OpenAPI / OCL / formal / implementation / contract-test edits
- Do **not** emit an ApplicationPlan or choose contract kinds/densities
- Exactly **one** Gherkin Scenario (checkable slice) per item in `acceptance_criterion`
- Prefer property-level Scenarios; cover Brief `in_scope` / `success_criteria`; do not pull in `out_of_scope`
- Do **not** treat Gherkin as Cucumber executable SoT

## Steps

1. Resolve active ChangeBrief via `.solidsdd/active-change.json` → `.solidsdd/changes/<change_id>/change-brief.json` (migrate legacy flat Brief if needed). Read change intent and context (`solidsdd-context` output if available).
2. If input is prose or incomplete Gherkin, normalize to Feature/Scenario form per [gherkin-requirements.md](references/gherkin-requirements.md) (create/update `.feature` under default layout when useful; new Scenarios for this Brief only).
3. Apply slice rules in [work-decomposition.md](references/work-decomposition.md).
4. List items with id, intent, acceptance_criterion (property-level Gherkin Scenario), depends_on, status (plus optional feature_path / scenario_name / confidence / human_gate).
5. Set `acceptance_of_whole` for the final integration `solidsdd-verify` (align with Brief `success_criteria`).
6. Apply gate rules in [human-gates.md](references/human-gates.md) when ambiguity warrants a gate.
7. Validate against [work-plan.schema.json](references/work-plan.schema.json).
8. Write JSON to `.solidsdd/changes/<change_id>/work-plan.json`.

## Output

JSON conforming to the WorkPlan schema, plus a one-paragraph summary and the WorkPlan path. Return these artifacts to the parent unchanged in meaning.

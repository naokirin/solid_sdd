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
- [run-cost.md](references/run-cost.md) — greenfield cost / `touches` vs `depends_on`
- [gherkin-requirements.md](references/gherkin-requirements.md) — **requirement format (required)**
- [working-language.md](references/working-language.md) — item / Feature prose language
- [change-brief.md](references/change-brief.md) — scope premise when Brief exists
- [change-lifecycle.md](references/change-lifecycle.md) — active Brief / WorkPlan paths
- [active-change.schema.json](references/active-change.schema.json)
- [human-gates.md](references/human-gates.md)

## Constraints

- Produce the WorkPlan only (plus optional `requirements/**/*.feature` normalization)
- Write WorkPlan to `.solidsdd/changes/<change_id>/work-plan.json` for the active change
- No ChangeBrief overwrite, OpenAPI / OCL / formal / implementation / contract-test edits
- Do **not** emit an ApplicationPlan or choose contract kinds/densities
- Exactly **one** Gherkin Scenario (or coherent group of related Scenarios sharing the same implementation boundary) per Slice/item in `acceptance_criterion`
- Do **not** create micro-items (`vocabulary-only`, `schema-only`, `test-only`, `verify-only`). Group Scenarios by coherent implementation boundary (Slice) per [work-decomposition.md](references/work-decomposition.md)
- Prefer property-level Scenarios; each item must set `covers` to Brief `in_scope` / `success_criteria` ids; do not cover `out_of_scope` ids; tag Scenarios with matching `@R*` / `@SC*`
- On greenfield / shared OpenAPI+OCL paths, follow **Greenfield / shared-contract** in [work-decomposition.md](references/work-decomposition.md) (foundation `depends_on`, narrow `touches`)
- Do **not** treat Gherkin as Cucumber executable SoT
- JSON keys English; item strings and Gherkin step prose in the **working language**; Gherkin keywords stay English ([working-language.md](references/working-language.md))

## Steps

1. Resolve active ChangeBrief via `.solidsdd/active-change.json` → `.solidsdd/changes/<change_id>/change-brief.json` (migrate legacy flat Brief if needed). Read change intent and context (`solidsdd-context` output if available). Resolve working language from project rule or Context §6.
2. If input is prose or incomplete Gherkin, normalize to Feature/Scenario form per [gherkin-requirements.md](references/gherkin-requirements.md) (create/update `.feature` under default layout when useful; new Scenarios for this Brief only, with coverage tags).
3. Apply slice rules in [work-decomposition.md](references/work-decomposition.md).
4. List items with id, intent, acceptance_criterion (property-level Gherkin Scenario), **`covers`** (Brief ids), depends_on, status (plus optional feature_path / scenario_name / confidence / human_gate) in the working language. Set WorkPlan `change_id`.
5. Set `acceptance_of_whole` for the final integration `solidsdd-verify` (align with Brief `success_criteria`). Ensure union of `covers` includes every `R*` / `SC*` id.
6. Apply gate rules in [human-gates.md](references/human-gates.md) when ambiguity warrants a gate.
7. Validate against [work-plan.schema.json](references/work-plan.schema.json).
8. Write JSON to `.solidsdd/changes/<change_id>/work-plan.json`.

## Output

JSON conforming to the WorkPlan schema, plus a one-paragraph summary and the WorkPlan path. Return these artifacts to the parent unchanged in meaning.

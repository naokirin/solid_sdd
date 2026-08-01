---
name: solidsdd-critique
description: >-
  Adversarial, read-only critique of a prior solid_sdd phase artifact (plan,
  contracts, derived tests, formal specs, or verification). When called from
  solidsdd-loop, must run as an explicit Task subagent. Emits CritiqueReport;
  does not edit artifacts. Analogous to SpecKit analyze/clarify quality gates.
license: MIT
---

# solidsdd.critique

## Execution

**subagent required** when invoked from `solidsdd.loop` (or any orchestrator chaining phases). Parent must use Task so the **producer of the artifact is not the evaluator**. Solo user invocation may run in the current agent.

## Purpose

Emit a `CritiqueReport` that adversarially evaluates another phase’s result—especially **contract weakness** (thin preconditions, missing error shapes, density bias, weak derived tests).

## References

- [critique-report.schema.json](references/critique-report.schema.json)
- [adversarial-critique.md](references/adversarial-critique.md)
- [loop-retry.md](references/loop-retry.md)
- [judgment-axes.md](references/judgment-axes.md)

## Constraints

- **Read-only**: do not modify ApplicationPlan, OpenAPI/GraphQL, OCL, tests, formal specs, or implementation
- Do not soften findings to keep the loop moving
- On fail, set `loop_action` and `suggested_next_skills` per [loop-retry.md](references/loop-retry.md)

## Inputs (from parent Task prompt)

- `subject`: one of the CritiqueReport `subject` enum values
- Paths / excerpts of the artifact under review
- Optional: change intent, context summary, ApplicationPlan (for density vs signals)

## Steps

1. Read [adversarial-critique.md](references/adversarial-critique.md) and apply the checklist for `subject`.
2. Inspect the artifact; list every adequacy failure as a finding (prefer over-reporting thin contracts).
3. Set `result` to `fail` if any finding is `blocker` or `major`; otherwise `pass`.
4. On fail, choose `suggested_next_skills` that own the defect at the **source** (re-judge / re-apply / re-derive—not implement to paper over weak specs).
5. Shape output per [critique-report.schema.json](references/critique-report.schema.json).

## Success criteria

- Findings are concrete (location + what is missing or too weak)
- Contract-weakness checklist was applied for contract/test subjects
- Failures are actionable for loop retry without parent rewriting artifacts

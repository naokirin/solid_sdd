---
name: solidsdd-critique
description: >-
  Adversarial, read-only critique of a prior solid_sdd phase artifact (change
  context, change brief, work plan, application plan, contracts, derived tests,
  formal specs, or verification). When called from solidsdd-loop or solidsdd-run,
  must run as an explicit Task subagent. Emits CritiqueReport; does not edit
  artifacts. Calibrated so only checkability holes fail the loop.
license: MIT
---

# solidsdd.critique

## Execution

**subagent required** when invoked from `solidsdd.loop`, `solidsdd.run`, or any orchestrator chaining phases. Parent must use Task so the **producer of the artifact is not the evaluator**. Solo user invocation may run in the current agent.

## Purpose

Emit a `CritiqueReport` that adversarially evaluates another phase’s result. Focus on **lost checkability** (missing `pre`, no API error path, tests that ignore existing `pre`, density vs signals). Polish stays `minor` so the loop can proceed.

## References

- [critique-report.schema.json](references/critique-report.schema.json)
- [adversarial-critique.md](references/adversarial-critique.md) — **severity calibration (required)**
- [gherkin-requirements.md](references/gherkin-requirements.md) — when `subject` is `work_plan`
- [change-brief.md](references/change-brief.md) — when `subject` is `change_brief`
- [change-context.md](references/change-context.md) — when `subject` is `change_context`
- [change-context-gate.schema.json](references/change-context-gate.schema.json) — when reviewing Change Context gate
- [loop-retry.md](references/loop-retry.md)
- [judgment-axes.md](references/judgment-axes.md)

When reviewing a ChangeBrief, resolve path via `.solidsdd/active-change.json` → `.solidsdd/changes/<change_id>/change-brief.json` unless the parent Task prompt gives an explicit path.

## Constraints

- **Read-only**: do not modify Change Context, ChangeBrief, WorkPlan, ApplicationPlan, OpenAPI/GraphQL, OCL, tests, formal specs, or implementation
- Do not inflate polish into `major` / `fail` (see severity calibration)
- Do not soft-pedal true checkability holes as `minor`
- On fail, set `loop_action` and `suggested_next_skills` per [loop-retry.md](references/loop-retry.md)

## Inputs (from parent Task prompt)

- `subject`: one of the CritiqueReport `subject` enum values
- Paths / excerpts of the artifact under review
- Optional: change intent, context summary, ApplicationPlan (for density vs signals)

## Steps

1. Read [adversarial-critique.md](references/adversarial-critique.md), especially **Severity calibration**.
2. Inspect the artifact; draft findings, then assign severity using the major vs not-major table.
3. Set `result` to `fail` only if any finding is `blocker` or `major`; otherwise `pass` (minors allowed).
4. On fail, choose `suggested_next_skills` that own the defect at the **source**.
5. Shape output per [critique-report.schema.json](references/critique-report.schema.json).

## Success criteria

- Findings are concrete (location + what is missing or too weak)
- Severity matches calibration (standard-density samples can `pass` with minors)
- Failures are actionable and worth consuming retry budget

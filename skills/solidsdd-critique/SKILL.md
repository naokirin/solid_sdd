---
name: solidsdd-critique
description: >-
  Adversarial, read-only critique of a prior solid_sdd phase artifact (change
  context, change brief, work plan, application plan, contracts, derived tests,
  formal specs, or verification). When called from solidsdd-loop or solidsdd-run,
  must run as an explicit Task subagent. Runs deterministic solidsdd-lint first,
  then LLM adequacy review. Emits CritiqueReport; does not edit artifacts.
  Calibrated so only checkability holes fail the loop.
license: MIT
---

# solidsdd.critique

## Execution

**subagent required** when invoked from `solidsdd.loop`, `solidsdd.run`, or any orchestrator chaining phases. Parent must use Task so the **producer of the artifact is not the evaluator**. Solo user invocation may run in the current agent.

## Purpose

Emit a `CritiqueReport` that adversarially evaluates another phase’s result. Run **deterministic lint first**, then focus LLM review on **lost checkability** (missing `pre`, no API error path, tests that ignore existing `pre`, density vs signals, adequacy of id coverage). Polish stays `minor` so the loop can proceed.

## References

- [critique-report.schema.json](references/critique-report.schema.json)
- [adversarial-critique.md](references/adversarial-critique.md) — **severity calibration + lint-first (required)**
- [working-language.md](references/working-language.md) — finding detail language
- [gherkin-requirements.md](references/gherkin-requirements.md) — when `subject` is `work_plan`
- [change-brief.md](references/change-brief.md) — when `subject` is `change_brief`
- [change-context.md](references/change-context.md) — when `subject` is `change_context`
- [change-context-gate.schema.json](references/change-context-gate.schema.json) — when reviewing Change Context gate
- [loop-retry.md](references/loop-retry.md)
- [judgment-axes.md](references/judgment-axes.md)
- [solidsdd-lint.md](references/solidsdd-lint.md) — deterministic lint before LLM review

When reviewing a ChangeBrief, resolve path via `.solidsdd/active-change.json` → `.solidsdd/changes/<change_id>/change-brief.json` unless the parent Task prompt gives an explicit path.

**Lint tooling** lives in the solid_sdd repository: `scripts/solidsdd-lint.sh` (see that repo’s `scripts/solidsdd-lint/README.md`). Prefer the path from the installed solid_sdd checkout or parent Task prompt.

## Constraints

- **Read-only**: do not modify Change Context, ChangeBrief, WorkPlan, ApplicationPlan, OpenAPI/GraphQL, OCL, tests, formal specs, or implementation
- Do not inflate polish into `major` / `fail` (see severity calibration)
- Do not soft-pedal true checkability holes as `minor`
- On fail, set `loop_action` and `suggested_next_skills` per [loop-retry.md](references/loop-retry.md)
- Finding `detail` strings use the **working language** ([working-language.md](references/working-language.md)); keys/enums stay English

## Inputs (from parent Task prompt)

- `subject`: one of the CritiqueReport `subject` enum values
- Paths / excerpts of the artifact under review
- Optional: change intent, context summary, ApplicationPlan (for density vs signals)
- Optional: absolute path to `scripts/solidsdd-lint.sh` or solid_sdd repo root

## Steps

1. Resolve working language from project rule or Change Context §6 when present. Read [adversarial-critique.md](references/adversarial-critique.md), especially **Deterministic lint first** and **Severity calibration**.
2. **Run lint** from the consuming project root:
   ```bash
   /path/to/solid_sdd/scripts/solidsdd-lint.sh --project-root . --pretty
   ```
   Capture JSON. Map each lint finding into CritiqueReport `findings` (severity unchanged; map `schema_violation` → category `consistency` or `other`; `scope_gap` / `unverifiable_acceptance` / `consistency` map when they match CritiqueReport enums, else `other`).
3. Inspect the artifact with LLM review for **adequacy** (not re-deriving coverage existence). Draft additional findings; assign severity using the major vs not-major table.
4. Set `result` to `fail` only if any finding is `blocker` or `major`; otherwise `pass` (minors allowed).
5. On fail, choose `suggested_next_skills` that own the defect at the **source** ([loop-retry.md](references/loop-retry.md)).
6. Shape output per [critique-report.schema.json](references/critique-report.schema.json). When the parent supplies an output path (e.g. `items/<id>/critique-application-plan.json`), **write** the CritiqueReport there.
7. Return the report to the parent unchanged in meaning.

## Success criteria

- Lint ran (or tooling gap explicitly recorded) before LLM review
- Findings are concrete (location + what is missing or too weak)
- Severity matches calibration (standard-density samples can `pass` with minors)
- Failures are actionable and worth consuming retry budget

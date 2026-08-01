---
name: solidsdd-loop
description: >-
  Orchestrate solid_sdd as the parent agent only: run context locally, and
  launch judge/critique/apply/derive/implement/verify (and Phase 3 formal
  skills) as explicit Task subagents. Honors human_gate, CritiqueReport, and
  verification loop_action with a shared auto-retry budget.
license: MIT
---

# solidsdd.loop

## Purpose

Run the full loop. This skill is **orchestrator-only** — do not delegate `solidsdd.loop` itself to a subagent.

## References

- [execution-model.md](references/execution-model.md) — orchestrator / subagent / critique rules
- [adversarial-critique.md](references/adversarial-critique.md) — when and how to critique phase outputs
- [human-gates.md](references/human-gates.md) — when to stop for a person
- [loop-retry.md](references/loop-retry.md) — verify/critique failure → retry / gate / stop
- [contract-layout.md](references/contract-layout.md) — default artifact paths
- [project-rule.mdc](references/project-rule.mdc) — copy into `.cursor/rules/` (or equivalent) once per project

## Execution policy

| Step | How |
|------|-----|
| `solidsdd-context` | Parent agent (this conversation) |
| `solidsdd-judge`, `solidsdd-critique`, `solidsdd-apply-api`, `solidsdd-apply-dbc`, `solidsdd-derive-tests`, `solidsdd-implement`, `solidsdd-verify`, `solidsdd-apply-formal`, `solidsdd-verify-formal` | **Required subagent** via Task tool (or equivalent) |

Never execute a subagent-required skill's procedure in the parent. Do not rewrite an `ApplicationPlan` or thin a `CritiqueReport`—re-run the owning skill as a subagent if wrong.

## Sequence

1. Parent: `solidsdd-context`
2. **Task subagent** `solidsdd-judge` → ApplicationPlan
3. **Task subagent** `solidsdd-critique` with `subject: application_plan`
4. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-judge as Task, then critique again)
5. If plan or any target has `human_gate.required: true` → **stop** (see [human-gates.md](references/human-gates.md)); do not apply until humans approve
6. After explicit approval, **resume** from the interrupted step (do not thin the plan); see resume protocol in [human-gates.md](references/human-gates.md)
7. For each `status=apply` target, **Task subagent**:
   - `api` → `solidsdd-apply-api` (honor `adapter_hint`: `openapi` or `graphql`) then **Task** `solidsdd-critique` (`subject: api_contracts`)
   - `dbc` → `solidsdd-apply-dbc` then **Task** `solidsdd-critique` (`subject: dbc_contracts`)
   - `formal` → only after gate approval → `solidsdd-apply-formal` then **Task** `solidsdd-critique` (`subject: formal_specs`) (may run after or beside the API/DbC path; do not block API/DbC on formal `defer`)
8. If OCL changed → **Task subagent** `solidsdd-derive-tests` then **Task** `solidsdd-critique` (`subject: derived_tests`)
9. **Task subagent** `solidsdd-implement` (API/DbC implementation)
10. **Task subagent** `solidsdd-verify` then **Task** `solidsdd-critique` (`subject: verification_report`)
11. If formal artifacts were applied → **Task subagent** `solidsdd-verify-formal` then **Task** `solidsdd-critique` (`subject: verification_report`)
12. On verify or critique failure, follow [loop-retry.md](references/loop-retry.md):
    - `loop_action: retry` → re-run suggested skills as **new subagents**, then the relevant critique/verify (shared **max_auto_retries = 3**)
    - `loop_action: human_gate` or `stop` → end loop with report
    - Same suggested skill twice with no progress → escalate to human gate
    - Retry budget exhausted → human gate (no infinite loop)
13. If the parent discovers it ran a subagent-required skill inline → treat as isolation violation: feedback via critique/`isolation`, **re-run that skill as Task**, consume retry budget
14. Leave `formal`/`defer` and unmet human gates visible in the final summary—do not hide them

## Isolation checklist (required in final summary)

List each required Task launch with skill id + critique `subject` when applicable. Example rows: `judge`, `critique(application_plan)`, `apply-api`, `critique(api_contracts)`, … Mark any inline execution as a violation that was re-run or gated.

## Subagent prompt requirements

Each Task prompt must include:

- Skill id and path to the installed `solidsdd-*/SKILL.md`
- Working directory (consuming project root)
- Inputs (context summary, ApplicationPlan excerpt, critique `subject`, changed OCL paths, etc.)
- Constraint: only that skill's allowed edits; follow that skill's `references/`
- Expected return: summary, changed files, plan/report artifacts

## Success criteria

- Subagent-required steps were not run inline in the parent (or were detected, re-run via Task, and counted)
- Each producer step that ran had its matching `solidsdd-critique` Task
- ApplicationPlan / CritiqueReports came from subagents without parent thinning
- Human gates honored before apply (including formal early-rollout policy)
- Verification and critiques pass, or stop with clear `loop_action` / human-gate reason within the retry budget
- Final summary includes the isolation checklist
- Artifacts remain consistent with the plan

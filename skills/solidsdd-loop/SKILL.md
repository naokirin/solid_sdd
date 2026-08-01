---
name: solidsdd-loop
description: >-
  Orchestrate solid_sdd as the parent agent only: run context locally, and
  launch judge/apply/derive/implement/verify (and Phase 3 formal skills) as
  explicit subagents via Task. Honors human_gate and verification loop_action.
license: MIT
---

# solidsdd.loop

## Purpose

Run the full loop. This skill is **orchestrator-only** — do not delegate `solidsdd.loop` itself to a subagent.

## References

- [execution-model.md](references/execution-model.md) — orchestrator / subagent rules
- [human-gates.md](references/human-gates.md) — when to stop for a person
- [loop-retry.md](references/loop-retry.md) — verify failure → retry / gate / stop
- [contract-layout.md](references/contract-layout.md) — default artifact paths
- [project-rule.mdc](references/project-rule.mdc) — copy into `.cursor/rules/` (or equivalent) once per project

## Execution policy

| Step | How |
|------|-----|
| `solidsdd-context` | Parent agent (this conversation) |
| `solidsdd-judge`, `solidsdd-apply-api`, `solidsdd-apply-dbc`, `solidsdd-derive-tests`, `solidsdd-implement`, `solidsdd-verify`, `solidsdd-apply-formal`, `solidsdd-verify-formal` | **Required subagent** via Task tool (or equivalent) |

Never execute a subagent-required skill's procedure in the parent. Do not rewrite an `ApplicationPlan` from `solidsdd-judge` to thin contracts—re-run `solidsdd-judge` as a subagent if the plan is wrong.

## Sequence

1. Parent: `solidsdd-context`
2. **Task subagent** `solidsdd-judge` → ApplicationPlan
3. If plan or any target has `human_gate.required: true` → **stop** (see [human-gates.md](references/human-gates.md)); do not apply until humans approve
4. For each `status=apply` target, **Task subagent**:
   - `api` → `solidsdd-apply-api` (honor `adapter_hint`: `openapi` or `graphql`)
   - `dbc` → `solidsdd-apply-dbc`
   - `formal` → only after gate approval → `solidsdd-apply-formal` (may run after or beside the API/DbC path; do not block API/DbC on formal `defer`)
5. If OCL changed → **Task subagent** `solidsdd-derive-tests`
6. **Task subagent** `solidsdd-implement` (API/DbC implementation)
7. **Task subagent** `solidsdd-verify`
8. If formal artifacts were applied → **Task subagent** `solidsdd-verify-formal`
9. On failure, follow [loop-retry.md](references/loop-retry.md):
   - `loop_action: retry` → re-run suggested skills as **new subagents**, then verify (max 3 verify-fail retries)
   - `loop_action: human_gate` or `stop` → end loop with report
   - Same suggested skill twice with no progress → escalate to human gate
10. Leave `formal`/`defer` and unmet human gates visible in the final summary—do not hide them

## Subagent prompt requirements

Each Task prompt must include:

- Skill id and path to the installed `solidsdd-*/SKILL.md`
- Working directory (consuming project root)
- Inputs (context summary, ApplicationPlan excerpt, changed OCL paths, etc.)
- Constraint: only that skill's allowed edits; follow that skill's `references/`
- Expected return: summary, changed files, plan/report artifacts

## Success criteria

- Subagent-required steps were not run inline in the parent
- ApplicationPlan came from the judge subagent without parent thinning
- Human gates honored before apply (including formal early-rollout policy)
- Verification passes, or stops with clear `loop_action` / human-gate reason
- Artifacts remain consistent with the plan

---
name: solidsdd-loop
description: >-
  Orchestrate solid_sdd as the parent agent only: run context locally, and
  launch judge/apply/derive/implement/verify as explicit subagents via Task.
  Use for autonomous SDD loops.
license: MIT
---

# solidsdd.loop

## Purpose

Run the full MVP loop. This skill is **orchestrator-only** — do not delegate `solidsdd.loop` itself to a subagent.

## References

- [execution-model.md](references/execution-model.md) — orchestrator / subagent rules
- [contract-layout.md](references/contract-layout.md) — default artifact paths
- [project-rule.mdc](references/project-rule.mdc) — copy into `.cursor/rules/` (or equivalent) once per project

## Execution policy

| Step | How |
|------|-----|
| `solidsdd-context` | Parent agent (this conversation) |
| `solidsdd-judge`, `solidsdd-apply-api`, `solidsdd-apply-dbc`, `solidsdd-derive-tests`, `solidsdd-implement`, `solidsdd-verify` | **Required subagent** via Task tool (or equivalent) |

Never execute a subagent-required skill's procedure in the parent. Do not rewrite an `ApplicationPlan` from `solidsdd-judge` to thin contracts—re-run `solidsdd-judge` as a subagent if the plan is wrong. Read [references/execution-model.md](references/execution-model.md).

## Sequence

1. Parent: `solidsdd-context`
2. **Task subagent** `solidsdd-judge` → ApplicationPlan
3. For each `status=apply` target, **Task subagent**:
   - `api` → `solidsdd-apply-api`
   - `dbc` → `solidsdd-apply-dbc`
4. If OCL changed → **Task subagent** `solidsdd-derive-tests`
5. **Task subagent** `solidsdd-implement`
6. **Task subagent** `solidsdd-verify`
7. On failure, retry the suggested skill as a **new subagent** (max 3 loops unless rules say otherwise)
8. Leave `formal`/`defer` items visible in the final summary—do not hide them

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
- Verification passes, or stops with a clear blocker and human-gate reason
- Artifacts (OpenAPI, OCL, tests, code) remain consistent with the plan

---
name: sdd-loop
description: >-
  Orchestrate solid_sdd as the parent agent only: run context/judge locally,
  and launch apply/derive/implement/verify as explicit subagents via Task.
  Use for autonomous SDD loops.
---

# sdd.loop

## Purpose

Run the full MVP loop. This skill is **orchestrator-only** — do not delegate `sdd.loop` itself to a subagent.

## Execution policy

| Step | How |
|------|-----|
| `sdd-context`, `sdd-judge` | Parent agent (this conversation) |
| `sdd-apply-api`, `sdd-apply-dbc`, `sdd-derive-tests`, `sdd-implement`, `sdd-verify` | **Required subagent** via Task tool (or equivalent) |

Never execute a subagent-required skill's procedure in the parent. Read [docs/execution-model.md](../../docs/execution-model.md).

## Sequence

1. Parent: `sdd-context`
2. Parent: `sdd-judge` → ApplicationPlan
3. For each `status=apply` target, **Task subagent**:
   - `api` → `sdd-apply-api`
   - `dbc` → `sdd-apply-dbc`
4. If OCL changed → **Task subagent** `sdd-derive-tests`
5. **Task subagent** `sdd-implement`
6. **Task subagent** `sdd-verify`
7. On failure, retry the suggested skill as a **new subagent** (max 3 loops unless rules say otherwise)
8. Leave `formal`/`defer` items visible in the final summary—do not hide them

## Subagent prompt requirements

Each Task prompt must include:

- Skill id and path to `skills/<dir>/SKILL.md`
- Working directory
- Inputs (ApplicationPlan excerpt, changed OCL paths, etc.)
- Constraint: only that skill's allowed edits
- Expected return: summary, changed files, plan/report artifacts

## Success criteria

- Subagent-required steps were not run inline in the parent
- Verification passes, or stops with a clear blocker and human-gate reason
- Artifacts (OpenAPI, OCL, tests, code) remain consistent with the plan

---
name: solidsdd-loop
description: >-
  Orchestrate solid_sdd as the slice parent only: run context locally, and
  launch judge/critique/apply/derive/implement/verify (and Phase 3 formal
  skills) as explicit Task subagents. Persists ApplicationPlan / critiques /
  verification under items/<id>/ and honors run-state retry budgets. For
  multi-criterion requirements use solidsdd-run.
license: MIT
---

# solidsdd.loop

## Purpose

Run the **slice** loop for one change intent (typically one verifiable acceptance criterion). This skill is **orchestrator-only** — do not delegate `solidsdd.loop` itself to a subagent.

For multi-criterion requirements, use **`solidsdd-run`** (decompose → WorkPlan → this loop per item → integration verify). Do not expand this skill into work decomposition.

## References

- [execution-model.md](references/execution-model.md) — orchestrator / subagent / critique rules
- [adversarial-critique.md](references/adversarial-critique.md) — when and how to critique phase outputs
- [human-gates.md](references/human-gates.md) — when to stop for a person
- [loop-retry.md](references/loop-retry.md) — verify/critique failure → retry / gate / stop
- [contract-layout.md](references/contract-layout.md) — default artifact paths
- [run-state.md](references/run-state.md) — **persist plans / critiques / retry budget (required)**; use `solidsdd-run-state` CLI (no free-form Python)
- [run-state.schema.json](references/run-state.schema.json)
- [run-cost.md](references/run-cost.md) — isolation; **allowed cost skips B1–B5**; context pack; host toolchain thrash vs cost
- [project-rule.mdc](references/project-rule.mdc) — copy into `.cursor/rules/` (or equivalent) once per project
- [host-toolchain.md](references/host-toolchain.md) — preflight; paste commands into Tasks

## Execution policy

| Step | How |
|------|-----|
| `solidsdd-context` | Parent agent (this conversation) |
| Context pack write / B1 mechanical critique / B3 skip implement | Parent (per [run-cost.md](references/run-cost.md)); record `cost_skip:B*` |
| `solidsdd-judge`, `solidsdd-critique`, `solidsdd-apply-api`, `solidsdd-apply-dbc`, `solidsdd-derive-tests`, `solidsdd-implement`, `solidsdd-verify`, `solidsdd-apply-formal`, `solidsdd-verify-formal` | **Required subagent** via Task tool (or equivalent), except when a documented cost skip or Consolidated Slice Execution applies |

### Consolidated Slice Mode (Preferred per cost-reduction-plan.md)

Orchestrators may execute the slice loop using the **Consolidated Slice Model** to reduce Task launch count and overhead:
1. **Plan Slice Task**: Combines `solidsdd-judge`, `apply-api`/`apply-dbc` contract design, and `derive-tests` into one Task.
2. **Implement Slice Task**: Applies implementation code updates.
3. **Verify Slice Task**: Runs verification checks.
4. **Checkpoint & Failure-Driven Critique**: Runs Critique at major Specification/WorkPlan/Integration boundaries, or on Verification failure.

Never execute a subagent-required skill's procedure in the parent **except** documented mechanical substitutes (B1 lint→critique JSON). Do not rewrite an `ApplicationPlan` or thin a producer’s LLM `CritiqueReport`—re-run the owning skill as a subagent if wrong.

**Persist** under `.solidsdd/changes/<change_id>/items/<item_id>/` (caller supplies `item_id`; default `ad-hoc` only for solo loops). Update the parent `run-state.json` item entry (`loop_phase`, `loop_retry`, `status`) at each step boundary via **`scripts/solidsdd-run-state.sh`** (e.g. `set-item`, `set-phase`, `note`, `record-metrics`). Do **not** use free-form `python -c` / unbounded heredoc for run-state.

## Sequence

1. Resolve `change_id` / `item_id` / artifact dir from the caller (or active change + `items/ad-hoc`). Read `run-state.json` when present; if this item’s `loop_phase` is mid-slice and artifacts exist, **resume** from that phase.
2. Parent: `solidsdd-context` (include **Toolchain** from `scripts/solidsdd-host-toolchain.sh` / `.solidsdd/host-toolchain.json`; copy into `run-state.host_toolchain` when persisting)
2b. Parent: write **`items/<id>/context-pack.md`** ([execution-model.md](references/execution-model.md) — Context pack); refresh after apply/implement if listed files changed materially
3. **Task subagent** `solidsdd-judge` → write `application-plan.json` into the item dir (include `change_id` / `covers` when known); update context-pack with target table
4. **Critique application_plan:** if all targets are `skip`/`defer` only → **B1** mechanical lint critique (no LLM Task); else **Task** `solidsdd-critique` (`subject: application_plan`) → `critique-application-plan.json`
5. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-judge as Task, then critique again); decrement `items.<id>.loop_retry.remaining` in `run-state.json`
6. If plan or any target has `human_gate.required: true` → **stop** (see [human-gates.md](references/human-gates.md)); do not apply until humans approve; persist `blocked` / `stopped` in run-state
7. After explicit approval, **resume** from the interrupted `loop_phase` using the on-disk plan (do not thin the plan); see resume protocol in [human-gates.md](references/human-gates.md)
8. For each `status=apply` target, **Task subagent**:
   - `api` → `solidsdd-apply-api` (honor `adapter_hint`: `openapi` or `graphql`) then **Task** `solidsdd-critique` (`subject: api_contracts`) → `critique-api-contracts.json`
   - `dbc` → `solidsdd-apply-dbc` then **Task** `solidsdd-critique` (`subject: dbc_contracts`) → `critique-dbc-contracts.json`
   - `formal` → only after gate approval → `solidsdd-apply-formal` then **Task** `solidsdd-critique` (`subject: formal_specs`) → `critique-formal-specs.json` (may run after or beside the API/DbC path; do not block API/DbC on formal `defer`)
   - **B2:** do not launch critique subjects for apply/derive kinds that did not run
9. If OCL changed → **Task subagent** `solidsdd-derive-tests` then **Task** `solidsdd-critique` (`subject: derived_tests`) → `critique-derived-tests.json`
10. **Implement:** if **B3** (no implementation `touches` and no apply implying implement) → skip Task and note `cost_skip:B3`; else **Task** `solidsdd-implement`
11. **Task subagent** `solidsdd-verify` → write `verification-report.json` (**B5:** may cite prior same-suite green verify instead of re-running full tests when this item edited no code/contract-tests); then **Task** `solidsdd-critique` (`subject: verification_report`) → `critique-verification-report.json`
12. If formal artifacts were applied → **Task subagent** `solidsdd-verify-formal` then **Task** `solidsdd-critique` (`subject: verification_report`)
13. On verify or critique failure, follow [loop-retry.md](references/loop-retry.md):
    - `loop_action: retry` → re-run suggested skills as **new subagents**, then the relevant critique/verify (shared **`loop_retry`**, max 3)
    - `loop_action: human_gate` or `stop` → end loop with report; update run-state
    - Same suggested skill twice with no progress → escalate to human gate
    - Retry budget exhausted (`remaining` 0) → human gate (no infinite loop)
14. If the parent discovers it ran a subagent-required skill inline → treat as isolation violation: feedback via critique/`isolation`, **re-run that skill as Task**, consume retry budget
15. On success set item `status: done`, `loop_phase: done` in `run-state.json` (prefer `solidsdd-run-state set-item --id <id> --status done --loop-phase done [--sync-work-plan]`). Leave `formal`/`defer` and unmet human gates visible in the final summary—do not hide them

## Isolation checklist (required in final summary)

List each required Task launch **or** `cost_skip:B*` substitute with skill id + critique `subject` when applicable. Example rows: `toolchain(ready|gap)`, `context-pack`, `judge`, `critique(application_plan)|cost_skip:B1`, `apply-api`, … Append notes to `run-state.isolation_notes` when under `solidsdd-run` (including `toolchain_rediscovery:<tool>:<reason>`, `cost_skip:B*`).

## Subagent prompt requirements

Each Task prompt must include:

- Skill id and path to the installed `solidsdd-*/SKILL.md`
- Working directory (consuming project root)
- **Context pack path** — prefer pack; avoid re-reading full SoT files unless editing them or pack is stale ([execution-model.md](references/execution-model.md))
- Inputs (context summary, ApplicationPlan path under `items/<id>/`, critique `subject`, changed OCL paths, etc.)
- **Toolchain commands** from context / `.solidsdd/host-toolchain.json` for verify / implement / derive / shell npm|node|bundle — use only those; **do not** filesystem-search for tools ([host-toolchain.md](references/host-toolchain.md))
- Constraint: only that skill's allowed edits; follow that skill's `references/`
- Expected return: summary, changed files, and **paths** of written plan/report JSON under the item dir

## Success criteria

- Subagent-required steps were not run inline in the parent (or were detected, re-run via Task, and counted), except documented B1 mechanical critique
- Each producer step that ran had its matching `solidsdd-critique` Task **or** an allowed cost skip recorded
- ApplicationPlan / CritiqueReports / VerificationReport / context-pack were **written under `items/<id>/`**, not left only in chat
- `loop_retry.remaining` in `run-state.json` matches consumed retries
- Human gates honored before apply (including formal early-rollout policy)
- Verification and critiques pass, or stop with clear `loop_action` / human-gate reason within the retry budget
- Final summary includes the isolation checklist (including `toolchain(ready|gap)` and any `cost_skip:B*`)
- Artifacts remain consistent with the plan
- Host tools were not rediscovered when Toolchain commands were available (or rediscovery was recorded)

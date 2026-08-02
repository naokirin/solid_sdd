---
name: solidsdd-run
description: >-
  Outer orchestrator for solid_sdd: produce Change Context and ChangeBrief,
  decompose into a WorkPlan, run solidsdd-loop once per item, then integration
  solidsdd-verify. Parent only — do not delegate solidsdd-run itself. Use for
  multi-criterion work; use solidsdd-loop alone for a single known slice.
license: MIT
---

# solidsdd.run

## Purpose

Drive **requirement → Change Context → ChangeBrief → WorkPlan → per-slice loop → integration verify**. This skill is **orchestrator-only** — do not delegate `solidsdd.run` itself to a subagent.

`solidsdd-loop` stays the **slice** orchestrator (one change intent / one Gherkin Scenario). Do not re-implement loop phases inside `solidsdd-run`.

## References

- [execution-model.md](references/execution-model.md) — orchestrator / subagent / critique rules
- [change-context.md](references/change-context.md) — demand / NFR / tech selection (fixed Markdown)
- [change-brief.md](references/change-brief.md) — scope premise (return point)
- [change-lifecycle.md](references/change-lifecycle.md) — active change paths / additional requirements
- [change-brief.schema.json](references/change-brief.schema.json)
- [active-change.schema.json](references/active-change.schema.json)
- [change-status.schema.json](references/change-status.schema.json)
- [work-decomposition.md](references/work-decomposition.md) — slice rules for WorkPlan
- [gherkin-requirements.md](references/gherkin-requirements.md) — property-level Gherkin
- [work-plan.schema.json](references/work-plan.schema.json)
- [adversarial-critique.md](references/adversarial-critique.md) — including `subject: change_context` / `change_brief` / `work_plan`
- [human-gates.md](references/human-gates.md)
- [loop-retry.md](references/loop-retry.md) — verify/critique failure → retry / gate / stop
- [contract-layout.md](references/contract-layout.md)
- [run-state.md](references/run-state.md) — **persist phase / retries / item artifacts (required)**
- [run-state.schema.json](references/run-state.schema.json)
- [project-rule.mdc](references/project-rule.mdc) — copy into `.cursor/rules/` (or equivalent) once per project

## Execution policy

| Step | How |
|------|-----|
| `solidsdd-context` | Parent agent (this conversation) |
| `solidsdd-intake`, `solidsdd-brief`, `solidsdd-decompose`, `solidsdd-critique`, `solidsdd-verify` (integration), `solidsdd-verify-formal` (if needed) | **Required subagent** via Task |
| Each WorkPlan item | Invoke **`solidsdd-loop`** as the slice orchestrator (same parent session following that skill — do not inline judge/apply/implement inside `solidsdd-run`) |

Never execute a subagent-required skill’s procedure in the parent. Do not rewrite Change Context / `ChangeBrief` / `WorkPlan` or thin a `CritiqueReport`—re-run the owning skill as a subagent if wrong.

**Persist:** maintain `.solidsdd/changes/<change_id>/run-state.json` (read at step start, write at step end). Outer critique/verify JSON may live under the change directory; per-item plans/reports under `items/<item_id>/` ([run-state.md](references/run-state.md)).

## Sequence

1. Parent: `solidsdd-context` (include existing Features/contracts and any `.solidsdd/active-change.json` / `run-state.json`)
2. If `run-state.json` exists with `phase` not `done` and `status.json` is `active` → **resume** from that phase (skip completed outer steps; do not re-invent Brief/WorkPlan unless critique failed).
3. **Task subagent** `solidsdd-intake` → `change-context.md` + `change-context-gate.json` under `.solidsdd/changes/<change_id>/` (pass optional user `change_id`; creates lifecycle paths — [change-lifecycle.md](references/change-lifecycle.md)). Create initial `run-state.json` (`phase: intake`, `run_retry` remaining 3).
4. **Task subagent** `solidsdd-critique` with `subject: change_context`; persist critique; update `phase` / `run_retry` as needed
5. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-intake as Task, then critique again); decrement `run_retry.remaining`
6. If `change-context-gate.json` has `human_gate.required: true` → **stop** until humans approve (or amend + re-intake); write `stopped_reason`; then resume without thinning Change Context — [human-gates.md](references/human-gates.md). Optionally suggest manual `solidsdd-report` for a readable snapshot (not a required gate).
7. **Task subagent** `solidsdd-brief` → ChangeBrief for the **same** active `change_id` (must read Change Context; migrate legacy flat Brief if needed); set `phase: brief`
8. **Task subagent** `solidsdd-critique` with `subject: change_brief`
9. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-brief; re-intake if framing is wrong)
10. If ChangeBrief has `human_gate.required: true` → **stop** until humans approve; then resume without thinning the brief
11. **Task subagent** `solidsdd-decompose` → WorkPlan at `.solidsdd/changes/<change_id>/work-plan.json` (must read active ChangeBrief as scope authority). Initialize `run-state.items` from WorkPlan (`ready`/`pending`, each with `loop_retry` max 3, `artifact_dir: items/<id>`).
12. **Task subagent** `solidsdd-critique` with `subject: work_plan`
13. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-decompose; re-brief / re-intake if premise is wrong)
14. When prior Features / prior `.solidsdd/changes/*/out_of_scope` exist → **Task subagent** `solidsdd-critique` with `subject: cross_change_consistency` (recommended); on fail → re-brief / re-decompose as suggested
15. If WorkPlan or any item has `human_gate.required: true` → **stop** until humans approve (write `gate-approval.json` before resume — [human-gates.md](references/human-gates.md)); then resume without thinning the plan
16. While items remain, run **waves** of independent loops (`phase: waves`, bump `wave_index`):
   - Promote any `pending` → `ready` when all `depends_on` are `done` (update both WorkPlan and `run-state.items`)
   - Collect **all** currently `ready` items as the wave (empty → if `pending`/`blocked` remain, stop with dependency / gate report; else proceed to integration)
   - Mark wave items `running` in `run-state`; launch **`solidsdd-loop` for every item in the wave in parallel** (same parent turn). Pass `item_id` and `items/<id>/` as the persistence root
   - Each loop uses that item’s `intent`, ChangeBrief + Change Context excerpts for scope/tech, its own Task subagents, and **`items.<id>.loop_retry`** (not chat memory)
   - After **all** loops in the wave finish: mark each `done` or `blocked` in WorkPlan + `run-state`; on human_gate/stop for an item, leave siblings’ results intact and decide whether to end the run or continue remaining waves
   - Then form the next wave from newly unblocked items
   - **Serialize when `touches` intersect**: if two+ ready items list overlapping paths in `touches` (set intersection non-empty), run those contending items sequentially within the wave; still parallelize non-contending ready items. If `touches` is missing, fall back to the legacy heuristic (“clearly contend on the same primary edit paths”) and prefer adding `touches` on re-decompose.
17. After all items `done` (or single-item plan finished its one loop):
   - **Task subagent** `solidsdd-verify` over the whole workspace / `acceptance_of_whole` (and Brief `success_criteria` when relevant); write `integration-verification-report.json`
   - **Task subagent** `solidsdd-critique` (`subject: verification_report`); persist critique
   - If formal artifacts were applied across slices → **Task** `solidsdd-verify-formal` then critique as in loop
   - On successful integration: set `.solidsdd/changes/<change_id>/status.json` to `"status": "done"` and `run-state.phase` to `done`
18. On integration verify or critique failure, follow [loop-retry.md](references/loop-retry.md) with **`run_retry`** (**max_auto_retries = 3**, separate from each slice loop’s budget): prefer re-running the owning slice’s loop or suggested skills as Task—not parent edits
19. Leave unmet gates and blocked items visible in the final summary (and in `run-state.json`)

## Isolation checklist (required in final summary)

List: `intake`, `critique(change_context)`, `[gate if required]`, `brief`, `critique(change_brief)`, `decompose`, `critique(work_plan)`, `[critique(cross_change_consistency) when applicable]`, each wave with item ids → parallel `loop` (and note that each loop’s own isolation checklist applies; note any serialize-for-contention), `verify` (integration), `critique(verification_report)`, plus formal steps if any. Mark inline execution of subagent-required skills as violations. Persist notable notes on `run-state.isolation_notes`.

## Subagent / loop prompt requirements

### Intake / brief / decompose / critique / integration verify

Each Task prompt must include skill id, `SKILL.md` path, working directory, inputs, constraints, expected return (same pattern as `solidsdd-loop`). For brief and later steps, include Change Context and ChangeBrief paths. Tell critique/verify where to **write** JSON when under this change.

### Per-item loop

When starting `solidsdd-loop` for an item, provide:

- Skill path to `solidsdd-loop/SKILL.md`
- Working directory (consuming project root)
- **Change intent** = that item’s `intent`
- **`item_id`** and artifact directory `.solidsdd/changes/<change_id>/items/<item_id>/`
- The item’s `acceptance_criterion` (Gherkin Scenario; for verify focus) and `covers`
- Optional `feature_path` / `scenario_name` when present
- Change Context path/excerpt (§4 NFR / §5 tech when relevant)
- ChangeBrief path/excerpt (in/out of scope)
- Context summary and WorkPlan excerpt (item id + depends)
- Instruction to read/write that item’s `loop_retry` via parent-updated `run-state.json`
- Note that sibling loops in the **same wave** may run concurrently; keep edits scoped to this item’s intent

## Success criteria

- Subagent-required steps were not run inline in the parent (or were re-run via Task and counted)
- `run-state.json` reflects phase, waves, and retry remaining after each step
- Change Context came from intake without parent thinning; `critique(change_context)` ran; Change Context gate honored when `required`
- ChangeBrief came from brief without parent thinning; `critique(change_brief)` ran
- WorkPlan came from decompose without parent thinning; `critique(work_plan)` ran
- Each done item had a `solidsdd-loop` run scoped to its intent with persisted plans under `items/<id>/`
- Independent `ready` items in a wave were started **in parallel** (or serialized only with an explicit contention reason)
- Integration `solidsdd-verify` (+ critique) ran after all items (or after the single item)
- Human gates honored; final summary includes the isolation checklist, wave grouping, and any blocked items

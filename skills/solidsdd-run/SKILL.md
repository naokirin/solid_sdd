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
- [project-rule.mdc](references/project-rule.mdc) — copy into `.cursor/rules/` (or equivalent) once per project

## Execution policy

| Step | How |
|------|-----|
| `solidsdd-context` | Parent agent (this conversation) |
| `solidsdd-intake`, `solidsdd-brief`, `solidsdd-decompose`, `solidsdd-critique`, `solidsdd-verify` (integration), `solidsdd-verify-formal` (if needed) | **Required subagent** via Task |
| Each WorkPlan item | Invoke **`solidsdd-loop`** as the slice orchestrator (same parent session following that skill — do not inline judge/apply/implement inside `solidsdd-run`) |

Never execute a subagent-required skill’s procedure in the parent. Do not rewrite Change Context / `ChangeBrief` / `WorkPlan` or thin a `CritiqueReport`—re-run the owning skill as a subagent if wrong.

## Sequence

1. Parent: `solidsdd-context` (include existing Features/contracts and any `.solidsdd/active-change.json`)
2. **Task subagent** `solidsdd-intake` → `change-context.md` + `change-context-gate.json` under `.solidsdd/changes/<change_id>/` (pass optional user `change_id`; creates lifecycle paths — [change-lifecycle.md](references/change-lifecycle.md))
3. **Task subagent** `solidsdd-critique` with `subject: change_context`
4. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-intake as Task, then critique again)
5. If `change-context-gate.json` has `human_gate.required: true` → **stop** until humans approve (or amend + re-intake); then resume without thinning Change Context — [human-gates.md](references/human-gates.md). Optionally suggest manual `solidsdd-report` for a readable snapshot (not a required gate).
6. **Task subagent** `solidsdd-brief` → ChangeBrief for the **same** active `change_id` (must read Change Context; migrate legacy flat Brief if needed)
7. **Task subagent** `solidsdd-critique` with `subject: change_brief`
8. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-brief; re-intake if framing is wrong)
9. If ChangeBrief has `human_gate.required: true` → **stop** until humans approve; then resume without thinning the brief
10. **Task subagent** `solidsdd-decompose` → WorkPlan at `.solidsdd/changes/<change_id>/work-plan.json` (must read active ChangeBrief as scope authority)
11. **Task subagent** `solidsdd-critique` with `subject: work_plan`
12. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-decompose; re-brief / re-intake if premise is wrong)
13. If WorkPlan or any item has `human_gate.required: true` → **stop** until humans approve; then resume without thinning the plan
14. While items remain, run **waves** of independent loops:
   - Promote any `pending` → `ready` when all `depends_on` are `done`
   - Collect **all** currently `ready` items as the wave (empty → if `pending`/`blocked` remain, stop with dependency / gate report; else proceed to integration)
   - Launch **`solidsdd-loop` for every item in the wave in parallel** (same parent turn: concurrent Task / concurrent loop sessions). Do **not** wait for one ready item before starting another in the same wave
   - Each loop uses that item’s `intent`, ChangeBrief + Change Context excerpts for scope/tech, its own Task subagents, and its own retry budget
   - After **all** loops in the wave finish: mark each `done` or `blocked`; on human_gate/stop for an item, leave siblings’ results intact and decide whether to end the run or continue remaining waves
   - Then form the next wave from newly unblocked items
   - **Serialize only when necessary**: if two+ ready items would clearly contend on the same primary edit paths (e.g. both rewriting the same OpenAPI SoT as the main deliverable), run those contending items sequentially within the wave; still parallelize non-contending ready items
15. After all items `done` (or single-item plan finished its one loop):
   - **Task subagent** `solidsdd-verify` over the whole workspace / `acceptance_of_whole` (and Brief `success_criteria` when relevant)
   - **Task subagent** `solidsdd-critique` (`subject: verification_report`)
   - If formal artifacts were applied across slices → **Task** `solidsdd-verify-formal` then critique as in loop
   - On successful integration: set `.solidsdd/changes/<change_id>/status.json` to `"status": "done"`
16. On integration verify or critique failure, follow [loop-retry.md](references/loop-retry.md) with a **run-level** auto-retry budget (**max_auto_retries = 3**, separate from each slice loop’s budget): prefer re-running the owning slice’s loop or suggested skills as Task—not parent edits
17. Leave unmet gates and blocked items visible in the final summary

## Isolation checklist (required in final summary)

List: `intake`, `critique(change_context)`, `[gate if required]`, `brief`, `critique(change_brief)`, `decompose`, `critique(work_plan)`, each wave with item ids → parallel `loop` (and note that each loop’s own isolation checklist applies; note any serialize-for-contention), `verify` (integration), `critique(verification_report)`, plus formal steps if any. Mark inline execution of subagent-required skills as violations.

## Subagent / loop prompt requirements

### Intake / brief / decompose / critique / integration verify

Each Task prompt must include skill id, `SKILL.md` path, working directory, inputs, constraints, expected return (same pattern as `solidsdd-loop`). For brief and later steps, include Change Context and ChangeBrief paths.

### Per-item loop

When starting `solidsdd-loop` for an item, provide:

- Skill path to `solidsdd-loop/SKILL.md`
- Working directory (consuming project root)
- **Change intent** = that item’s `intent`
- The item’s `acceptance_criterion` (Gherkin Scenario; for verify focus)
- Optional `feature_path` / `scenario_name` when present
- Change Context path/excerpt (§4 NFR / §5 tech when relevant)
- ChangeBrief path/excerpt (in/out of scope)
- Context summary and WorkPlan excerpt (item id + depends)
- Note that sibling loops in the **same wave** may run concurrently; keep edits scoped to this item’s intent

## Success criteria

- Subagent-required steps were not run inline in the parent (or were re-run via Task and counted)
- Change Context came from intake without parent thinning; `critique(change_context)` ran; Change Context gate honored when `required`
- ChangeBrief came from brief without parent thinning; `critique(change_brief)` ran
- WorkPlan came from decompose without parent thinning; `critique(work_plan)` ran
- Each done item had a `solidsdd-loop` run scoped to its intent
- Independent `ready` items in a wave were started **in parallel** (or serialized only with an explicit contention reason)
- Integration `solidsdd-verify` (+ critique) ran after all items (or after the single item)
- Human gates honored; final summary includes the isolation checklist, wave grouping, and any blocked items

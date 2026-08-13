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

Drive **requirement → [optional Grill] → Change Context → ChangeBrief → WorkPlan → per-slice loop → integration verify → knowledge harvest**. This skill is **orchestrator-only** — do not delegate `solidsdd.run` itself to a subagent.

`solidsdd-loop` stays the **slice** orchestrator (one change intent / one Gherkin Scenario). Do not re-implement loop phases inside `solidsdd-run`.

## References

- [execution-model.md](references/execution-model.md) — orchestrator / subagent / critique / context-pack rules
- [change-context.md](references/change-context.md) — demand / NFR / tech selection (fixed Markdown)
- [change-brief.md](references/change-brief.md) — scope premise (return point)
- [change-lifecycle.md](references/change-lifecycle.md) — active change paths / additional requirements
- [change-brief.schema.json](references/change-brief.schema.json)
- [active-change.schema.json](references/active-change.schema.json)
- [change-status.schema.json](references/change-status.schema.json)
- [work-decomposition.md](references/work-decomposition.md) — slice rules for WorkPlan
- [gherkin-requirements.md](references/gherkin-requirements.md) — property-level Gherkin
- [work-plan.schema.json](references/work-plan.schema.json)
- [architecture-axes.md](references/architecture-axes.md) — when a change affects structure
- [architecture-plan.schema.json](references/architecture-plan.schema.json)
- [adversarial-critique.md](references/adversarial-critique.md) — including `subject: change_context` / `change_brief` / `work_plan` / `architecture_plan`
- [human-gates.md](references/human-gates.md)
- [loop-retry.md](references/loop-retry.md) — verify/critique failure → retry / gate / stop
- [contract-layout.md](references/contract-layout.md)
- [run-state.md](references/run-state.md) — **persist phase / retries / item artifacts (required)**; prefer `scripts/solidsdd-run-state.sh`
- [run-state.schema.json](references/run-state.schema.json)
- [run-cost.md](references/run-cost.md) — wall-clock cost model; **B1–B5 cost skips**; context packs; greenfield/follow-on mitigations; host toolchain thrash vs orchestration cost
- [knowledge.md](references/knowledge.md) — durable knowledge consult / harvest in the run
- [clarifications.md](references/clarifications.md) — durable framing Q/A (Grill)
- [solidsdd-next.md](references/solidsdd-next.md) — deterministic next / validate
- [host-toolchain.md](references/host-toolchain.md) — preflight; paste commands into Tasks; no rediscovery
- [project-rule.mdc](references/project-rule.mdc) — copy into `.cursor/rules/` (or equivalent) once per project

## Execution policy

| Step | How |
|------|-----|
| `solidsdd-context` | Parent agent (this conversation) |
| `solidsdd-grill` (conditional), `solidsdd-knowledge` (consult / harvest), `solidsdd-intake`, `solidsdd-brief`, `solidsdd-decompose`, `solidsdd-architecture`, `solidsdd-critique`, `solidsdd-verify` (integration), `solidsdd-verify-formal` (if needed) | **Required subagent** via Task |
| Each WorkPlan item | Invoke **`solidsdd-loop`** as the slice orchestrator (same parent session following that skill — do not inline judge/apply/implement inside `solidsdd-run`) |

Never execute a subagent-required skill’s procedure in the parent. Do not rewrite Change Context / `ChangeBrief` / `WorkPlan` / `knowledge-harvest.json` / `clarifications/open.json` or thin a `CritiqueReport`—re-run the owning skill as a subagent if wrong.

**Persist:** maintain `.solidsdd/changes/<change_id>/run-state.json` via **`scripts/solidsdd-run-state.sh`** (read at step start, write at step end). Prefer `scripts/solidsdd-next.sh next` / `validate --declared` when available ([run-state.md](references/run-state.md)). Do **not** mutate run-state with free-form `python -c` / unbounded heredoc. Outer critique/verify JSON may live under the change directory; per-item plans/reports under `items/<item_id>/`.

## Sequence

1. Parent: `solidsdd-context` (include existing Features/contracts, `knowledge/` / `.solidsdd/kg/` presence, **host toolchain** via `scripts/solidsdd-host-toolchain.sh` → `.solidsdd/host-toolchain.json`, and any `.solidsdd/active-change.json` / `run-state.json`). Copy readiness into `run-state.host_toolchain` when the change dir / run-state exists (or on first run-state write). If `ready=false`, warn in the summary and prefer fixing the host before a long multi-Task run.
2. If `run-state.json` exists with `phase` not `done` and `status.json` is `active` → **resume** from that phase (skip completed outer steps; do not re-invent Brief/WorkPlan unless critique failed). Honor open blocking clarifications before advancing past Grill/intake.
3. **Task subagent** `solidsdd-knowledge` with `mode: consult` when starting a change (or when `knowledge/` / `.solidsdd/kg/` exists). Prefer after intake has created the change directory so `knowledge-consult.md` lands under `.solidsdd/changes/<change_id>/`; if consulting before intake, re-run or move the pack after the dir exists. Set `phase: knowledge_consult` when persisting run-state.
4. **Conditional Task** `solidsdd-grill` when framing is ambiguous, the user asks to grill, or `solidsdd-next` recommends `grill` ([clarifications.md](references/clarifications.md)). Skip when the initial instruction already settled framing. Set `phase: grill`. If `clarifications/open.json` has blocking opens → **stop** until resolved or `gate-approval` `scope: clarifications`; then resume.
5. **Task subagent** `solidsdd-intake` → `change-context.md` + `change-context-gate.json` under `.solidsdd/changes/<change_id>/` (pass optional user `change_id`; creates lifecycle paths — [change-lifecycle.md](references/change-lifecycle.md)). Pass `knowledge-consult.md` and `clarifications/open.json` when present. Create initial `run-state.json` with `scripts/solidsdd-run-state.sh --change-id <id> init` (`phase: intake`, `run_retry` remaining 3) if not already created. After the change dir exists, ensure consult output is under that dir (Task re-consult if needed).
6. Read `change-context-gate.json`'s `human_gate.required`:
   - **If `true`**: **Task subagent** `solidsdd-critique` with `subject: change_context` now, before Brief runs, so a required gate is checked before spending effort on the Brief; persist critique; update `phase` / `run_retry`. On fail → follow [loop-retry.md](references/loop-retry.md) (usually re-intake as Task, then critique again); decrement `run_retry.remaining`. Then **stop** until humans approve (or amend + re-intake); write `stopped_reason`; then resume without thinning Change Context — [human-gates.md](references/human-gates.md). Optionally suggest manual `solidsdd-report` for a readable snapshot (not a required gate). Continue to step 7 once resumed.
   - **If `false`**: skip a standalone `change_context` critique here — it is reviewed together with the Brief in the combined Specification Review at step 8.
7. **Task subagent** `solidsdd-brief` → ChangeBrief for the **same** active `change_id` (must read Change Context; migrate legacy flat Brief if needed); set `phase: brief`. Pass knowledge-consult excerpts so `assumptions` / `constraints` may cite policy ids.
8. Critique the specification:
   - **If step 6 already critiqued `change_context` separately** (gate was required): **Task subagent** `solidsdd-critique` with `subject: change_brief` (Brief only). On fail → follow [loop-retry.md](references/loop-retry.md) (usually re-brief; re-intake if framing is wrong).
   - **Else**: **Task subagent** `solidsdd-critique` with `subject: specification`, reviewing `change-context.md` **and** `change-brief.json` together as one Specification Review Checkpoint ([adversarial-critique.md](references/adversarial-critique.md)). On fail, findings apply the Change Context and/or ChangeBrief major tables; `suggested_next_skills` names `solidsdd-intake` and/or `solidsdd-brief` per which document the finding concerns — follow [loop-retry.md](references/loop-retry.md) for whichever producer(s) are implicated.
9. If ChangeBrief has `human_gate.required: true` → **stop** until humans approve; then resume without thinning the brief. (`change-context-gate` was already `false` to reach the `specification` path, so only the Brief's own gate can fire here.)
10. **Task subagent** `solidsdd-decompose` → WorkPlan at `.solidsdd/changes/<change_id>/work-plan.json` (must read active ChangeBrief as scope authority). Initialize `run-state.items` from WorkPlan (`ready`/`pending`, each with `loop_retry` max 3, `artifact_dir: items/<id>`).
11. **Task subagent** `solidsdd-critique` with `subject: work_plan`
12. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-decompose; re-brief / re-intake if premise is wrong)
13. When prior Features / prior `.solidsdd/changes/*/out_of_scope` exist → **Task subagent** `solidsdd-critique` with `subject: cross_change_consistency` (recommended); on fail → re-brief / re-decompose as suggested
13b. When `knowledge-consult.md` cites confirmed/canonical policies → **Task** `solidsdd-critique` with `subject: knowledge_consistency` (recommended); on fail → re-intake / re-brief
14. If WorkPlan or any item has `human_gate.required: true` → **stop** until humans approve (write `gate-approval.json` before resume — [human-gates.md](references/human-gates.md)); then resume without thinning the plan
14b. **Task subagent** `solidsdd-architecture` → `ArchitecturePlan` at `.solidsdd/changes/<change_id>/architecture-plan.json` (reads Change Context, ChangeBrief, and WorkPlan `touches`; set `phase: architecture`). When it writes `status: changed`: **Task subagent** `solidsdd-critique` with `subject: architecture_plan` (Architecture Review checkpoint); persist both artifacts. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-run `solidsdd-architecture`). When it writes `status: unchanged`, skip the critique call entirely. If the ArchitecturePlan has `human_gate.required: true` → **stop** before launching waves until humans approve (write `gate-approval.json` `scope: architecture_plan` before resume — [human-gates.md](references/human-gates.md)); then resume without thinning the plan.
15. While items remain, run **waves** of independent loops (`phase: waves`, bump `wave_index`):
   - Promote any `pending` → `ready` when all `depends_on` are `done` (update both WorkPlan and `run-state.items`)
   - Collect **all** currently `ready` items as the wave (empty → if `pending`/`blocked` remain, stop with dependency / gate report; else proceed to integration)
   - Mark wave items `running` in `run-state`; for each item, follow **`solidsdd-loop` in this parent session** (Task per judge/critique/apply/… — **do not** launch one Task that runs the whole loop). When several ready items have **non-intersecting** `touches`, you may drive those loops concurrently in the same parent turn. Pass `item_id` and `items/<id>/` as the persistence root
   - Each loop uses that item’s `intent`, ChangeBrief + Change Context excerpts for scope/tech, its own Task subagents, and **`items.<id>.loop_retry`** (not chat memory)
   - After **all** loops in the wave finish: mark each `done` or `blocked` in WorkPlan + `run-state`; on human_gate/stop for an item, leave siblings’ results intact and decide whether to end the run or continue remaining waves
   - Then form the next wave from newly unblocked items
   - **Serialize when `touches` intersect**: if two+ ready items list overlapping paths in `touches` (set intersection non-empty), run those contending items sequentially within the wave; still parallelize non-contending ready items. If `touches` is missing, fall back to the legacy heuristic (“clearly contend on the same primary edit paths”) and prefer adding `touches` on re-decompose. If many items share touches with empty `depends_on`, record the smell in `isolation_notes` and prefer re-decompose (foundation `depends_on`) on critique fail / next change — see [work-decomposition.md](references/work-decomposition.md)
16. After all items `done` (or single-item plan finished its one loop):
   - **Integration verify:** check `scripts/solidsdd-next.sh next` first — it detects **B4** mechanically (exactly one WorkPlan item whose item `verification-report.json` already covers `acceptance_of_whole` / relevant `success_criteria` with pass) and recommends skipping straight to knowledge harvest. When B4 applies → skip duplicate integration verify+critique; record `cost_skip:B4` and reuse that report path. Else:
   - **Task subagent** `solidsdd-verify` over the whole workspace / `acceptance_of_whole` (and Brief `success_criteria` when relevant); write `integration-verification-report.json` (or `verification-report.json` at change root per layout)
   - **Separate Task subagent** `solidsdd-critique` (`subject: verification_report`); persist critique — never the same Task as verify
   - If formal artifacts were applied across slices → **Task** `solidsdd-verify-formal` then critique as in loop
17. On successful integration verify (+ critique), or B4 reuse of a covering item verify:
   - **Task subagent** `solidsdd-knowledge` with `mode: harvest` → write `knowledge-harvest.json`; set `phase: knowledge_harvest`. If `.solidsdd/kg/` does not exist yet, run `scripts/solidsdd-kg.sh init --root .` first (mechanical parent step, not a Task) — see [knowledge.md](references/knowledge.md).
   - When candidates exist (or harvest requests critique): **Task** `solidsdd-critique` (`subject: knowledge_harvest`); set `phase: critique_knowledge_harvest`
   - If `knowledge-harvest.json` has `human_gate.required: true` → **stop** until `gate-approval.json` with `scope: knowledge_harvest` ([human-gates.md](references/human-gates.md) / [knowledge.md](references/knowledge.md)); do **not** mark `done` yet. In the stop message, present every `proposed` candidate with `id` / `type` / `title` / **full `rationale`** (why harvested: provenance + universality + non-obvious bound) and `body` / `source_refs` when present — never id/title-only or “see the JSON”
   - On approve / approve_partial: **Task** `solidsdd-knowledge` with `mode: harvest` and `apply: true` (or instruct apply of allowed candidates only)
   - On reject / skip-all: record candidate statuses; proceed without writing knowledge
   - Then set `.solidsdd/changes/<change_id>/status.json` to `"status": "done"` and `run-state.phase` to `done`
18. On integration verify or critique failure, follow [loop-retry.md](references/loop-retry.md) with **`run_retry`** (**max_auto_retries = 3**, separate from each slice loop’s budget): prefer re-running the owning slice’s loop or suggested skills as Task—not parent edits
19. Leave unmet gates and blocked items visible in the final summary (and in `run-state.json`)

## Isolation checklist (required in final summary)

List: `toolchain(ready|gap)`, `knowledge(consult)`, `[grill if run]`, `intake`, `[critique(change_context) — only on the gate-required path]`, `[gate if required]`, `brief`, `critique(specification)` **or** `critique(change_brief)` (whichever path step 8 took), `decompose`, `critique(work_plan)`, `[critique(cross_change_consistency) when applicable]`, `[critique(knowledge_consistency) when applicable]`, `architecture` **and** `[critique(architecture_plan) — only when status:changed]` **and** `[gate if required]`, each wave with item ids → parallel `loop` (and note that each loop’s own isolation checklist applies; note any serialize-for-contention / `cost_skip:B*`), `verify` (integration) **or** `cost_skip:B4`, `critique(verification_report)` when verify ran, `knowledge(harvest)`, `[critique(knowledge_harvest)]`, `[knowledge gate if required]`, plus formal steps if any. Mark inline execution of subagent-required skills as violations. Persist notable notes on `run-state.isolation_notes` (including `toolchain_rediscovery:<tool>:<reason>` when a Subagent had to re-resolve host tools; `next_deviation:<action>:<reason>` when ignoring `solidsdd-next`; `cost_skip:B*`).

## Subagent / loop prompt requirements

### Intake / brief / decompose / architecture / knowledge / grill / critique / integration verify

Each Task prompt must include skill id, `SKILL.md` path, working directory, inputs, constraints, expected return (same pattern as `solidsdd-loop`). For brief and later steps, include Change Context and ChangeBrief paths. For architecture, additionally include the WorkPlan path (`touches` is the primary structural-change signal). For knowledge harvest, include Context/Brief paths and whether `apply` is allowed. For grill, include clarifications path. Tell critique/verify/knowledge where to **write** JSON when under this change. When re-invoking `solidsdd-critique` on a `subject` that just failed, include the prior `CritiqueReport` path (and the fix summary) so the Task can follow [adversarial-critique.md](references/adversarial-critique.md) "Retry critique" instead of re-deriving every check from scratch.

**Toolchain (required for verify / implement / derive-tests / any shell that runs npm|node|bundle|npx):** paste the context **Toolchain** `commands` block (or `.solidsdd/host-toolchain.json` `commands`). Instruct the Subagent: use only those commands; **do not** `find` / multi-path search for npm/node; on failure report immediately. See [host-toolchain.md](references/host-toolchain.md).

### Per-item loop

When starting `solidsdd-loop` for an item, provide:

- Skill path to `solidsdd-loop/SKILL.md`
- Working directory (consuming project root)
- **Change intent** = that item’s `intent`
- **`item_id`** and artifact directory `.solidsdd/changes/<change_id>/items/<item_id>/`
- Instruction to write/refresh **`items/<id>/context-pack.md`** and pass it into every Task ([execution-model.md](references/execution-model.md))
- The item’s `acceptance_criterion` (Gherkin Scenario; for verify focus) and `covers`
- Optional `feature_path` / `scenario_name` when present
- Change Context path/excerpt (§4 NFR / §5 tech when relevant)
- ChangeBrief path/excerpt (in/out of scope)
- Context summary and WorkPlan excerpt (item id + depends)
- **Toolchain commands** from context / `host-toolchain.json` (required)
- Instruction to read/write that item’s `loop_retry` via parent-updated `run-state.json`
- Note [allowed cost skips B1–B5](references/run-cost.md#allowed-cost-skips-b1b5)
- Note that sibling loops in the **same wave** may run concurrently; keep edits scoped to this item’s intent

## Success criteria

- Subagent-required steps were not run inline in the parent (or were re-run via Task and counted), except documented mechanical cost skips
- `run-state.json` reflects phase, waves, retry remaining, and `cost_skip:B*` notes after each step
- Change Context came from intake without parent thinning; Change Context gate honored when `required`
- ChangeBrief came from brief without parent thinning; both Change Context and ChangeBrief were critiqued — either as a standalone `critique(change_context)` + `critique(change_brief)` pair (gate-required path) or as one `critique(specification)` covering both (gate-not-required path); never left uncritiqued
- WorkPlan came from decompose without parent thinning; `critique(work_plan)` ran
- `solidsdd-architecture` ran before the wave loops; when it wrote `status: changed`, `critique(architecture_plan)` ran and the ArchitecturePlan's human gate (if any) was honored before waves launched
- Each done item had a `solidsdd-loop` run scoped to its intent with persisted plans / context-pack under `items/<id>/`
- Independent `ready` items in a wave were started **in parallel** (or serialized only with an explicit contention reason)
- Integration `solidsdd-verify` (+ critique) ran after all items **or** B4 reused a covering single-item verify
- `solidsdd-knowledge` harvest ran after successful integration (or B4-equivalent success); knowledge human gate honored when `required`; change not marked `done` while that gate is pending
- Human gates honored; final summary includes the isolation checklist, wave grouping, cost skips, and any blocked items

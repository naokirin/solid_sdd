---
name: solidsdd-run
description: >-
  Outer orchestrator for solid_sdd. Runs Triage first to pick an Execution
  Profile (direct/thin/standard/full), then either implements directly,
  runs a thin implement+verify pass, or produces Change Context and
  ChangeBrief, decomposes into a WorkPlan, runs solidsdd-loop once per item,
  then integration solidsdd-verify. Parent only — do not delegate
  solidsdd-run itself. Use for multi-criterion work; use solidsdd-loop alone
  for a single known slice already scoped at standard/full.
license: MIT
---

# solidsdd.run

## Purpose

Drive **requirement → Triage (Execution Profile) → [direct | thin | optional Grill → Change Context → ChangeBrief → WorkPlan → per-slice loop → integration verify → knowledge harvest]**. This skill is **orchestrator-only** — do not delegate `solidsdd.run` itself to a subagent.

Not every change needs the full pipeline. **Triage** classifies the change's risk/complexity/boundary-impact and selects one of four **Execution Profiles** before any heavy step runs — see [triage.md](references/triage.md). Trivial and simple changes run **Direct (L0)** or **Thin (L1)** and never touch Intake/Brief/WorkPlan/Architecture/Critique; ordinary and high-risk changes run **Standard (L2)** / **Full (L3)**, which is exactly today's pipeline, unchanged. A profile can only escalate upward mid-run, never downgrade — see **Escalation** below.

`solidsdd-loop` stays the **slice** orchestrator (one change intent / one Gherkin Scenario) for the Standard/Full path. Do not re-implement loop phases inside `solidsdd-run`.

## References

- [triage.md](references/triage.md) — Execution Profile decision rules, explicit-profile safety override, escalation triggers
- [triage-result.schema.json](references/triage-result.schema.json)
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
- [physical-design.md](references/physical-design.md) — optional, Level 3 only; completes before implementation waves start
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
| `solidsdd-context`, **Triage** | Parent agent (this conversation) — no Task; Triage must stay light (judgment + a `triage-result.json` write, not a Task) |
| Direct (L0) implementation + project verification | Parent agent — L0 has no isolation requirement to protect, so no Task |
| `solidsdd-implement` / `solidsdd-verify` under Thin (L1) | **Required subagent** via Task (same isolation reason as at Standard/Full) |
| `solidsdd-grill` (conditional), `solidsdd-knowledge` (consult / harvest), `solidsdd-intake`, `solidsdd-brief`, `solidsdd-decompose`, `solidsdd-architecture`, `solidsdd-critique`, `solidsdd-verify` (integration), `solidsdd-verify-formal` (if needed) | **Required subagent** via Task — Standard/Full (L2/L3) only |
| Each WorkPlan item (Standard/Full only) | Invoke **`solidsdd-loop`** as the slice orchestrator (same parent session following that skill — do not inline judge/apply/implement inside `solidsdd-run`) |

Never execute a subagent-required skill’s procedure in the parent. Do not rewrite Change Context / `ChangeBrief` / `WorkPlan` / `knowledge-harvest.json` / `clarifications/open.json` or thin a `CritiqueReport`—re-run the owning skill as a subagent if wrong.

**Persist:** maintain `.solidsdd/changes/<change_id>/run-state.json` via **`scripts/solidsdd-run-state.sh`** (read at step start, write at step end). Prefer `scripts/solidsdd-next.sh next` / `validate --declared` when available ([run-state.md](references/run-state.md)). Do **not** mutate run-state with free-form `python -c` / unbounded heredoc. Outer critique/verify JSON may live under the change directory; per-item plans/reports under `items/<item_id>/`.

## Sequence

1. Parent: `solidsdd-context` (include existing Features/contracts, `knowledge/` / `.solidsdd/kg/` presence, **host toolchain** via `scripts/solidsdd-host-toolchain.sh` → `.solidsdd/host-toolchain.json`, and any `.solidsdd/active-change.json` / `run-state.json` / `triage-result.json`). Copy readiness into `run-state.host_toolchain` when the change dir / run-state exists (or on first run-state write). If `ready=false`, warn in the summary and prefer fixing the host before a long multi-Task run.
2. **Triage or resume** (parent, no Task):
   - If `run-state.json` exists with `phase` not `done` and `status.json` is `active` → **resume**: read the persisted `execution_profile.effective` (a run-state predating this feature has none — treat as `standard`) and jump to the matching section below at the persisted `phase`; do not re-triage and do not re-invent Brief/WorkPlan unless critique failed. Honor open blocking clarifications before advancing past Grill/intake.
   - Else if only `triage-result.json` exists (no `run-state.json` — an L0 change being revisited) → read it; re-triage only if this request is materially different from what it recorded.
   - Else (new change): run **Triage** now. Parse an explicit profile from the user's instruction (`--profile <x>` or `profile: <x>`; default `auto`). Evaluate change type / complexity / risk / contract impact / architecture impact per [triage.md](references/triage.md); compute `required_minimum_profile` and `effective_profile = max(requested, required_minimum)`. Write `.solidsdd/changes/<change_id>/triage-result.json` ([triage-result.schema.json](references/triage-result.schema.json)), creating the change dir per [change-lifecycle.md](references/change-lifecycle.md) if needed (pass optional user `change_id`).
   - **Dispatch** on `effective_profile`: `direct` → follow **Direct execution (L0)** below and stop — do not continue into step 3. `thin` → follow **Thin execution (L1)** below and stop. `standard` or `full` → continue at step 3 (today's full Sequence; `full` additionally applies the tightenings marked inline below).

## Direct execution (L0)

For changes Triage classified `direct`: typo/wording fixes, local CSS/UI tweaks, log lines, single-function internal implementation changes, non-structural refactors — no contract, API, DB, or architecture impact.

1. Implement the change directly in this parent conversation. No Task subagent — L0 has no isolation concern to protect (there is no separate contract/plan phase to isolate implementation from).
2. Run whatever of the project's own test / lint / typecheck commands apply to the touched files (via Bash). If none apply, say so in the summary.
3. Write `.solidsdd/changes/<change_id>/triage-result.json` (already written at step 2) and `.solidsdd/changes/<change_id>/status.json` with `"status": "done"`. Do **not** create `run-state.json`, `change-context.md`, `change-brief.json`, or `work-plan.json` — none of those apply at L0.
4. If verification fails, or you discover a risk category / contract impact / architecture impact you didn't see at Triage → do not force it through at L0. Follow **Escalation** below instead of pushing ahead.
5. Final summary: what changed, what verification ran and its result, and that this was a `direct` (L0) run — explicitly note that Intake/Brief/Decompose/Architecture/`solidsdd-loop`/Critique did **not** run, by design.

## Thin execution (L1)

For changes Triage classified `thin`: small additive feature work, small UI feature additions, narrow additive extensions to an existing contract, small existing-logic changes — local impact confirmed, but worth a light isolation/verification pass.

1. Initialize a **reduced** `run-state.json` via `scripts/solidsdd-run-state.sh --change-id <id> init` (`phase: triage`); persist `execution_profile` immediately (`scripts/solidsdd-run-state.sh --change-id <id> set-execution-profile …`, per [run-state.md](references/run-state.md)).
2. Optional: write a short Context/Impact note (a few lines: touched files, why this is scoped thin) at `.solidsdd/changes/<change_id>/thin-context.md` when it will materially help the Task prompts. This is **not** a ChangeBrief — do not give it `human_gate` / `success_criteria` / scope fields.
3. **Task subagent** `solidsdd-implement` with the change intent, the Context/Impact note (if written), and Toolchain commands ([host-toolchain.md](references/host-toolchain.md)). Set `phase: thin_implementation`.
4. **Task subagent** `solidsdd-verify` scoped to the touched surface; write `verification-report.json`. Set `phase: thin_verification`.
5. On pass: set `.solidsdd/changes/<change_id>/status.json` `"status": "done"` and `run-state.phase: done`. Do **not** run a standalone critique on a clean pass — this profile is checkpoint/failure-driven like the rest of solid_sdd ([adversarial-critique.md](references/adversarial-critique.md)); nothing here is a producer-driven checkpoint.
6. On failure, or when the Task reports it can't judge safety, or a contract/architecture surface shows up that Triage didn't expect → **Task subagent** `solidsdd-critique` (`subject: verification_report`, or `subject: triage` when the Triage call itself is in question) and follow **Escalation** below. Do not silently retry the same failure class at L1 more than once.

## Standard / Full execution (L2/L3)

Runs when Triage's `effective_profile` is `standard` or `full` — this is `solidsdd-run`'s full Sequence, unchanged by Execution Profiles except where marked "**Under `full`**" below.

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
13. When prior Features / prior `.solidsdd/changes/*/out_of_scope` exist → **Task subagent** `solidsdd-critique` with `subject: cross_change_consistency` (recommended at `standard`; **required at `full`** — do not skip it there when prior Features/changes exist); on fail → re-brief / re-decompose as suggested
13b. When `knowledge-consult.md` cites confirmed/canonical policies → **Task** `solidsdd-critique` with `subject: knowledge_consistency` (recommended at `standard`; **required at `full`**); on fail → re-intake / re-brief
14. If WorkPlan or any item has `human_gate.required: true` → **stop** until humans approve (write `gate-approval.json` before resume — [human-gates.md](references/human-gates.md)); then resume without thinning the plan
14b. **Task subagent** `solidsdd-architecture` (reads Change Context, ChangeBrief, and WorkPlan `touches`; set `phase: architecture`). At Level 0 (no structural trigger) it writes only `ArchitecturePlan` at `.solidsdd/changes/<change_id>/architecture-plan.json` with `status: unchanged`. Otherwise it edits the Architecture Model — `.solidsdd/architecture/{workspace.dsl,invariants.yaml}` (persistent, whole-project) and `.solidsdd/changes/<change_id>/architecture-reasoning.md` — then generates `architecture-plan.json` (`status: changed`) as a projection of that model; at Architecture Depth Level 3, when the physical realization is non-obvious, it additionally writes `.solidsdd/changes/<change_id>/physical-design.md` ([physical-design.md](references/physical-design.md)). This whole step (Logical Design through Physical Design, when applicable) completes before any implementation wave starts — do not let a wave's `solidsdd-loop` begin before Architecture resolves. When it writes `status: changed`: **Task subagent** `solidsdd-critique` with `subject: architecture_plan` (Architecture Review checkpoint, reads the Architecture Model + Reasoning + generated plan + `physical-design.md` when present); persist all artifacts. On critique fail → follow [loop-retry.md](references/loop-retry.md) (usually re-run `solidsdd-architecture`). When it writes `status: unchanged`, skip the critique call entirely. If the ArchitecturePlan has `human_gate.required: true` → **stop** before launching waves until humans approve (write `gate-approval.json` `scope: architecture_plan` before resume — [human-gates.md](references/human-gates.md)); then resume without thinning the plan.
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
   - **Under `full`**: when a slice's ApplicationPlan defers `formal` for a category Triage flagged as high-risk (concurrency, transaction boundary, distributed processing — see [triage.md](references/triage.md)), that deferral is not the default; the item's `solidsdd-judge` rationale must justify it explicitly rather than deferring silently
17. On successful integration verify (+ critique), or B4 reuse of a covering item verify:
   - **Task subagent** `solidsdd-knowledge` with `mode: harvest` → write `knowledge-harvest.json`; set `phase: knowledge_harvest`. If `.solidsdd/kg/` does not exist yet, run `scripts/solidsdd-kg.sh init --root .` first (mechanical parent step, not a Task) — see [knowledge.md](references/knowledge.md).
   - When candidates exist (or harvest requests critique): **Task** `solidsdd-critique` (`subject: knowledge_harvest`); set `phase: critique_knowledge_harvest`
   - If `knowledge-harvest.json` has `human_gate.required: true` → **stop** until `gate-approval.json` with `scope: knowledge_harvest` ([human-gates.md](references/human-gates.md) / [knowledge.md](references/knowledge.md)); do **not** mark `done` yet. In the stop message, present every `proposed` candidate with `id` / `type` / `title` / **full `rationale`** (why harvested: provenance + universality + non-obvious bound) and `body` / `source_refs` when present — never id/title-only or “see the JSON”
   - On approve / approve_partial: **Task** `solidsdd-knowledge` with `mode: harvest` and `apply: true` (or instruct apply of allowed candidates only)
   - On reject / skip-all: record candidate statuses; proceed without writing knowledge
   - Then set `.solidsdd/changes/<change_id>/status.json` to `"status": "done"` and `run-state.phase` to `done`
18. On integration verify or critique failure, follow [loop-retry.md](references/loop-retry.md) with **`run_retry`** (**max_auto_retries = 3**, separate from each slice loop’s budget): prefer re-running the owning slice’s loop or suggested skills as Task—not parent edits
19. Leave unmet gates and blocked items visible in the final summary (and in `run-state.json`)

## Escalation

Any escalation trigger from [triage.md](references/triage.md) — verification failure, unexpected test failure, contract mismatch, unexpected dependency, architecture/public-API impact discovered, data-integrity risk discovered, scope exceeding the initial assessment, or the agent being unable to judge safety at the current profile — fires during **any** profile, not just Direct/Thin. When it fires:

1. Re-run Triage with the new evidence. **Never move to a lower profile** — only up, or stay if already at `full`.
2. Write a new `triage-result.json` with an `escalation` block (`from`, `to`, `trigger`, `reason`, `at`); keep the prior file too (do not delete it — it's the audit trail).
3. **From Direct (L0)**: `run-state.json` didn't exist — initialize it now at the phase the new profile requires. Whatever was already implemented and whatever the L0 verification attempt found become inputs (mention them in the Intake/Brief Task prompt as prior context), not throwaway work.
4. **From Thin (L1)**: keep the existing reduced `run-state.json`'s `triage` / `thin_implementation` / `thin_verification` history; initialize the remaining Standard/Full phases the new profile requires (usually starting at `intake`), passing `thin-context.md` (if written) into that Task as prior framing. Do not redo the L1 implementation from scratch — but do run every Standard/Full checkpoint (Brief, WorkPlan, Architecture Judgment, and their critiques) that the new profile requires and L1 skipped; escalation upgrades assurance, it does not retroactively grant it.
5. **Within Standard escalating to Full**: no phase restart — only the "Under `full`" tightenings above become required for the remainder of the run.
6. State the escalation and its reason in the final summary — never continue silently as if the profile had been `standard`/`full` from the start.

## Isolation checklist (required in final summary)

**Every profile:** state `triage(effective_profile, required_minimum_profile, reasons)` first, and any `escalation` that occurred.

**Direct (L0):** `triage`, implementation, verification-commands-run — and explicitly confirm intake/brief/decompose/architecture/loop/critique/knowledge did **not** run.

**Thin (L1):** `triage`, `[thin-context note if written]`, `implement` (Task), `verify` (Task), `[critique if failure/uncertainty triggered escalation]` — and explicitly confirm brief/decompose/architecture/waves/knowledge-harvest did **not** run.

**Standard/Full (L2/L3):** `triage`, `toolchain(ready|gap)`, `knowledge(consult)`, `[grill if run]`, `intake`, `[critique(change_context) — only on the gate-required path]`, `[gate if required]`, `brief`, `critique(specification)` **or** `critique(change_brief)` (whichever path step 8 took), `decompose`, `critique(work_plan)`, `[critique(cross_change_consistency) when applicable — required under full]`, `[critique(knowledge_consistency) when applicable — required under full]`, `architecture` **and** `[critique(architecture_plan) — only when status:changed]` **and** `[gate if required]`, each wave with item ids → parallel `loop` (and note that each loop’s own isolation checklist applies; note any serialize-for-contention / `cost_skip:B*`), `verify` (integration) **or** `cost_skip:B4`, `critique(verification_report)` when verify ran, `knowledge(harvest)`, `[critique(knowledge_harvest)]`, `[knowledge gate if required]`, plus formal steps if any.

Mark inline execution of subagent-required skills as violations. Persist notable notes on `run-state.isolation_notes` (including `toolchain_rediscovery:<tool>:<reason>` when a Subagent had to re-resolve host tools; `next_deviation:<action>:<reason>` when ignoring `solidsdd-next`; `cost_skip:B*`).

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

- Triage ran (or was correctly resumed/reused) before any heavier step; `effective_profile` is never below `required_minimum_profile`; an explicit low profile request never bypassed the safety floor
- Direct (L0) never invoked Intake/Brief/Decompose/Architecture/`solidsdd-loop`/Critique/Knowledge, and never wrote `run-state.json`
- Thin (L1) never invoked Brief/Decompose/Architecture/waves/Knowledge Harvest, and ran a standalone critique only on failure/uncertainty, not on a clean pass
- Any escalation only moved the profile **up**, was recorded in a new `triage-result.json` with an `escalation` block, and was stated in the final summary — never applied silently
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

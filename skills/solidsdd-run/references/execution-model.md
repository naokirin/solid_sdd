# Execution model (Orchestrator / Subagent)

If skills run only as a continuous sequence in one agent, the following happens:

- A large requirement enters a single loop and acceptance criteria drift from artifacts
- Application judgment softens contracts to reduce later implementation/fix cost
- Contracts are weakened or tests rewritten to match the implementation while still in the implementer’s context
- OCL→test generation mixes with implementation edits
- Verification becomes self-grading
- **Each phase’s artifact quality is left to the agent that produced it**

Therefore, **when the caller is an orchestrator (`solidsdd.run` / `solidsdd.loop` or an equivalent parent agent)**, the parent must not execute “Subagent required” skills itself. In Cursor, launch an **explicit subagent** (e.g. Task tool) and pass only the skill name and I/O.

Additionally, after major phases, **always launch `solidsdd.critique` (adversarial evaluation) as a separate Task**. Like SpecKit clarify / analyze, this keeps the quality gate as an independent command. Severity is **major/fail only when checkability is lost**; polishing at standard density stays minor (loop continues). Details: bundled `adversarial-critique.md` (edit source: `reference-src/adversarial-critique.md`).

When a user manually names a single skill, the conversation agent may run it (the user is the parent).

## Two-layer orchestration

```text
User or solidsdd.run (outer parent)
  │
  ├─ solidsdd.context                 … parent OK
  ├─ Task: solidsdd.intake            ← Change Context (MD) + gate JSON
  ├─ Task: solidsdd.critique          ← subject: change_context
  ├─ [stop if change-context-gate human_gate.required]
  ├─ Task: solidsdd.brief             ← ChangeBrief
  ├─ Task: solidsdd.critique          ← subject: change_brief
  ├─ Task: solidsdd.decompose         ← WorkPlan (from Brief)
  ├─ Task: solidsdd.critique          ← subject: work_plan
  ├─ wave: all currently ready items (depends_on satisfied)
  │     ├─ solidsdd.loop (item A)     … same wave: parallel by default
  │     └─ solidsdd.loop (item B)     … serialize only on path contention
  │           └─ Task: judge / critique / apply-* / verify / …
  ├─ … next wave after dependents unlock …
  └─ Task: solidsdd.verify            ← integration (acceptance_of_whole)
       └─ Task: solidsdd.critique     ← verification_report
```

- **`solidsdd.run`**: Intake → Brief → decompose → **wave-scoped slices** → integration verify → mark change `done`. Do not reimplement loop phases in the parent.
- **`solidsdd.loop`**: Dedicated to **one slice** (one verifiable acceptance criterion / one change intent). Need not know WorkPlan; may receive ChangeBrief / Change Context excerpts for scope and tech.
- Even a single-item WorkPlan: run still invokes loop **once**, then integration verify.
- **Parallelism**: Launch `solidsdd.loop` for all `ready` items in a wave by default. Serialize only contested groups when there is clear path contention on the same artifacts.
- **Across changes**: Additional requirements start a new meaningful `change_id` under `.solidsdd/changes/` (see [../reference-src/change-lifecycle.md](../reference-src/change-lifecycle.md)). Features and contracts accumulate; Briefs do not become a living PRD.
- **Cost**: Expect roughly **10+ Task steps per slice** plus outer intake/brief/decompose critiques. Greenfield WorkPlans must use foundation `depends_on` / narrow `touches` — see [run-cost.md](run-cost.md) and [../reference-src/work-decomposition.md](../reference-src/work-decomposition.md).

## Role split (slice = `solidsdd.loop`)

```text
User or solidsdd.loop (parent / orchestrator)
  │
  ├─ solidsdd.context              … parent OK (optional under run)
  │
  ├─ Task: solidsdd.judge          ← subagent required (avoid bias)
  ├─ Task: solidsdd.critique       ← subagent required (adversarial plan review)
  ├─ Task: solidsdd.apply.api      ← subagent required
  ├─ Task: solidsdd.critique       ← subagent required (API contract)
  ├─ Task: solidsdd.apply.dbc      ← subagent required
  ├─ Task: solidsdd.critique       ← subagent required (OCL)
  ├─ Task: solidsdd.derive.tests   ← subagent required
  ├─ Task: solidsdd.critique       ← subagent required (derived tests)
  ├─ Task: solidsdd.implement      ← subagent required
  ├─ Task: solidsdd.verify         ← subagent required
  ├─ Task: solidsdd.critique       ← subagent required (verification report)
  ├─ Task: solidsdd.apply.formal   ← subagent required (Phase 3, after gate approval)
  ├─ Task: solidsdd.critique       ← subagent required (formal spec)
  └─ Task: solidsdd.verify.formal  ← subagent required (Phase 3)
       └─ Task: solidsdd.critique  ← subagent required (formal verification report)
```

## Per-skill policy

| Skill | Execution policy | Reason |
|-------|------------------|--------|
| `solidsdd.run` | **orchestrator only** | Outer parent; do not delegate to a subagent |
| `solidsdd.loop` | **orchestrator only** | Slice parent; do not delegate to a subagent |
| `solidsdd.context` | orchestrator | For later planning; light exploration may stay on the parent |
| `solidsdd.intake` | **subagent required** | Isolate demand / NFR / tech framing from scope slicing |
| `solidsdd.brief` | **subagent required** | Isolate change scope (in/out) from slicing and implementation |
| `solidsdd.decompose` | **subagent required** | Isolate work decomposition from contract judgment and implementation |
| `solidsdd.judge` | **subagent required** | Isolate density judgment from implementation context; avoid thinning contracts |
| `solidsdd.critique` | **subagent required** | Someone other than the producer adversarially evaluates phase artifacts (including weak contracts) |
| `solidsdd.apply.api` | **subagent required** | Stay within API contracts; do not mix with implementation or tests |
| `solidsdd.apply.dbc` | **subagent required** | Stay within OCL |
| `solidsdd.derive.tests` | **subagent required** | Core of OCL→tests; isolation must forbid implementation edits |
| `solidsdd.implement` | **subagent required** | Fix implementation only; do not rewrite contracts |
| `solidsdd.verify` | **subagent required** | Avoid self-grading in the implementer’s context |
| `solidsdd.apply.formal` | **subagent required** | Stay within formal specs (Phase 3) |
| `solidsdd.verify.formal` | **subagent required** | Avoid self-grading of model checking (Phase 3) |

The parent accepts artifacts from `solidsdd.intake` / `solidsdd.brief` / `solidsdd.decompose` / `solidsdd.judge` and only drives loop branching. It does not re-run or overwrite the judgment itself. Critique outcomes are not softened by the parent.

From Phase 2 onward, the parent also handles the following (see skill `references/human-gates.md` / `loop-retry.md`):

- If `human_gate.required` is true, **stop before apply** (still effective after critique(plan) passes). Under run: Change Context gate may stop before brief; ChangeBrief gate may stop before decompose; WorkPlan gate may stop before slice loops
- Follow `loop_action` (`retry` / `human_gate` / `stop`) on verify / critique fail (default auto-retry cap 3; **shared budget per orchestrator**. run and each loop have separate budgets)

Phase 3: only after human-gate approval for `formal` `apply`, launch `solidsdd.apply.formal` / critique(formal) / `solidsdd.verify.formal`. Deferred formal must not block the API/DbC path.

## Adversarial isolation and feedback

1. If the parent runs a subagent-required skill inline → record as `solidsdd.critique` (`subject: isolation`) and **re-run that skill via Task** (the parent must not “fix” the artifact itself)
2. Critique / verify `retry` → launch the suggested skill as a **new Task**, then re-run critique for that subject (and verify if needed)
3. Auto-retry is **at most 3** (verify fail + critique fail + isolation re-run combined). No progress on the same skill repeatedly, or budget exhausted → `human_gate`
4. No infinite loops: do not auto-retry after the budget is exceeded
5. **Never** put a producer and its matching `solidsdd.critique` in the **same** Task (includes integration `verify` + `critique(verification_report)`)
6. **Never** launch one Task whose job is “execute the entire `solidsdd.loop` for item Wn” (judge through verify). The **run parent** (or the human session following `solidsdd.loop`) must orchestrate; each subagent-required skill is its own Task. “Separate write passes” inside one agent are **not** a compliant substitute — treat as isolation violation and re-run via Task, or stop at `human_gate` if the host cannot launch Tasks

## Parent obligations (`solidsdd.loop`)

1. Do not collapse subagent-required skills into “I’ll follow the skill steps myself” via the parent’s tools
2. Include in each Task prompt: path to that skill’s `SKILL.md`, artifact paths, and prior outputs (context summary, ApplicationPlan, critique subject, etc.)
3. Accept only the subagent’s outputs (diffs, reports, ApplicationPlan, CritiqueReport) and pass them to the next phase
4. Do not thin contracts or findings by rewriting `ApplicationPlan` / CritiqueReport in the parent (if wrong, re-launch the relevant skill as a Subagent)
5. If `human_gate.required`, do not apply until approved (including early formal rollout)
6. **Do not skip** the matching `solidsdd.critique` after a producer step **unless** an [allowed cost skip (B1–B5)](run-cost.md#allowed-cost-skips-b1b5) applies; record `cost_skip:B<n>` in `isolation_notes`
7. If `solidsdd.verify` / `solidsdd.verify.formal` / `solidsdd.critique` fails, follow `loop_action` and suggested skills and **re-launch as a subagent** (or gate / stop)
8. Stop at a human gate when the auto-retry cap is exceeded
9. Leave a final summary listing each required Task / mechanical substitute and critique subject (isolation checklist), including any `cost_skip:B*`
10. When contracts already exist for this change, prefer ApplicationPlans that **extend** shared OpenAPI/OCL rather than re-scaffolding the package on every item
11. Before the first producer Task of a slice (and when pack would go stale after large edits), write **`items/<id>/context-pack.md`** (see [Context pack](#context-pack)) and pass its path in every Task prompt for that item

## Parent obligations (`solidsdd.run`)

1. Do not inline `solidsdd.intake` / `critique(change_context)` / `solidsdd.brief` / `critique(change_brief)` / `solidsdd.decompose` / `critique(work_plan)` / integration `verify` (except B4 reuse of a covering item verify)
2. Each item follows the **`solidsdd.loop` skill on this parent session** (run parent must not directly run judge/apply/implement, and must **not** delegate the whole loop to a single Task)
3. Do not thin Change Context / `ChangeBrief` / `WorkPlan` / CritiqueReport in the parent
4. Respect Change Context gate before brief; ChangeBrief human_gate before decompose; WorkPlan human_gate before launching slices
5. Pass Change Context and ChangeBrief paths/excerpts **and context-pack paths** into decompose and into each loop prompt when scope or tech questions may arise
6. Launch loops for independent `ready` items in the same wave **in parallel** (serialize only with a recorded reason on contention). If many ready items share `touches`, prefer a WorkPlan that used foundation `depends_on` ([work-decomposition.md](../reference-src/work-decomposition.md)); record serialize reason in `run-state.isolation_notes`
7. After all items complete: run integration `solidsdd.verify` (+ **separate** critique Task) **unless B4** applies (single item whose verify already covers `acceptance_of_whole`); then record `cost_skip:B4`
8. Honor run-level retry budget; leave isolation checklist, wave shape, cost skips, and blocked items in the final summary
9. Read [run-cost.md](run-cost.md) before large greenfield runs; budget time for O(N × loop steps); apply [allowed cost skips](run-cost.md#allowed-cost-skips-b1b5) and context packs

## Context pack

Cold-start re-reads of full Brief / OpenAPI / OCL dominate wall-clock. The **parent** builds a short pack once per slice (and refreshes when the pack’s listed files change materially):

**Path:** `.solidsdd/changes/<change_id>/items/<item_id>/context-pack.md` (optional change-level pack for outer intake/brief Tasks: `context-pack-framing.md`)

**Include (keep short):**

- Absolute WD; `change_id` / `item_id`; working language
- Paths (+ 10–40 line excerpts only when needed) to Change Context, ChangeBrief, WorkPlan item block, Feature Scenario
- Host-toolchain `commands` block (paste verbatim)
- Cited knowledge policy ids + one-line each (not full files)
- After judge: ApplicationPlan path + target kind/status table
- Instruction: **prefer this pack**; do **not** re-Read full OpenAPI/OCL/Brief/tests unless you must edit that file or the pack is marked stale

**Do not** put full contract bodies or entire test files in the pack.

## Prompt template for subagents

```text
You are executing the solid_sdd skill: <skill-name>
Read and follow: skills/<skill-dir>/SKILL.md
Working directory: <consuming project root>
Context pack: <path to context-pack.md> — prefer it; avoid re-reading full SoT files unless editing them or pack is stale
Inputs:
  - ...
Constraints:
  - Do only what that skill allows
  - Return: summary, changed files, artifacts (plan/report JSON if any)
```

For critique, always include `subject` and the path/excerpt under evaluation.

## Manual execution

If the user calls only `solidsdd-derive-tests`, the current agent may run it.  
If **another skill continues in the same response** (e.g. implement right after judge), prefer Task for subagent-required skills to avoid crosstalk. In continuous chains, recommend inserting `solidsdd-critique` via Task right after each producer.

If a single verifiable acceptance criterion is already known, `solidsdd-loop` alone is enough. For multi-criterion or ambiguous requirements, use `solidsdd-run`.

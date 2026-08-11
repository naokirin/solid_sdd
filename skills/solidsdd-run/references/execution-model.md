# Execution model (Orchestrator / Subagent)

If skills run only as a continuous sequence in one agent, the following happens:

- A large requirement enters a single loop and acceptance criteria drift from artifacts
- Application judgment softens contracts to reduce later implementation/fix cost
- Contracts are weakened or tests rewritten to match the implementation while still in the implementer’s context
- OCL→test generation mixes with implementation edits
- Verification becomes self-grading
- **Each phase’s artifact quality is left to the agent that produced it**

Therefore, **when the caller is an orchestrator (`solidsdd.run` / `solidsdd.loop` or an equivalent parent agent)**, the parent must not execute “Subagent required” skills itself. In Cursor, launch an **explicit subagent** (e.g. Task tool) and pass only the skill name and I/O.

Critique is not automatically launched after every phase. `Plan Review` is the normal planning checkpoint. Additional adversarial critique (`solidsdd.critique`) is launched as a separate Task only when explicitly required by a quality checkpoint or when verification/diagnosis indicates it is necessary. Critique is checkpoint-driven and failure-driven, not producer-driven.

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
- **Cost**: Expect roughly **3–4 Task steps per slice** in the Canonical Consolidated Model (historically 10+ in fine-grained mode) plus outer framing and integration verification. Greenfield WorkPlans must use foundation `depends_on` / narrow `touches` — see [run-cost.md](run-cost.md) and [../reference-src/work-decomposition.md](../reference-src/work-decomposition.md).

## Role split (slice = `solidsdd.loop`)

```text
User or solidsdd.loop (parent / orchestrator)
  │
  ├─ solidsdd.context              … parent OK (optional under run)
  │
  ├─ [Canonical Slice Execution]
  ├─ Task: Plan Slice              ← judge + API/DbC contract design + derive-tests in one context
  ├─ Task: Implement Slice         ← apply code edits against contracts
  ├─ Task: Verify Slice            ← run contract tests & verification
  │
  └─ [Adversarial Checkpoints & Failure-driven Critique]
       ├─ Checkpoint Review        (WorkPlan & Integration Review at major quality boundaries)
       └─ Failure-driven Critique  (triggered on Verification failure / retry diagnosis)
```

### Canonical Consolidated Slice Model

The **Consolidated Slice Model** is the canonical execution model for `solidsdd-loop`:

- **Plan Slice Task**: Combines contract density judgment (`solidsdd.judge`), API/DbC contract updates (`apply.api`, `apply.dbc`), and contract test derivation (`derive.tests`) into a single coherent planning pass for the slice.
- **Implement Slice Task**: Applies source code implementation matching the slice specification and contracts.
- **Verify Slice Task**: Deterministically runs contract test suites and verification checks.
- **Checkpoint & Failure-Driven Critique**: Replaces per-artifact micro-critiques with checkpoint reviews at major quality boundaries (Specification, WorkPlan, Integration). Full Critique subagents are launched **on verification failure** or explicit isolation retry.

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
5. **Maintain phase boundary isolation**: keep `Plan Slice`, `Implement Slice`, `Verify Slice`, and `Failure-Driven Critique` in separate Subagent Tasks (do not collapse an entire loop into a single uncheckable Task).
6. **Checkpoint & Failure-Driven Critique**: Checkpoint Reviews are conducted at major quality boundaries (Specification, WorkPlan, Integration). Intermediate subagent critiques are omitted in green paths and triggered on verification failure or explicit retry diagnosis.

## Parent obligations (`solidsdd.loop`)

1. Do not collapse subagent-required phase tasks into “I’ll follow the skill steps myself” via the parent’s tools
2. Include in each Task prompt: path to that skill’s `SKILL.md`, artifact paths, **context-pack** path, and prior outputs (ApplicationPlan, critique subject, etc.)
3. Accept only the subagent’s outputs (diffs, reports, ApplicationPlan, CritiqueReport) and pass them to the next phase
4. Do not thin contracts or findings by rewriting `ApplicationPlan` / CritiqueReport in the parent (if wrong, re-launch the relevant skill as a Subagent)
5. If `human_gate.required`, do not apply until approved (including early formal rollout)
6. **Follow Canonical Critique Policy**: run Checkpoint Reviews at major quality boundaries and trigger Failure-Driven Critique on verification failure
7. If `solidsdd.verify` / `solidsdd.verify.formal` / `solidsdd.critique` fails, follow `loop_action` and suggested skills and **re-launch as a subagent** (or gate / stop)
8. Stop at a human gate when the auto-retry cap is exceeded
9. Leave a final summary listing each required Task / mechanical substitute and critique subject (isolation checklist), including any `cost_skip:B*`
10. When contracts already exist for this change, prefer ApplicationPlans that **extend** shared OpenAPI/OCL rather than re-scaffolding the package on every item
11. Before the first producer Task of a slice (and when pack would go stale after large edits), write **`items/<id>/context-pack.md`** (see [Context pack](#context-pack)) and pass its path in every Task prompt for that item
12. Persist `run-state.json` via **`scripts/solidsdd-run-state.sh`** (or Write/StrReplace on that file). Do **not** use free-form `python -c` / unbounded heredoc to mutate run-state / WorkPlan item status / change `status.json` ([run-state.md](../reference-src/run-state.md))

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
10. Update orchestrator state with **`scripts/solidsdd-run-state.sh`** (keep `solidsdd-next` read-only). Forbidden: free-form Python one-liners for `run-state.json` mutations

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
If **another skill continues in the same response** (e.g. implement right after judge), prefer Task for subagent-required skills to avoid crosstalk.

If a single verifiable acceptance criterion is already known, `solidsdd-loop` alone is enough. For multi-criterion or ambiguous requirements, use `solidsdd-run`.

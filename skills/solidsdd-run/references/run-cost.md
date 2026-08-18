# Run cost and evaluation samples

solid_sdd trades wall-clock agent time for **isolation and checkability**. Small domains can still be expensive if decomposition and orchestration multiply work. This note records cost drivers and required mitigations after the `inventory-reservation` end-to-end run (2026-08).

For the broader structural improvement plan to reduce Task counts and transition to Slice/Checkpoint-based orchestration, see [cost-reduction-plan.md](cost-reduction-plan.md).

## Execution Profile cost model

Before any of the below applies, `solidsdd-run` triages the change into an Execution Profile — see [triage.md](../reference-src/triage.md). The Canonical Consolidated Model and its cost skips (B1–B5) below describe the `standard`/`full` path only; `direct`/`thin` are a **different, cheaper scale**, not a further skip inside that same path:

| Profile | Outer Task-class steps | Per-change cost shape |
|---|---|---|
| `direct` (L0) | **0** | Inline edit + project test/lint/typecheck; no Task, no `run-state.json` |
| `thin` (L1) | **2** (normal path) | Task `solidsdd-implement` → Task `solidsdd-verify`; critique only on failure |
| `standard` (L2) | **4–6** (see below) | Full Canonical Consolidated Model |
| `full` (L3) | **4–6**, with fewer optional steps skipped | Same model as `standard`; cross-change/knowledge-consistency critique and formal-deferral justification become required rather than recommended |

**Do not confuse this with cost-skip B1–B5 below.** B1–B5 are mechanical, narrowly-scoped exceptions *inside* the `standard`/`full` pipeline (skip one Task inside a slice, or skip a duplicate integration verify). Execution Profile is a policy-level, phase-scale decision made once at Triage, before the pipeline starts. A `direct`/`thin` change never reaches B1–B5 because it never reaches the pipeline they apply to.

## Cost model (order of magnitude)

### Canonical Consolidated Model (Current Standard)

For a WorkPlan with **N** coherent property slices under the canonical consolidated slice model, expect roughly:

| Layer | Task-class steps (typical) |
|-------|----------------------------|
| Outer (`solidsdd-run`) | intake + brief + decompose + critique(work_plan) + integration verify + critique(integration) ≈ **4–6** |
| Each slice (`solidsdd-loop`) | Plan Slice Task + Plan Review (Checkpoint) + Implement Slice Task + Verify Slice Task ≈ **3–4** (normal green path) |

### Historical Baseline (Pre-Consolidation Fine-Grained Model)

Prior to the consolidated slice model, each producer artifact launched a separate subagent Task and matching critique:

| Layer | Task-class steps (historical fine-grained) |
|-------|--------------------------------------------|
| Outer (`solidsdd-run`) | intake + critique + brief + critique + decompose + critique (+ optional cross-change) + integration verify + critique ≈ **8–10** |
| Each slice (`solidsdd-loop`) | judge + critique + (apply-api + critique) + (apply-dbc + critique) + (derive-tests + critique) + implement + verify + critique ≈ **10–12** |

Wall-clock scales with **O(N × loop steps)**. Consolidated slice execution reduces loop steps per slice from ~10–12 down to ~3–4 while preserving verification and checkability boundaries.

## Required mitigations (orchestration)

1. **Keep `solidsdd-loop` orchestration structured across meaningful Phase boundaries.** Do **not** launch one Task whose prompt is "run the entire loop uncheckably". Maintain Subagent Task boundaries for `Plan Slice`, `Implement Slice`, `Verify Slice`, and `Failure-Driven Critique`.
2. **Use Consolidated Slice Execution with Checkpoint Reviews & Failure-Driven Critique.** Combine planning steps into `Plan Slice Task` (`judge` + API/DbC contract planning + test derivation), `Implement Slice Task`, and `Verify Slice Task`. Checkpoint Reviews run at major quality boundaries and full Critique subagents trigger on verification failure.
3. If the host cannot nest Task from a loop helper agent, **the run parent must drive loop steps itself** (Task per skill). Do not fall back to same-agent produce+critique except as an explicit isolation violation that is re-run or gated.
4. **Serialize only on real contention** (`touches` intersection or recorded heuristic). Prefer greenfield WorkPlans that use `depends_on` so serialization is intentional ([work-decomposition.md](../reference-src/work-decomposition.md)).
5. **Pass a context pack** into each Task ([execution-model.md](execution-model.md) — context pack): prefer pack paths/excerpts over re-reading full Brief/OpenAPI/OCL on every cold start.
6. **Mutate run-state only via `scripts/solidsdd-run-state.sh`** (or visible Write/StrReplace). Free-form Python for `run-state.json` causes host allowlist prompts that are not product gates.

## Allowed cost skips (B1–B5)

These are **explicit product rules**, not silent parent thinning. When used, record `cost_skip:B<n>` in `run-state.isolation_notes` and in any substitute artifact summary.

| Id | When | May skip / substitute | Must still do |
|----|------|------------------------|---------------|
| **B1** | ApplicationPlan targets are all `skip` and/or `defer` (no `apply`) | Additional adversarial Critique Task | Persist the ApplicationPlan (Plan Review / mechanical lint is still executed) |
| **B3** | Item `touches` has no implementation paths (`src/`, app package, etc.) **and** no `apply` target implies implement | `Implement Slice Task` | Contract apply/derive/verify as otherwise required |
| **B4** | WorkPlan has **exactly one** item **and** that item’s `verification-report.json` already covers `acceptance_of_whole` (and relevant Brief `success_criteria`) with pass | Duplicate **integration** `solidsdd-verify` | Keep the item verify; note `cost_skip:B4` and path to the reused report |
| **B5** | Prior item verify on this change used the **same** toolchain commands / same test suite and passed, **and** this item made **no code or contract-test edits** (skip-plan / docs-only) | Re-running the full suite inside `solidsdd-verify` | Still write `verification-report.json` that **cites** the prior report (command, timestamp/path, pass); run cheap existence/diff checks for OpenAPI/OCL if those are in scope. Launch Failure-Driven Diagnosis / Critique only if verification fails. |

**Never skip under these ids:** Checkpoint Reviews (e.g., Plan Review), or merging producer+review into one Task. Failure-driven Critique cannot be skipped if verification fails.

### B4 mechanical detection

`scripts/solidsdd-next.sh next` detects B4 automatically: when all WorkPlan items are `done`, the WorkPlan has **exactly one** item, and that item's `items/<id>/verification-report.json` has `result: pass` with `"acceptance_of_whole"` present in some check's `covers`, `next` recommends `action: knowledge_harvest` (skipping `integration_verify`) instead of the default `action: integration_verify`, with the reason spelled out. `integration_verify` stays in `legal_actions` so the orchestrator may still run it for extra rigor. For this to fire, the sole item's `solidsdd-verify` must actually tag `"acceptance_of_whole"` in `covers` when it demonstrably validates the whole Brief — see [solidsdd-verify](../skills/solidsdd-verify/SKILL.md) step 5. The orchestrator still records `cost_skip:B4` in `run-state.isolation_notes` and cites the reused report path per the table above.

## Required mitigations (decomposition)

See **Greenfield / shared-contract changes** and **Follow-on / co-delivered slices** in [work-decomposition.md](../reference-src/work-decomposition.md):

- Greenfield: foundation item first, narrow `touches`, do not stamp identical shared paths on every `ready` item.
- Follow-on: do **not** emit vocabulary-only foundation items; keep success+failure of the **same** operation in **one** item when they share an implementation path; merge items whose verify would be vacuous once a sibling implement is green.

### Evaluation sample — `add-list-holds` (2026-08)

Live replay used **N = 3** (OpenAPI/OCL vocabulary → authorized list → unauthorized list) ≈ **38** Task launches. A **N = 1** co-delivered plan (contracts + authorized + unauthorized in one Scenario/item) estimates ≈ **29** Tasks (**−24%** overall; **−45%** on loop-only steps) with the same outer framing/harvest. The gap was mostly redundant loops (vocabulary-only W1; W3 verify-only after W2 implement), not implementation size.

## Evaluation sample kinds

| Kind | Purpose | Cost expectation |
|------|---------|------------------|
| **Golden / framing** | Lint, schema, Brief/WorkPlan shapes | Low — may omit full loops |
| **Hand-maintained runnable** | CI `npm test` / adapters (e.g. historical arithmetic-api) | Medium — artifacts may not replay a full live run |
| **Live `solidsdd-run` replay** | Prove orchestrator + isolation end-to-end | High — budget time for O(N × loop steps); use greenfield mitigations |

Do not treat a live replay’s wall-clock as a defect in the *implementation size*; treat bad decomposition or collapsed isolation as defects in the *run*.

## Host toolchain thrash vs orchestration cost

Subagents often start **non-interactive** shells without mise/asdf PATH hooks. If each verify/implement Task rediscovers `npm`/`node`, the run looks “mysteriously slow” even when isolation is correct.

| Signal | Interpretation |
|--------|----------------|
| Task counts match O(N × loop steps); `host_toolchain.ready=true`; no `toolchain_rediscovery:` notes | **Expected solid_sdd orchestration cost** |
| Long shell turns with `find` / many `which`; `isolation_notes` contain `toolchain_rediscovery:<tool>:…` | **Host toolchain thrash** — fix PATH / mise; paste `.solidsdd/host-toolchain.json` `commands` into Tasks |
| `solidsdd-context` / probe shows `ready=false` before waves | **Stop and fix the host** before a multi-Task run |

Probe: `scripts/solidsdd-host-toolchain.sh --project-root .` (see [host-toolchain.md](../reference-src/host-toolchain.md)). Parents must copy Toolchain commands into verify/implement/derive Task prompts and forbid filesystem rediscovery when commands are present.

## Relation to hardening

Mechanical lint / `covers` / `run-state` reduce LLM-only hardness. Per-slice Task cost remains for real producers and reviewers. **Allowed cost skips (B1–B5)** and **context packs** are the explicit product speed-ups — do not invent additional skips in the parent without updating this doc and [execution-model.md](execution-model.md).

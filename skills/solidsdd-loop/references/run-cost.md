# Run cost and evaluation samples

solid_sdd trades wall-clock agent time for **isolation and checkability**. Small domains can still be expensive if decomposition and orchestration multiply work. This note records cost drivers and required mitigations after the `inventory-reservation` end-to-end run (2026-08).

## Cost model (order of magnitude)

For a WorkPlan with **N** property items, expect roughly:

| Layer | Task-class steps (typical) |
|-------|----------------------------|
| Outer (`solidsdd-run`) | intake + critique + brief + critique + decompose + critique (+ optional cross-change) + integration verify + critique ≈ **8–10** |
| Each slice (`solidsdd-loop`) | judge + critique + (apply-api + critique) + (apply-dbc + critique) + (derive-tests + critique) + implement + verify + critique ≈ **10–12** when both API and DbC apply |

So wall-clock scales closer to **O(N × loop steps)** than to lines of application code. Contract tests and `.solidsdd` JSON often dwarf `src/` in a sample repo — that is expected when every producer is critiqued.

## Required mitigations (orchestration)

1. **Keep `solidsdd-loop` on the outer parent session.** Do **not** launch one Task whose prompt is “run the entire loop for Wn”. That collapses producer and critique into one agent (or forces fake “separate write passes”) and violates [execution-model.md](execution-model.md).
2. **Each producer that ran → its own `solidsdd-critique` Task** (unless a [cost skip](#allowed-cost-skips-b1b5) applies). Never combine a producer and its matching critique in one Task; never combine `solidsdd-verify` and `critique(verification_report)` in one Task.
3. If the host cannot nest Task from a loop helper agent, **the run parent must drive loop steps itself** (Task per skill). Do not fall back to same-agent produce+critique except as an explicit isolation violation that is re-run or gated.
4. **Serialize only on real contention** (`touches` intersection or recorded heuristic). Prefer greenfield WorkPlans that use `depends_on` so serialization is intentional ([work-decomposition.md](../reference-src/work-decomposition.md)).
5. **Pass a context pack** into each Task ([execution-model.md](execution-model.md) — context pack): prefer pack paths/excerpts over re-reading full Brief/OpenAPI/OCL on every cold start.

## Allowed cost skips (B1–B5)

These are **explicit product rules**, not silent parent thinning. When used, record `cost_skip:B<n>` in `run-state.isolation_notes` and in any substitute artifact summary.

| Id | When | May skip / substitute | Must still do |
|----|------|------------------------|---------------|
| **B1** | ApplicationPlan targets are all `skip` and/or `defer` (no `apply`) | LLM Task `critique(application_plan)` → **mechanical** pass: parent runs `solidsdd-lint` (or equivalent) and writes `critique-application-plan.json` with `result: pass`, noting `cost_skip:B1` + lint summary | Persist the ApplicationPlan |
| **B2** | This item did not run `apply-api` / `apply-dbc` / `derive-tests` | The matching `critique(api_contracts)` / `critique(dbc_contracts)` / `critique(derived_tests)` | — |
| **B3** | Item `touches` has no implementation paths (`src/`, app package, etc.) **and** no `apply` target implies implement | `solidsdd-implement` Task | Contract apply/derive/verify as otherwise required |
| **B4** | WorkPlan has **exactly one** item **and** that item’s `verification-report.json` already covers `acceptance_of_whole` (and relevant Brief `success_criteria`) with pass | Duplicate **integration** `solidsdd-verify` + its critique | Keep the item verify + `critique(verification_report)`; note `cost_skip:B4` and path to the reused report |
| **B5** | Prior item verify on this change used the **same** toolchain commands / same test suite and passed, **and** this item made **no code or contract-test edits** (skip-plan / docs-only) | Re-running the full suite inside `solidsdd-verify` | Still write `verification-report.json` that **cites** the prior report (command, timestamp/path, pass); run cheap existence/diff checks for OpenAPI/OCL if those are in scope; then normal `critique(verification_report)` unless B1-style mechanical rules also apply |

**Never skip under these ids:** `critique(change_context|change_brief|work_plan)`, critique after a real `apply` / `derive-tests` / `implement` that edited artifacts, `critique(knowledge_harvest)` when candidates exist, or merging producer+critique into one Task.

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

Mechanical lint / `covers` / `run-state` reduce LLM-only hardness. Per-phase Task cost remains for real producers. **Allowed cost skips (B1–B5)** and **context packs** are the explicit product speed-ups — do not invent additional skips in the parent without updating this doc and [execution-model.md](execution-model.md).

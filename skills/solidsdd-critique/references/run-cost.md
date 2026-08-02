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
2. **Each producer → its own `solidsdd-critique` Task.** Never combine `solidsdd-verify` and `critique(verification_report)` in one Task.
3. If the host cannot nest Task from a loop helper agent, **the run parent must drive loop steps itself** (Task per skill). Do not fall back to same-agent produce+critique except as an explicit isolation violation that is re-run or gated.
4. **Serialize only on real contention** (`touches` intersection or recorded heuristic). Prefer greenfield WorkPlans that use `depends_on` so serialization is intentional ([work-decomposition.md](../reference-src/work-decomposition.md)).

## Required mitigations (decomposition)

See **Greenfield / shared-contract changes** in [work-decomposition.md](../reference-src/work-decomposition.md): foundation item first, narrow `touches`, do not stamp identical shared paths on every `ready` item.

## Evaluation sample kinds

| Kind | Purpose | Cost expectation |
|------|---------|------------------|
| **Golden / framing** | Lint, schema, Brief/WorkPlan shapes | Low — may omit full loops |
| **Hand-maintained runnable** | CI `npm test` / adapters (e.g. historical arithmetic-api) | Medium — artifacts may not replay a full live run |
| **Live `solidsdd-run` replay** | Prove orchestrator + isolation end-to-end | High — budget time for O(N × loop steps); use greenfield mitigations |

Do not treat a live replay’s wall-clock as a defect in the *implementation size*; treat bad decomposition or collapsed isolation as defects in the *run*.

## Relation to hardening

Mechanical lint / `covers` / `run-state` reduce LLM-only hardness. They do **not** remove per-phase Task cost. Further speed-ups (skipping critique on additive no-ops, batch apply) would be explicit product changes — not silent parent thinning.

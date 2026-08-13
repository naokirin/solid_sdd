---
name: solidsdd-loop
description: >-
  Orchestrate solid_sdd slice execution using the canonical Consolidated Slice Model
  (Plan -> Implement -> Verify) with Checkpoint and Failure-Driven Critique. Persists
  slice artifacts under items/<id>/ and honors run-state retry budgets.
license: MIT
---

# solidsdd.loop

## Purpose

Run the **slice** loop for one change intent (typically one verifiable acceptance criterion or coherent set of Scenarios). This skill is **orchestrator-only** — do not delegate `solidsdd.loop` itself to a subagent.

The primary goal of `solidsdd-loop` is **slice completion** (fulfilling acceptance criteria with verified code and consistent contracts), not executing a fixed list of Task steps.

For multi-criterion requirements, use **`solidsdd-run`** (decompose → WorkPlan → this loop per item → integration verify).

## References

- [execution-model.md](references/execution-model.md) — canonical orchestrator & slice execution rules
- [plan-slice-cheatsheet.md](references/plan-slice-cheatsheet.md) — **give this to the Plan Slice Task** (generated; consolidates judge + apply-api + apply-dbc + derive-tests)
- [adversarial-critique.md](references/adversarial-critique.md) — Checkpoint Reviews & Failure-driven Critique
- [human-gates.md](references/human-gates.md) — when to stop for a person
- [loop-retry.md](references/loop-retry.md) — verify/critique failure → retry / gate / stop
- [contract-layout.md](references/contract-layout.md) — default artifact paths
- [run-state.md](references/run-state.md) — **persist plans / critiques / retry budget (required)**; use `solidsdd-run-state` CLI
- [run-state.schema.json](references/run-state.schema.json)
- [run-cost.md](references/run-cost.md) — isolation; cost skips B1–B5; context pack; host toolchain thrash prevention
- [project-rule.mdc](references/project-rule.mdc) — project rule
- [host-toolchain.md](references/host-toolchain.md) — preflight; paste commands into Tasks

## Canonical Execution Model (Consolidated Slice Model)

The standard execution model consolidates fine-grained subagent passes into meaningful slice milestones:

```text
Context
  ↓
Plan Slice Task          (judge + API/DbC contract design + derive tests)
  ↓
Plan Review              (Checkpoint / Mechanical Lint)
  ↓
Implement Slice Task     (code edits matching contracts)
  ↓
Verify Slice Task        (run contract tests & verification)
  ↓ (if failed)
Failure-Driven Review    (Diagnose → Fix → Re-verify)
  ↓
Complete Slice
```

### Execution Policy

| Phase | Execution Mode | Description |
|-------|----------------|-------------|
| `solidsdd-context` & Context Pack | Parent Agent | Inspect stack, write `items/<id>/context-pack.md` |
| `Plan Slice` Task | Subagent Task | Determine contract density, design OpenAPI/OCL changes, derive tests |
| `Plan Review` | Checkpoint / Parent | Deterministic lint / optional Checkpoint Critique |
| `Implement Slice` Task | Subagent Task | Write application code edits (skipped under B3 if docs-only) |
| `Verify Slice` Task | Subagent Task | Run tests & contract verification (B5 reuse if unchanged) |
| `Failure-Driven Review` | Subagent Task (on failure only) | Launch targeted Critique / Diagnosis when verification fails |

Do **not** launch separate subagent Tasks for every intermediate file write (`apply-api`, `apply-dbc`, `derive-tests`) in standard runs. Treat intermediate contracts as artifacts produced during the slice lifecycle.

## Canonical Sequence

1. **Resolve Slice Context**: Read `change_id` / `item_id` / artifact dir. Check `run-state.json`; resume from recorded phase if interrupting state exists.
2. **Context & Pack (Parent)**: Run `solidsdd-context` and snapshot host toolchain. Write `.solidsdd/changes/<change_id>/items/<item_id>/context-pack.md`. When a clearly same-shape prior item exists, name it as a precedent to adapt — see [execution-model.md](references/execution-model.md) "Context pack".
3. **Plan Slice (Task Subagent)**: Launch a single **Plan Slice** Task.
   - Outputs: `application-plan.json`, updated OpenAPI/OCL contracts, and derived contract test files.
   - Point the Task at **[plan-slice-cheatsheet.md](references/plan-slice-cheatsheet.md)** (a generated concatenation of `solidsdd-judge` + `solidsdd-apply-api` + `solidsdd-apply-dbc` + `solidsdd-derive-tests`'s SKILL.md + primary adapter reference) instead of naming all four skills' paths separately — a live diagnostic measurement (2026-08) found most of a Plan Slice Task's time going to re-reading those same four skills' worth of onboarding docs from scratch on every slice. The cheat sheet links to the full individual skills for edge cases (GraphQL, RSpec, exact schema validation, human-gate detail).
   - Update `run-state.json` (`loop_phase: plan`).
4. **Plan Review (Checkpoint)**: Run deterministic `scripts/solidsdd-lint.sh`. If human gate is required, stop and await approval before implementation.
5. **Implement Slice (Task Subagent)**: Launch **Implement Slice** Task (unless cost skip **B3** applies for non-code items). Update `run-state.json` (`loop_phase: implement`).
6. **Verify Slice (Task Subagent)**: Launch **Verify Slice** Task. Run contract suite and verification checks. Write `verification-report.json`. Update `run-state.json` (`loop_phase: verify`).
7. **Failure-Driven Diagnosis (on failure only)**:
   - If verification **passes** → proceed to Step 8.
   - If verification **fails** → launch **Critique / Diagnosis Task** (`subject: verification_report` or targeted component failure). Follow `loop-retry.md` (Retry → Fix Task → Re-verify, max 3 budget). If verify fails again after a fix and critique runs a second time on the same subject, pass the prior `CritiqueReport` into that Task's prompt so it follows [adversarial-critique.md](references/adversarial-critique.md) "Retry critique" (targeted re-check, not full re-derivation).
8. **Complete Slice**: Update `run-state.json` item status to `done` (`solidsdd-run-state set-item --id <id> --status done --loop-phase done --sync-work-plan`). Record metrics via `solidsdd-run-state record-metrics`.

## Success Criteria (Outcome-based)

A slice execution is successful when **all** of the following outcome conditions are met (not whether a list of Task steps was completed):

1. **Requirement Coverage**: The slice's acceptance criteria (`covers` IDs / Gherkin Scenarios) are fully satisfied.
2. **Contract Consistency**: OpenAPI, DbC (OCL), and test specifications are aligned without contradictions.
3. **Implementation Completeness**: Necessary source code changes exist and function as specified.
4. **Verification Success**: All contract tests and verification checks pass cleanly (`verification-report.json` with status `pass`).

## Isolation & Task Guidelines

Each Task prompt must include:
- Skill ID and path to installed `solidsdd-*/SKILL.md`
- Project root directory and **Context Pack Path** (`items/<id>/context-pack.md`)
- Verbatim **Toolchain commands** from `.solidsdd/host-toolchain.json`
- Explicit scope constraints and expected return paths

Record metrics (`task_launch_count`, `critique_count`) in `run-state.json` via `scripts/solidsdd-run-state.sh`.

---

## Legacy / Fine-Grained Mode (Debug & Historical)

> [!NOTE]
> The fine-grained mode (launching separate subagent Tasks per individual artifact: `judge` → `critique` → `apply-api` → `critique` → `apply-dbc` → `critique` → `derive-tests` → `critique`) is preserved for **strict debugging, legacy compatibility, or explicit manual inspection only**. It is **not** used during standard `solidsdd-run` or `solidsdd-loop` orchestration.

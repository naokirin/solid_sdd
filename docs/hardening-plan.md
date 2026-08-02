# Hardening plan — mechanical assurance for requirements quality

**Status:** draft (post Phase 4)  
**Date:** 2026-08-03  
**Context:** External review of the repo concluded that solid_sdd already structures phase artifacts well (run/loop split, subagent isolation, critique severity calibration including F10), but **“requirements hardness” still bottoms out in LLM judgment**. This document turns that review into an ordered improvement plan.

**Related:** [roadmap.md](roadmap.md), [phase4.md](phase4.md), [feedback-tuning.md](feedback-tuning.md), [architecture.md](architecture.md), [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md), [../reference-src/contract-layout.md](../reference-src/contract-layout.md)

## Diagnosis

| Layer | Today | Gap |
|-------|-------|-----|
| Structured producers | Change Context, ChangeBrief, WorkPlan, ApplicationPlan, CritiqueReport, VerificationReport | Strong |
| Adversarial critique | Separate Task; severity calibrated (F10) | Critique itself is still one LLM pass |
| Mechanical verification | Redocly + contract tests (post-apply) | Little/no deterministic check on *requirements → plan coverage* |
| Run durability | Brief/WorkPlan/status persisted | ApplicationPlan / Critique / Verification / retry budget mostly conversational |

**Goal:** Raise the share of assurance that does **not** depend on LLM reading, without discarding the existing critique / subagent design.

**Non-goals (this plan):** Replacing Gherkin as acceptance SoT; mandating formal methods; rewriting Phase 0–4 delivered skills from scratch.

## Principles

1. **IDs before prose checks** — Coverage and drift detection must be set operations on identifiers, not free-text matching.
2. **Deterministic lint before critique** — Critique judges *adequacy of coverage*, not *whether coverage exists*.
3. **Persist orchestrator state** — Retry budgets, wave progress, and phase artifacts must survive session loss.
4. **Schema-first; prefer additive fields** — Keep `version: "1"` until a documented migration exists. **Exception (resolved):** ChangeBrief scope lists hard-break to `{ id, text }` objects (no dual-read).
5. **Critique stays LLM-native** — Soften or harden severity via eval corpus, not by expanding critique into a second schema validator.

## Recommended order

Primary sequence from the review (adopted here):

1. **ID traceability** (`covers` chain)
2. **Deterministic pre-critique lint**
3. **Run / loop state persistence**
4. **NFR as structured SoT** + **critique eval corpus** (parallelizable)
5. **EARS (optional layer)** when requirement-sentence quality becomes the bottleneck
6. Supporting: CI, tool-enforced read-only, approval records, richer examples, schema evolution policy

---

## Workstream A — ID traceability (P0)

### Problem

`in_scope` / `success_criteria` are `string[]`. WorkPlan items, ApplicationPlan targets, and VerificationReport checks have no `covers`. Critique decides coverage by natural-language match (`adversarial-critique.md`: uncovered Brief scope → major).

### Target model

Full chain through Brief → WorkPlan → Gherkin → ApplicationPlan → Verification (per original review):

```text
ChangeBrief.in_scope[id] / success_criteria[id] / out_of_scope[id]
    → WorkPlan.item.covers[]              # Brief ids (R*, SC*, …)
    → Feature / Scenario                  # same ids via tags (e.g. @R1) on Scenario
        → ApplicationPlan.target.covers[] # WorkPlan item ids (W*)
            → VerificationReport.check.covers[]
```

WorkPlan keeps `feature_path` / `scenario_name` as location hints; **coverage authority** is `covers` + Scenario tags, not prose match.

### Schema / artifact changes (sketch)

| Artifact | Change |
|----------|--------|
| `change-brief.schema.json` | **Breaking:** `in_scope` / `success_criteria` / `out_of_scope` → array of `{ id, text }` only (ids e.g. `R1`, `SC1`, `X1`). No string-array dual-read. |
| `work-plan.schema.json` | `items[].covers: string[]` (required, minItems 1 → Brief ids); keep `feature_path` / `scenario_name` |
| `requirements/**/*.feature` | Each Scenario owned by a WorkPlan item must tag the Brief ids it covers (e.g. `@R1 @SC1`) |
| `application-plan.schema.json` | `targets[].covers?: string[]` (WorkPlan item ids) |
| `verification-report.schema.json` | `checks[].covers?: string[]` |
| Examples + report | Migrate arithmetic-api; emit coverage matrix in `solidsdd-report` |

### Skill / reference updates

- `change-brief.md`, `work-decomposition.md`, `adversarial-critique.md`, `change-report.md`, `gherkin-requirements.md`
- `solidsdd-brief` / `decompose` / `judge` / `verify` / `report` / `critique` steps
- Example `arithmetic-api` Brief + WorkPlan + Feature tag migration (hard cut; update all in-repo consumers)

### Acceptance

- [x] Uncovered `R*` / `SC*` detectable by a script with **no** LLM (Brief ↔ WorkPlan ↔ Scenario tags)
- [x] Critique calibration text shifts from “is it covered?” to “is the cover *adequate*?”
- [x] Report can render a coverage matrix from JSON + Feature tags alone

### Migration

- **Hard break** on Brief field shape: consumers and examples must use `{ id, text }` objects. No dual-read of bare strings. Bump docs/install notes that old Briefs are invalid; migrate in-repo examples in the same change.
- [x] `examples/arithmetic-api` Brief / WorkPlan / Features migrated (2026-08-03)

---

## Workstream B — Deterministic lint before critique (P0)

### Problem

Many `major` conditions in `adversarial-critique.md` are graph/parse/schema checks today performed by the critique agent.

### Deliverable

`scripts/solidsdd-lint.sh` (or `scripts/solidsdd-lint/*`) invoked as **Step 0/1 of `solidsdd-critique` only** (initial scope — avoid wiring into run/loop gates until the lint surface is stable). Orchestrators keep calling critique as today; critique must run lint before LLM review.

| Check | Mechanism |
|-------|-----------|
| JSON Schema validation (Brief, WorkPlan, ApplicationPlan, Critique, Verification, gates, status) | ajv / check-jsonschema |
| `change_id` == directory name | string compare |
| `depends_on` acyclic + ids resolve | graph DFS/BFS |
| `acceptance_criterion` has Given/When/Then; ≤1 Scenario per item | lightweight Gherkin parse |
| `covers` completeness / unknown ids (Brief ↔ WorkPlan ↔ Scenario tags) | set difference (needs Workstream A) |
| Ambiguity lexicon (JA/EN) | word/phrase lint → findings seed for `unverifiable_acceptance` |
| Optional: `touches` overlap for wave contention | set intersection (Workstream C/F) |

Lint output should be machine-readable (JSON) so critique can **import** hard fails as findings (`blocker`/`major`) rather than rediscovering them.

**Out of initial scope:** invoking lint from `solidsdd-run` / `solidsdd-loop` outside critique; expand later if needed.

### Acceptance

- [x] Lint fails closed on schema / cycle / uncovered id without calling an LLM
- [x] Critique SKILL.md requires lint first; loop-retry maps lint-only fails to the owning producer skill
- [x] Ambiguity lexicon documented and extensible per working language
- [x] run/loop do not gain a separate lint gate in M1

---

## Workstream C — Orchestrator state persistence (P0/P1)

### Problem

`contract-layout.md` does not define storage for ApplicationPlan / CritiqueReport / VerificationReport. `status.json` is only `active|done|abandoned`. `max_auto_retries = 3` is conversational. Waves cannot reliably resume or audit density rationale.

### Target layout

```text
.solidsdd/changes/<change_id>/
  run-state.json                 # phase, wave, item statuses, retry remaining, isolation notes
  items/<item_id>/
    application-plan.json
    critique-application-plan.json
    verification-report.json
    critique-verification-report.json
    # plus other phase critiques as needed (api/dbc/derived/formal)
```

Keep existing Brief / WorkPlan / Context paths. Update `contract-layout.md`, `change-lifecycle.md`, `change-report.md` discovery rules (prefer `items/<id>/` over ad-hoc `.solidsdd/application-plan*.json`).

### `run-state.json` (sketch)

- `version`, `change_id`
- `phase` / `wave_index`
- `retry`: `{ remaining, max, last_suggested_skills[] }`
- `items`: map of WorkPlan id → `{ status, blocked_reason?, last_loop_action? }`
- Convention: **read at step start, write at step end** (loop + run)

### Acceptance

- [x] Interrupted run can resume from `run-state.json` + item artifacts without re-deriving density from chat
- [x] Retry budget is a state machine, not model memory
- [x] Report / human gate can cite persisted ApplicationPlan paths

Shipped: `schemas/run-state.schema.json`, [run-state.md](../reference-src/run-state.md), orchestrator skill + layout updates (2026-08-03).

---

## Workstream D — Structured NFRs (P1)

### Problem

Change Context §4 is a Markdown table. Cannot mechanically assert six qualities considered, in-scope NFRs have thresholds, or integration verify covered them. Loop verify does not consume NFRs.

### Target

- **Decision:** `nfr.json` is SoT from day one of this workstream (no Markdown→JSON interim). Intake writes/updates `nfr.json`; `change-context.md` §4 is a projection only.
- In-scope NFRs require `threshold` + `measurement`; optional `verified_by`
- Integration verify / lint: fail if in-scope NFR lacks verification evidence when status is `done`

Ids (`NFR1`, …) should join the `covers` story where WorkPlan/verify claims NFR satisfaction.

### Acceptance

- [x] Missing quality row / empty in-scope NFR without threshold → lint fail
- [x] Example arithmetic-api still valid with explicit `status: out_of_scope` + rationale for Performance/Security

Shipped: `schemas/nfr.schema.json`, intake writes `nfr.json`, lint + arithmetic-api sample (2026-08-03).

---

## Workstream E — Critique regression corpus (P1)

### Problem

F10 softened severity; no eval proves the calibration still holds when `adversarial-critique.md` changes.

### Target

```text
evals/critique/
  cases/001-missing-out-of-scope/{input.json, expected.json}
  cases/002-vacuous-pre/...
  cases/003-happy-path-only-api/...
  cases/010-clean-standard-density/   # must pass
  ...
```

- 10–20 cases; **~half must-pass** (F10 regression)
- `expected.json`: required severity class, must-include `suggested_next_skills`, forbidden over-fail
- Optional: run 3× and record variance

Wire into CI once Workstream G exists (even if first version is manual checklist).

### Acceptance

- [x] Editing severity table without updating corpus fails CI or documented eval script
- [x] Clean standard-density fixtures pass under current calibration

Shipped: `evals/critique/` (12 cases) + `scripts/solidsdd-critique-eval.py` (deterministic checkers; LLM variance deferred).

---

## Workstream F — Supporting hardening (P1/P2)

| Item | Action | Priority |
|------|--------|----------|
| **CI** | GitHub Actions: `sync-skill-references.sh --check`, schema validate examples, run example tests, SKILL frontmatter sanity | P1 — **done** (`.github/workflows/ci.yml`) |
| **Read-only tools** | Where supported (e.g. Claude Code `allowed-tools`), restrict critique (and optionally intake/brief/decompose write surfaces); document Cursor limitation | P2 — **done** (`solidsdd-critique` frontmatter + SKILL note) |
| **Cross-change consistency** | New critique subject and/or intake section: collide with prior Scenarios / prior `out_of_scope` | P2 — **done** (`cross_change_consistency` + Context framing) |
| **Gate approval record** | `gate-approval.json` (who/when/scope/partial); **approver is free-text** (no git-user / `--approver` requirement); resume protocol checks the record exists when resuming past a gate | P2 — **done** (`gate-approval.schema.json` + human-gates) |
| **`touches` on WorkPlan items** | Paths for wave contention via set ops; update `solidsdd-run` | P2 — **done** |
| **`change_id` on WorkPlan / ApplicationPlan / VerificationReport** | Explicit membership when artifacts move | P2 — **done** (optional fields + lint) |
| **Schema evolution policy** | Document additive-only on `version: "1"`; process for `version: "2"` + migrators | P2 — **done** ([schema-evolution.md](schema-evolution.md)) |
| **Richer example** | One non-arithmetic domain (inventory reservation, approval+authz, or closing/settlement) to stress intake/brief/critique | P2 — **done** (`examples/inventory-reservation`) |
| **EARS layer** | Optional: Brief `in_scope[].text` (or dedicated field) in EARS patterns; Gherkin remains acceptance. Especially unwanted-behavior / state-driven | P3 — **entry note done** ([ears-requirements.md](../reference-src/ears-requirements.md)); pattern lint deferred |

---

## Workstream G — EARS (P3)

- Gherkin = how we verify; EARS = what the system shall do
- Natural entry: id’d `in_scope` texts (Workstream A) authored as EARS sentences
- Forces explicit unwanted-behavior and state-driven shapes that today are prose rules in `gherkin-requirements.md`
- Do **not** block A–E on EARS
- **M4:** optional authoring note shipped; mechanical EARS detection remains future

---

## Suggested milestones

### Milestone M1 — Coverage becomes mechanical

- [x] Workstreams **A** + **B** (schema hard-break + Scenario tags + critique-only lint + skill/reference sync)
- [x] Migrate `examples/arithmetic-api` Brief / WorkPlan / Features
- [x] Update critique docs so coverage holes are lint/major imports, not sole LLM discovery

Shipped artifacts: `schemas/*` (`covers` / scoped items), `scripts/solidsdd-lint.sh`, reference + skill updates.

### Milestone M2 — Runs are resumable and auditable

- [x] Workstream **C**
- [x] Report discovery + human-gates resume read `run-state` / item plans

### Milestone M3 — NFR + critique quality bar

- [x] Workstreams **D** + **E**
- [x] First GitHub Actions workflow (**F**/CI subset)

### Milestone M4 — Ecosystem / edge hardness

- [x] Remaining **F** items + optional **G** entry (EARS note)
- [x] Domain example beyond arithmetic (`examples/inventory-reservation`)
- External feedback continues via [feedback-tuning.md](feedback-tuning.md)

## Success metrics

| Metric | Baseline (today) | Target |
|--------|------------------|--------|
| Uncovered Brief scope detection | LLM critique only | Script exit ≠ 0 |
| Critique must-pass fixtures | 0 | ≥5 green fixtures |
| Resume after mid-loop crash | Not defined | Documented resume from `run-state.json` |
| In-scope NFR without threshold | Allowed in Markdown | Lint fail |
| CI on PR | None (pre-commit sync only) | Sync + schema + example tests |

## Explicit non-regressions

- Keep F10 stance: polish ≠ `major`; checkability holes remain fail
- Keep producer ≠ evaluator (Task critique)
- Keep ChangeBrief as scope authority; Change Context as framing; Gherkin as acceptance structure; OCL/OpenAPI as machine-checkable SoT for the active change
- Do not thin plans in the parent to satisfy lint or critique

## Resolved decisions (2026-08-03)

| # | Topic | Decision |
|---|--------|----------|
| 1 | Brief field migration | **Hard break** to `{ id, text }` objects only. No dual-read of bare strings. Migrate in-repo examples in the same change. |
| 2 | `covers` granularity | **Full chain:** Brief ids ↔ WorkPlan `covers` ↔ Feature/Scenario tags ↔ ApplicationPlan / Verification `covers`. |
| 3 | Where lint runs | **Critique-only** initially (Step 0/1 of `solidsdd-critique`). No separate run/loop lint gate in M1. |
| 4 | NFR SoT | **`nfr.json` is SoT** from introduction; Change Context §4 is a projection (no Markdown-first interim). |
| 5 | Approval identity | **Free-text approver** allowed in `gate-approval.json`; no mandatory git identity or CLI flag. |

## Document maintenance

When a workstream lands, checkboxes here and a short row in [feedback-tuning.md](feedback-tuning.md) intake log. Link new schemas/scripts from [architecture.md](architecture.md) and [contract-layout.md](../reference-src/contract-layout.md). Track progress under **Phase 5: Hardening** in [roadmap.md](roadmap.md).

# Human gates (Phase 2)

A **human gate** pauses autonomous `solidsdd-loop` or `solidsdd-run` progress until a person approves, rejects, or amends policy.

## When required

Set `human_gate.required: true` (plan-level and/or per target **or** Change Context gate / ChangeBrief / WorkPlan / item) when any of:

| Condition | Typical trigger |
|-----------|-----------------|
| **Change Context framing** | Material `agent_default` tech (language, API style, persistence, contract approach); user intent vs repo stack conflict; new security/money NFR in §4; blocking §7 questions; low framing confidence — see [change-context.md](change-context.md). **Do not** gate when the initial user instruction already settled those decisions |
| Breaking API change | Removed fields, stricter types, status code changes, renames without compatibility |
| Money / ledger boundary | Payments, balances, fees, refunds |
| AuthZ / session boundary | New permission checks, role model changes (optional gate; prefer gate when also `breaking` or `low_confidence`) |
| Low confidence | Judge cannot map intent to axes; missing stack context; conflicting requirements; **brief** has blocking `open_questions`; **decompose** cannot form checkable Gherkin Scenarios |
| **Knowledge harvest** | Non-empty `knowledge-harvest.json` candidates, or agent-judged durable knowledge needing confirmation before writing `knowledge/` — see [knowledge.md](knowledge.md). **Always** gate before applying promote / writing knowledge files |
| `formal` | Always gate in early Phase 3 rollout when `status` would be `apply` |

## Plan / Brief / WorkPlan fields

```json
"human_gate": {
  "required": true,
  "reason": "breaking_change on Operation enum removal"
}
```

Targets may repeat a narrower `human_gate` for location-specific approval. ChangeBrief, WorkPlan, and items use the same shape.

## Change Context gate artifact

Intake writes `.solidsdd/changes/<change_id>/change-context-gate.json` ([change-context-gate.schema.json](../schemas/change-context-gate.schema.json)):

```json
{
  "version": "1",
  "human_gate": { "required": false, "reason": "…" },
  "confidence": "high",
  "decisions_to_confirm": []
}
```

When `required: true`, list concrete `decisions_to_confirm` for the human.

## Gate approval record (required on resume)

When a human approves (or partially approves) a gate, **write** a `GateApproval` JSON before resuming ([gate-approval.schema.json](../schemas/gate-approval.schema.json)):

| Path | Use |
|------|-----|
| `.solidsdd/changes/<change_id>/gate-approval.json` | Latest approval (overwrite OK for same scope when re-approving) |
| `.solidsdd/changes/<change_id>/gate-approvals/<iso>-<scope>.json` | Optional append-only history |

```json
{
  "version": "1",
  "change_id": "initial-calculator",
  "approved_at": "2026-08-03T12:00:00Z",
  "approver": "alice (PM)",
  "scope": "change_context",
  "decision": "approve",
  "note": "Confirmed OpenAPI + in-process memory",
  "artifact_paths": [
    ".solidsdd/changes/initial-calculator/change-context.md",
    ".solidsdd/changes/initial-calculator/change-context-gate.json"
  ]
}
```

- **`approver` is free-text** (name / handle / role). No git identity or CLI flag required.
- `decision: approve_partial` **must** include `partial.allowed` / `partial.deferred_or_refused`; then re-judge or defer refused targets per resume rules below.
- Orchestrators **must not resume** past a gate that was `required: true` unless a matching `gate-approval.json` (or history entry) exists with `decision` `approve` or `approve_partial` for that `scope`. Conversation-only approval is insufficient for auditability.

## Orchestrator behavior (`solidsdd-loop`)

1. After `solidsdd-judge`, **persist** ApplicationPlan under `.solidsdd/changes/<change_id>/items/<item_id>/application-plan.json`, then run **Task** `solidsdd-critique` (`subject: application_plan`) and persist the CritiqueReport beside it. Update `run-state.json` ([run-state.md](run-state.md)).
2. If any `human_gate.required` is true → **stop before apply**; set item `status` / `loop_phase` accordingly in `run-state.json`.
3. Final summary must list gate reasons and waiting locations (and cite persisted plan paths).
4. Do not thin the plan to avoid the gate.
5. Resume only after explicit human approval **and** a written `gate-approval.json` (or updated plan from a re-run of `solidsdd-judge` under new instructions). On resume, **re-read** `items/<id>/application-plan.json` and `run-state.json`—do not reconstruct density from chat alone.

### Resume after approval

When the human approves:

1. Write `gate-approval.json` (`scope: application_plan` or `formal_apply` as appropriate).
2. Keep the approved `ApplicationPlan` on disk (do not strip `formal` or lower density).
3. Continue from the interrupted `loop_phase` in `run-state.json`:
   - pending `api` / `dbc` → apply-* → **critique** (persist) → derive-tests → **critique** → implement → verify → **critique** as usual
   - pending `formal` → `solidsdd-apply-formal` → **critique** → `solidsdd-verify-formal` → **critique**
4. If approval is **partial** (e.g. allow API but not formal), record `approve_partial`, re-run `solidsdd-judge` with that instruction as a subagent, or set the refused target to `defer`/`skip` only via a new judge plan—not by parent edits.

## Orchestrator behavior (`solidsdd-run`)

1. After `solidsdd-intake`, create/update `run-state.json`; run **Task** `solidsdd-critique` (`subject: change_context`); persist critique JSON when practical.
2. If `change-context-gate.json` has `human_gate.required` → **stop before brief** until approved (or re-intake after amendment); set `phase` / `stopped_reason` in `run-state.json`; on approval write `gate-approval.json` with `scope: change_context`.
3. After `solidsdd-brief`, run **Task** `solidsdd-critique` (`subject: change_brief`).
4. If ChangeBrief has `human_gate.required` → **stop before decompose** until approved; write `gate-approval.json` with `scope: change_brief`.
5. After `solidsdd-decompose`, initialize `items` in `run-state.json` from the WorkPlan; run **Task** `solidsdd-critique` (`subject: work_plan`). Optionally run **Task** `solidsdd-critique` (`subject: cross_change_consistency`) when prior Features / prior change `out_of_scope` exist.
6. If WorkPlan or any item has `human_gate.required` → **stop before launching slice loops** (or before that item’s loop); write `gate-approval.json` with `scope: work_plan`.
7. Do not thin Change Context, ChangeBrief, or WorkPlan to avoid the gate.
8. After approval + `gate-approval.json`, resume from `run-state.json` `phase` with the approved artifacts; continue via brief/decompose and/or `solidsdd-loop` as appropriate.
9. After successful integration verify (+ critique): **Task** `solidsdd-knowledge` (`mode: harvest`) → write `knowledge-harvest.json`; set `phase: knowledge_harvest`. Optionally **Task** `solidsdd-critique` (`subject: knowledge_harvest`). If `human_gate.required` → **stop before `done`** until `gate-approval.json` with `scope: knowledge_harvest`; on approve apply selected candidates (CLI promote / hand-authored files + links), then mark change `done`. On reject/skip with empty apply set, still mark `done` after recording decisions on candidates.

## Optional human-readable report

When stopping for a gate (or after intake / Brief for confirmation), the orchestrator or agent **may suggest** running manual `solidsdd-report` so humans can review demand / NFR / tech / design so far as Markdown (optional HTML). This is **not** a required gate and does not change SoT artifacts. See [change-report.md](change-report.md).

## Defaults

- **Change Context**: gate only when framing triggers fire; **clear initial instruction → no gate**.
- **Additive, non-breaking** API/DbC work with clear context: gate only when other modifiers fire (`breaking_change`, money, low confidence, formal apply).
- Evaluation / sample work: same rule—do not gate routine additive changes or clear sample stacks.
- Production defaults may set stricter always-gate rules via project rule overrides.
- Formal `apply` in early Phase 3: **always** gate.
- Knowledge harvest apply: **always** gate when candidates are non-empty (never auto-promote).

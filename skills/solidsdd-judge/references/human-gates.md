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

## Orchestrator behavior (`solidsdd-loop`)

1. After `solidsdd-judge`, **persist** ApplicationPlan under `.solidsdd/changes/<change_id>/items/<item_id>/application-plan.json`, then run **Task** `solidsdd-critique` (`subject: application_plan`) and persist the CritiqueReport beside it. Update `run-state.json` ([run-state.md](run-state.md)).
2. If any `human_gate.required` is true → **stop before apply**; set item `status` / `loop_phase` accordingly in `run-state.json`.
3. Final summary must list gate reasons and waiting locations (and cite persisted plan paths).
4. Do not thin the plan to avoid the gate.
5. Resume only after explicit human approval in the conversation (or updated plan from a re-run of `solidsdd-judge` under new instructions). On resume, **re-read** `items/<id>/application-plan.json` and `run-state.json`—do not reconstruct density from chat alone.

### Resume after approval

When the human approves:

1. Keep the approved `ApplicationPlan` on disk (do not strip `formal` or lower density).
2. Continue from the interrupted `loop_phase` in `run-state.json`:
   - pending `api` / `dbc` → apply-* → **critique** (persist) → derive-tests → **critique** → implement → verify → **critique** as usual
   - pending `formal` → `solidsdd-apply-formal` → **critique** → `solidsdd-verify-formal` → **critique**
3. If approval is **partial** (e.g. allow API but not formal), re-run `solidsdd-judge` with that instruction as a subagent, or set the refused target to `defer`/`skip` only via a new judge plan—not by parent edits.

## Orchestrator behavior (`solidsdd-run`)

1. After `solidsdd-intake`, create/update `run-state.json`; run **Task** `solidsdd-critique` (`subject: change_context`); persist critique JSON when practical.
2. If `change-context-gate.json` has `human_gate.required` → **stop before brief** until approved (or re-intake after amendment); set `phase` / `stopped_reason` in `run-state.json`.
3. After `solidsdd-brief`, run **Task** `solidsdd-critique` (`subject: change_brief`).
4. If ChangeBrief has `human_gate.required` → **stop before decompose** until approved.
5. After `solidsdd-decompose`, initialize `items` in `run-state.json` from the WorkPlan; run **Task** `solidsdd-critique` (`subject: work_plan`).
6. If WorkPlan or any item has `human_gate.required` → **stop before launching slice loops** (or before that item’s loop).
7. Do not thin Change Context, ChangeBrief, or WorkPlan to avoid the gate.
8. After approval, resume from `run-state.json` `phase` with the approved artifacts; continue via brief/decompose and/or `solidsdd-loop` as appropriate.

## Optional human-readable report

When stopping for a gate (or after intake / Brief for confirmation), the orchestrator or agent **may suggest** running manual `solidsdd-report` so humans can review demand / NFR / tech / design so far as Markdown (optional HTML). This is **not** a required gate and does not change SoT artifacts. See [change-report.md](change-report.md).

## Defaults

- **Change Context**: gate only when framing triggers fire; **clear initial instruction → no gate**.
- **Additive, non-breaking** API/DbC work with clear context: gate only when other modifiers fire (`breaking_change`, money, low confidence, formal apply).
- Evaluation / sample work: same rule—do not gate routine additive changes or clear sample stacks.
- Production defaults may set stricter always-gate rules via project rule overrides.
- Formal `apply` in early Phase 3: **always** gate.

# Human gates (Phase 2)

A **human gate** pauses autonomous `solidsdd-loop` progress until a person approves, rejects, or amends policy.

## When required

Set `human_gate.required: true` (plan-level and/or per target) when any of:

| Condition | Typical trigger |
|-----------|-----------------|
| Breaking API change | Removed fields, stricter types, status code changes, renames without compatibility |
| Money / ledger boundary | Payments, balances, fees, refunds |
| AuthZ / session boundary | New permission checks, role model changes (optional gate; prefer gate when also `breaking` or `low_confidence`) |
| Low confidence | Judge cannot map intent to axes; missing stack context; conflicting requirements |
| `formal` | Always gate in early Phase 3 rollout when `status` would be `apply` |

## Plan fields

```json
"human_gate": {
  "required": true,
  "reason": "breaking_change on Operation enum removal"
}
```

Targets may repeat a narrower `human_gate` for location-specific approval.

## Orchestrator behavior (`solidsdd-loop`)

1. After `solidsdd-judge`, run **Task** `solidsdd-critique` (`subject: application_plan`). Resolve critique retries before treating the plan as ready.
2. If any `human_gate.required` is true → **stop before apply**.
3. Final summary must list gate reasons and waiting locations.
4. Do not thin the plan to avoid the gate.
5. Resume only after explicit human approval in the conversation (or updated plan from a re-run of `solidsdd-judge` under new instructions).

### Resume after approval

When the human approves:

1. Keep the approved `ApplicationPlan` (do not strip `formal` or lower density).
2. Continue from the interrupted step:
   - pending `api` / `dbc` → apply-* → **critique** → derive-tests → **critique** → implement → verify → **critique** as usual
   - pending `formal` → `solidsdd-apply-formal` → **critique** → `solidsdd-verify-formal` → **critique**
3. If approval is **partial** (e.g. allow API but not formal), re-run `solidsdd-judge` with that instruction as a subagent, or set the refused target to `defer`/`skip` only via a new judge plan—not by parent edits.

## Defaults

- **Additive, non-breaking** API/DbC work with clear context: gate only when other modifiers fire (`breaking_change`, money, low confidence, formal apply).
- Evaluation / sample work: same rule—do not gate routine additive changes.
- Production defaults may set stricter always-gate rules via project rule overrides.
- Formal `apply` in early Phase 3: **always** gate.

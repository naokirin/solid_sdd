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
| `formal` | Always gate in early Phase 3 rollout when `status` would be `apply` (see docs/phase3.md) |

## Plan fields

```json
"human_gate": {
  "required": true,
  "reason": "breaking_change on Operation enum removal"
}
```

Targets may repeat a narrower `human_gate` for location-specific approval.

## Orchestrator behavior (`solidsdd-loop`)

1. After `solidsdd-judge`, if any `human_gate.required` is true → **stop before apply**.
2. Final summary must list gate reasons and waiting locations.
3. Do not thin the plan to avoid the gate.
4. Resume only after explicit human approval in the conversation (or updated plan from a re-run of `solidsdd-judge` under new instructions).

## Defaults

- Evaluation samples (e.g. arithmetic-api additive changes): gate only when modifiers fire.
- Production defaults may set stricter always-gate rules via project rule overrides.

# Phase 2 — Judgment, gates, and adapters

Phase 2 strengthens **when** to apply contracts and **how** the loop recovers—without yet requiring formal specification tooling (Phase 3).

## Delivered in this phase slice

| Area | What landed |
|------|-------------|
| Judgment axes | Breaking / authz / money / churn / confidence modifiers ([reference-src/judgment-axes.md](../reference-src/judgment-axes.md)) |
| ApplicationPlan | Optional `signals`, `breaking`, `confidence`, `human_gate` |
| Human gates | Policy + loop stop-before-apply ([reference-src/human-gates.md](../reference-src/human-gates.md)) |
| Verify → loop | `loop_action`, `failure_class`, retry mapping ([reference-src/loop-retry.md](../reference-src/loop-retry.md)) |
| GraphQL adapter | Skeleton conventions ([../adapters/graphql/README.md](../adapters/graphql/README.md)) |

## Not in this slice

- Full GraphQL or Rails evaluation samples
- Language-native DbC adapters beyond OCL→tests
- Automated confidence scoring models
- Formal `apply` path (Phase 3)

## How skills use it

1. `solidsdd-judge` fills Phase 2 optional fields using judgment axes + human-gates.
2. `solidsdd-loop` stops before apply when `human_gate.required`.
3. `solidsdd-verify` sets `loop_action` / `failure_class` on failure.
4. `solidsdd-loop` retries per [loop-retry.md](../reference-src/loop-retry.md) (max 3) or escalates to human gate.

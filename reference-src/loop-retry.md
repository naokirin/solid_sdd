# Loop retry and verification (Phase 2)

## VerificationReport expectations

`solidsdd-verify` must emit JSON matching `verification-report.schema.json`.

On **fail**:

- Populate `suggested_next_skills` with concrete skill ids (`solidsdd-implement`, `solidsdd-apply-api`, …).
- Set `loop_action`:
  - `retry` — safe to re-run suggested skills automatically
  - `human_gate` — stop; needs person (repeated failures, ambiguous contract vs impl, breaking fix)
  - `stop` — unrecoverable in-loop (missing toolchain, contradictory specs after retries)
- Optionally set `failure_class` on the report or failed checks:
  - `implementation_bug` → prefer `solidsdd-implement`
  - `contract_gap` → prefer `solidsdd-apply-api` / `solidsdd-apply-dbc` / `solidsdd-derive-tests`
  - `tooling` → `stop` or `human_gate`
  - `unknown` → one retry then `human_gate` if still failing

## Orchestrator retry policy (`solidsdd-loop`)

1. Default **max_auto_retries = 3** (count verify failures that trigger a retry).
2. On `loop_action: retry`, launch suggested skills as **new Task subagents**, then verify again.
3. On `loop_action: human_gate` or `stop`, end the loop; print report + reasons.
4. If the same skill is suggested for consecutive retries without progress, escalate to `human_gate`.
5. Never edit contracts in the parent to force a green verify.

## Mapping cheat sheet

| Observe | Suggested skill | loop_action |
|---------|-----------------|-------------|
| Contract test fails; OCL/OpenAPI look right | `solidsdd-implement` | `retry` |
| Tests assert behavior absent from OCL | `solidsdd-apply-dbc` then `solidsdd-derive-tests` | `retry` |
| OpenAPI drift / invalid doc | `solidsdd-apply-api` | `retry` |
| OCL changed but tests stale | `solidsdd-derive-tests` | `retry` |
| Third consecutive same failure | — | `human_gate` |

# Loop retry, verification, and critique (Phase 2+)

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

## CritiqueReport expectations

`solidsdd-critique` must emit JSON matching `critique-report.schema.json`.

On **fail** (`blocker` / `major` findings):

- Populate `suggested_next_skills` with the **source** skills (usually judge / apply-* / derive-tests—not implement to hide thin contracts).
- Set `loop_action` the same way as verify (`retry` / `human_gate` / `stop`).
- Prefer categories `thin_contract`, `missing_precondition`, `weak_test`, `density_bias` when adequacy is the issue.

On **pass** with only `minor` findings: continue the loop; minors may be listed in the final summary.

## Orchestrator retry policy (`solidsdd-loop`)

1. Default **max_auto_retries = 3** — count **each** verify-fail retry **and** each critique-fail retry (shared budget). Isolation-violation re-runs also consume this budget.
2. On `loop_action: retry` (from verify **or** critique), launch suggested skills as **new Task subagents**, then re-run the relevant critique and/or verify.
3. On `loop_action: human_gate` or `stop`, end the loop; print report + reasons.
4. If the same skill is suggested for consecutive retries without progress, escalate to `human_gate`.
5. Never edit contracts in the parent to force a green verify or critique.
6. After a producer step, **do not skip** the matching `solidsdd-critique` subject (see [adversarial-critique.md](adversarial-critique.md)).

## Mapping cheat sheet

| Observe | Suggested skill | loop_action |
|---------|-----------------|-------------|
| Contract test fails; OCL/API look right | `solidsdd-implement` | `retry` |
| `pre` fails with wrong error type (e.g. `ZeroDivisionError` instead of domain `PreconditionError`) | `solidsdd-implement` | `retry` |
| Tests assert behavior absent from OCL | `solidsdd-apply-dbc` then `solidsdd-derive-tests` | `retry` |
| OpenAPI / GraphQL drift or invalid doc | `solidsdd-apply-api` | `retry` |
| OCL changed but tests stale | `solidsdd-derive-tests` | `retry` |
| Critique: plan too thin / density bias | `solidsdd-judge` | `retry` |
| Critique: vacuous OCL / missing domain errors | `solidsdd-apply-dbc` (± `derive-tests`) | `retry` |
| Critique: happy-path-only API | `solidsdd-apply-api` | `retry` |
| Critique: weak derived tests | `solidsdd-derive-tests` or `apply-dbc` | `retry` |
| Critique: isolation_violation | re-run that skill via Task | `retry` |
| Formal TLC missing jar/JDK | — | `stop` or `human_gate` (`tooling`) |
| Formal invariant violated | `solidsdd-apply-formal` (or implement if model is SoT for runtime) | `retry` / `human_gate` |
| Third consecutive same failure / retry budget exhausted | — | `human_gate` |

On every **fail**, `solidsdd-verify` / `solidsdd-verify-formal` / `solidsdd-critique` **must** set `loop_action` and preferably actionable `suggested_next_skills`.

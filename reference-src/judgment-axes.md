# Judgment axes (Phase 2)

Judge from risk and boundary axes, not from how hard implementation would be.
Never silently drop formal needs—use `defer` with rationale.
Cite the **signal id** (left column) in each target's `rationale` and optional `signals` array.

## Primary kind selection

| Signal id | Prefer |
|-----------|--------|
| `http_boundary` | `api` + adapter (`openapi` / `graphql`), status `apply` |
| `domain_contract` | `dbc` + adapter (`ocl` / future language-contract), status `apply` |
| `concurrency_safety` | `formal` — `apply` only when Phase 3 conditions hold (see below); otherwise `defer` with rationale |
| `exploratory_ux` | `natural_only` or density `thin` |

## Formal `apply` vs `defer` (Phase 3)

Prefer `status: apply` for `kind: formal` only when **all** hold:

1. `concurrency_safety` (or product-marked safety-critical scope) is present
2. Project has a formal adapter + documented checker (`adapter_hint`: `tla` / `alloy` / …)
3. Scope is a single protocol or shared resource
4. `human_gate.required: true` (early Phase 3 policy)

Otherwise `status: defer` with `adapter_hint: defer-formal`. Never omit formal need silently. Details: repo `docs/phase3.md`.

## Density and risk modifiers

| Signal id | Effect |
|-----------|--------|
| `breaking_change` | Prefer density `strict` for `api`; set `breaking: true`; usually `human_gate.required: true` |
| `authz_boundary` | Auth/session/permission surfaces → at least density `standard`, often `strict` for `api` + `dbc` |
| `money_boundary` | Payments, balances, ledger, billing → density `strict`; strong `dbc`; consider `formal` `defer` with explicit rationale |
| `high_churn` | Rapidly changing exploratory APIs → density `thin` or `standard`, avoid over-formalizing |
| `stable_core` | Mature, rarely changing core → density `standard` or `strict` |
| `low_confidence` | Ambiguous requirements or weak context → set `confidence: low` and `human_gate.required: true` |

## Combining rules

1. Choose `kind` / `adapter_hint` from primary signals first.
2. Raise density to the **maximum** implied by any matching modifier (thin < standard < strict).
3. If any of `breaking_change`, `money_boundary`, or `low_confidence` applies, set plan or target `human_gate`.
4. Do not lower density because implementation would be hard.

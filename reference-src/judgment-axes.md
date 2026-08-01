# Judgment axes (Phase 2)

Judge from risk and boundary axes, not from how hard implementation would be.
Never silently drop formal needs—use `defer` with rationale.
Cite the **signal id** (left column) in each target's `rationale` and optional `signals` array.

## Primary kind selection

| Signal id | Prefer |
|-----------|--------|
| `http_boundary` | `api` + adapter (`openapi` / `graphql`), status `apply` |
| `domain_contract` | `dbc` + adapter (`ocl` / future language-contract), status `apply` |
| `concurrency_safety` | `formal`, status `defer` until Phase 3 tooling exists (or `apply` when formal adapters land) |
| `exploratory_ux` | `natural_only` or density `thin` |

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

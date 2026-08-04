# Knowledge consult — add-concurrent-last-unit-safety

mode: consult  
change_id: add-concurrent-last-unit-safety  
working_language: en (project rule)  
kg_build: ok (`.solidsdd-cache/kg.db`; nodes=41, edges=2; CLI `scripts/solidsdd-kg.sh`)

## Applicable policies / concepts / decisions

### Policies

| id | title | why it applies |
|----|-------|----------------|
| `POL-OPAQUE-PRINCIPAL-AUTHZ` | Opaque principal authorize/deny only (not full IAM) | Concurrent authorized reserves still use opaque-principal allow/deny for reserve (and related mutation paths). Full IAM remains out of scope. Unauthorized callers must fail with named `UnauthorizedError` (or equivalent) and must not mutate stock or holds. |

Scope query `product.inventory_reservation` returns this policy only. Context pack links it to prior lookup requirements (`add-lookup-available-stock/R1`, `R3`); no Brief `R*` exist yet for this change, so `impact` on `add-concurrent-last-unit-safety/R*` was not run.

### Concepts / decisions / patterns / lessons

**None** under `knowledge/`.

### Framing notes (not knowledge nodes — do not cite as SoT)

- Sequential insufficient-stock / soft-hold / availableStock behavior lives in prior ChangeBrief / OpenAPI / OCL (e.g. `initial-reservation` R1–R2; named `InsufficientStockError`), not in `knowledge/`.
- Concurrent last-unit safety, non-negative stock under interleaving, and bounded TLA+/TLC are **this change’s** requirement scope; no harvested invariant or formal pattern yet.
- Prior briefs deferred formal concurrency (`initial-reservation` X8 / similar); this change intentionally lifts that into Phase 3 formal with expected `human_gate`.

## Suggested citations (Brief assumptions / constraints)

- Cite **`POL-OPAQUE-PRINCIPAL-AUTHZ`** in Brief `assumptions` and/or `constraints` for AuthZ on concurrent reserve paths (opaque-principal only; unauthorized → named error, no mutation).
- Do **not** invent knowledge ids for non-negative stock / last-unit exclusivity / race-loser `InsufficientStockError` — keep those in Brief `in_scope` / Gherkin / contracts until a later harvest gate promotes durable nodes.

## Gaps

- No durable policy/invariant yet for concurrent non-negative available stock or last-unit exclusivity (expected harvest candidates after this change, not consult hits).
- No concepts/decisions for formal/TLA+ concurrency patterns under `knowledge/`.
- This change has no Brief `R*` yet → no requirement→knowledge `impact` for the new change.
- Tooling: `.solidsdd/kg/` present; `solidsdd-kg` CLI available via repo-root `scripts/solidsdd-kg.sh --root examples/inventory-reservation` — **no CLI gap**.

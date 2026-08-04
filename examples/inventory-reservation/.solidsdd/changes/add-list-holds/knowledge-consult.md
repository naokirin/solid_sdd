# Knowledge consult — add-list-holds

mode: consult  
change_id: add-list-holds  
working_language: en (project rule)  
kg_build: ok (`.solidsdd-cache/kg.db`; nodes=55, edges=2; CLI `scripts/solidsdd-kg.sh`)  
kg_check: ok (errors=0; warns=49 — known REQ_MUST_HAVE_IMPL / VERIFY / DUPLICATE_NODE_CANDIDATE on prior changes)

## Applicable policies / concepts / decisions

### Policies

| id | title | maturity | facets | why it applies |
|----|-------|----------|--------|----------------|
| `POL-OPAQUE-PRINCIPAL-AUTHZ` | Opaque principal authorize/deny only (not full IAM) | **canonical** | `decider` | User intent keeps opaque-principal AuthZ Means for listing soft-holds/reservations. Scope query `product.inventory_reservation` returns this policy only. Context pack links it to prior lookup requirements (`add-lookup-available-stock/R1`, `R3`). Policy body currently names reserve / release / expire / **lookup**; list is not yet enumerated in the policy text—Grill/intake must decide whether list is covered by the same Means without inventing visibility rules here. Unauthorized callers must fail with named `UnauthorizedError` (or equivalent) and must not mutate stock or holds. |

### Concepts / decisions / patterns / lessons / invariants

**None** under `knowledge/`.

### Framing notes (not knowledge nodes — do not cite as SoT)

- Soft-hold / reservation create, single-id lookup, availableStock, and concurrent last-unit behavior live in prior ChangeBrief / OpenAPI / OCL / Features—not in `knowledge/`.
- Who can see which holds, filters, paging, and response shape are **undecided** (Grill next). This consult does **not** invent answers; leave them for intake / Brief / Gherkin.
- Do not thin list UX or API shape into a living PRD under `knowledge/`.

## Suggested citations (Brief assumptions / constraints)

- Cite **`POL-OPAQUE-PRINCIPAL-AUTHZ`** (`maturity: canonical`, facet `decider`) in Brief `assumptions` and/or `constraints` for AuthZ on list-holds: opaque-principal allow/deny only; full IAM remains out of scope; unauthorized → named error, no mutation.
- Do **not** invent knowledge ids for list visibility, filters, paging, or response DTO—keep those in Grill → Change Context / Brief `in_scope` / Gherkin / contracts until a later harvest gate (if durable).

## Gaps

- No durable policy/concept for **list** visibility (“who can see what”), cross-principal vs self-only scoping, filters, paging, or response shape.
- Policy text lists operations through **lookup** but does not yet name **list**; whether to extend the policy wording is a post-Grill / harvest concern—not a consult invention.
- No Brief `R*` yet for `add-list-holds` → `impact` on `add-list-holds/R*` was not run.
- Tooling: `.solidsdd/kg/` present; `solidsdd-kg` CLI available via repo-root `scripts/solidsdd-kg.sh --root .` — **no CLI gap**.

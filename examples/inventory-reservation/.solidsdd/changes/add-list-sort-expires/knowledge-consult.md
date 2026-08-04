# Knowledge consult — add-list-sort-expires

mode: consult  
change_id: add-list-sort-expires  
working_language: en (project rule)  
placement: **draft** — change dir `.solidsdd/changes/add-list-sort-expires/` does not exist yet; intake should copy this file to `.solidsdd/changes/add-list-sort-expires/knowledge-consult.md`  
source_draft: `/tmp/add-list-sort-expires-knowledge-consult.md`  
kg_build: ok (`.solidsdd-cache/kg.db`; nodes=69, edges=5; CLI repo-root `scripts/solidsdd-kg.sh --root .`)  
kg_check: ok (errors=0; warns=59 — known REQ_MUST_HAVE_VERIFY / similar on prior changes)  
active_change_note: `.solidsdd/active-change.json` still points at `add-list-holds` (not this change)

## Ask (relevance framing)

Authorized soft-hold **collection list** shall return items sorted by **`expiresAt` ascending**. **AuthZ / visibility / full-dump Means are unchanged.**

## Applicable policies / concepts / decisions

### Policies

| id | title | maturity | facets | why it applies |
|----|-------|----------|--------|----------------|
| `POL-OPAQUE-PRINCIPAL-AUTHZ` | Opaque principal authorize/deny only (not full IAM) | **canonical** | `decider` | Ask keeps AuthZ Means unchanged: list remains opaque-principal allow/deny only; unauthorized → named `UnauthorizedError` (or equivalent), no mutation of stock/holds. Scope query `product.inventory_reservation` returns this policy. Linked from prior list AuthZ (`add-list-holds/R3`) and lookup AuthZ. |
| `POL-SOFT-HOLD-SHARED-READ-VISIBILITY` | Soft-hold reads share one visibility universe (list = get-by-id) | **canonical** | `decider`, `invariant` | Ask keeps visibility Means unchanged: authorized list still shares one visibility universe with get-by-id (all currently visible soft-holds; no principal-scoped / self-only / role / tenant views). Scope query returns this policy. Linked from `add-list-holds/R1`. |

### Decisions

| id | title | maturity | facets | why it applies |
|----|-------|----------|--------|----------------|
| `DEC-SOFT-HOLD-LIST-UNFILTERED-FULL-DUMP` | Soft-hold list is an unfiltered full dump of LookupResponse-equivalent items | **canonical** | `decider`, `acceptance-property` | Ask keeps full-dump Means unchanged: still one unfiltered full dump (no sku/status/time filters, no paging/cursor/limit-offset), LookupResponse-equivalent items, empty collection = success. **Sort order is orthogonal** to this decision (filters/paging/DTO shape stay deferred). Linked from `add-list-holds/R2`. Scope `scope` CLI returns policies only—decision found via `knowledge/decisions/` + `context`. |

### Concepts / patterns / lessons / invariants

**None** under `knowledge/` beyond the policies/decision above. No existing knowledge node defines collection **sort order**.

### Framing notes (not knowledge nodes — do not cite as SoT)

- List AuthZ, shared visibility, and unfiltered full-dump item shape live in the cited knowledge + prior `add-list-holds` Brief/contracts—not to be reopened by this change unless intake explicitly elevates them.
- **`expiresAt` ascending** sort is **new change intent**; there is no durable POL/DEC for list ordering yet. Keep sort acceptance in Grill → Change Context / Brief `in_scope` / Gherkin / contracts until a later harvest gate (if durable).
- Do not invent filter/paging/ownership rules under the guise of “sorting.”

## Suggested citations (Brief assumptions / constraints)

- Cite **`POL-OPAQUE-PRINCIPAL-AUTHZ`** (`canonical`, `decider`) — AuthZ Means **unchanged**.
- Cite **`POL-SOFT-HOLD-SHARED-READ-VISIBILITY`** (`canonical`, `decider`+`invariant`) — visibility Means **unchanged**.
- Cite **`DEC-SOFT-HOLD-LIST-UNFILTERED-FULL-DUMP`** (`canonical`, `decider`+`acceptance-property`) — full-dump / item-shape Means **unchanged**; sort does not imply filters or paging.
- Put **`expiresAt` ascending** sort in Brief `in_scope` / Gherkin acceptance (and optionally `assumptions` as hypothesized until confirmed)—**do not** invent a knowledge id for sort in this consult.

## Gaps

- No durable policy/decision for soft-hold collection **sort key / direction** (e.g. `expiresAt` ASC, ties, stability).
- Change directory `add-list-sort-expires` not created → this file is a **pre-intake draft**; no Brief `R*` yet → `impact` on `add-list-sort-expires/R*` was not run.
- `solidsdd-kg scope` lists policies in scope only; decision applicability confirmed via filesystem + `context DEC-SOFT-HOLD-LIST-UNFILTERED-FULL-DUMP`.
- Tooling: `.solidsdd/kg/` present; CLI available via repo-root `scripts/solidsdd-kg.sh` — **no CLI gap**.

---
id: POL-SOFT-HOLD-SHARED-READ-VISIBILITY
type: policy
title: Soft-hold reads share one visibility universe (list = get-by-id)
status: active
maturity: canonical
scope: product.inventory_reservation
aliases: []
facets:
  - decider
  - invariant
verified_at: "2026-08-04"
---

Authorized soft-hold reads—get-by-id and collection list—share one visibility universe: any authorized opaque principal sees all currently visible soft-holds. Do not introduce principal-scoped ownership, self-only listing, roles, tenants, or cross-principal admin views unless an explicit later change elevates them.

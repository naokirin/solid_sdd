---
id: CON-HOLD-VISIBILITY
type: concept
title: visible soft-hold
status: active
maturity: canonical
scope: product.inventory_reservation
aliases:
  - visible hold
  - 可視ホールド
facets:
  - vocabulary
verified_at: "2026-08-10"
---

A soft-hold is **visible** when an authorized opaque principal may read it via get-by-id or collection list. **Visible** is not the same as **exists**: missing id and not-visible id share a named failure channel on lookup (`PreconditionError`) but differ in caller intent. List and get-by-id share one visibility universe ([POL-SOFT-HOLD-SHARED-READ-VISIBILITY](../policies/POL-SOFT-HOLD-SHARED-READ-VISIBILITY.md)). Contract: OCL `HoldExists` / list full-dump posts; OpenAPI lookup/list operations.

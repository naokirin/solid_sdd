---
id: CON-AVAILABLE-STOCK
type: concept
title: availableStock
status: active
maturity: canonical
scope: product.inventory_reservation
aliases:
  - available stock
  - 引当可能数
facets:
  - vocabulary
verified_at: "2026-08-10"
---

**availableStock** is the quantity of a SKU still allocatable to new soft-holds after existing holds are accounted for—not physical on-hand inventory across warehouses. Reserve decreases it; release and expiry restore it. Lookup/list responses expose the **current** value for the SKU (not a reserve-time snapshot). Contract: OCL `Reservation::availableStock(sku)`; OpenAPI `LookupResponse.availableStock`.

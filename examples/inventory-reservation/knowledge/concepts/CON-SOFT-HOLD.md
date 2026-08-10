---
id: CON-SOFT-HOLD
type: concept
title: soft-hold
status: active
maturity: canonical
scope: product.inventory_reservation
aliases:
  - soft hold
  - ソフトホールド
facets:
  - vocabulary
verified_at: "2026-08-10"
---

A **soft-hold** is a temporary inventory reservation: quantity for a SKU is held for a TTL, reducing **available stock**, without confirming payment or shipment. It is not a finalized order or permanent allocation. Created by authorized reserve; removed by authorized release or TTL expiry. Contract types: OCL `Hold`; OpenAPI reserve/list/lookup surfaces.

---
id: DEC-SOFT-HOLD-LIST-UNFILTERED-FULL-DUMP
type: decision
title: Soft-hold list is an unfiltered full dump of LookupResponse-equivalent items
status: active
maturity: canonical
scope: product.inventory_reservation
aliases: []
facets:
  - decider
  - acceptance-property
verified_at: "2026-08-04"
---

Until an explicit change elevates filter dimensions or paging, soft-hold collection list returns one unfiltered full dump (no sku/status/time filters, no paging/cursor/limit-offset) whose items are LookupResponse-equivalent (holdId, sku, quantity, expiresAt, availableStock). Empty collection when none are visible is success. List-by-SKU aggregates and thinner DTOs without availableStock remain deferred.

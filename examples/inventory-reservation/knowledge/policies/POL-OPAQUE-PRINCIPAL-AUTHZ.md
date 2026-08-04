---
id: POL-OPAQUE-PRINCIPAL-AUTHZ
type: policy
title: Opaque principal authorize/deny only (not full IAM)
status: active
maturity: canonical
scope: product.inventory_reservation
aliases: []
facets:
  - decider
verified_at: "2026-08-03"
---

AuthZ for reserve, release, expire, and lookup is opaque-principal allow/deny only. Full IAM (SSO, OAuth UI, role admin) is out of scope for this sample product. Unauthorized callers fail with a named UnauthorizedError (or equivalent named domain error) and must not mutate stock or holds.

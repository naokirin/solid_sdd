---
id: CON-OPAQUE-PRINCIPAL
type: concept
title: opaque principal
status: active
maturity: canonical
scope: product.inventory_reservation
aliases:
  - opaque-principal
  - principal
facets:
  - vocabulary
verified_at: "2026-08-10"
---

An **opaque principal** is an authorized-or-not caller identity passed into mutation and read operations (e.g. OpenAPI `OpaquePrincipal` header). The sample does not model roles, tenants, or ownership—only allow/deny ([POL-OPAQUE-PRINCIPAL-AUTHZ](../policies/POL-OPAQUE-PRINCIPAL-AUTHZ.md)). Contract: OCL `principal.isAuthorized()` / `PrincipalAuthorized` pres; OpenAPI `#/components/parameters/OpaquePrincipal`.

---
id: CON-NAMED-DOMAIN-ERROR
type: concept
title: named domain error
status: active
maturity: canonical
scope: product.inventory_reservation
aliases:
  - named error channel
  - 名前付きドメインエラー
facets:
  - vocabulary
verified_at: "2026-08-10"
---

A **named domain error** is a first-class failure type shared by OpenAPI, OCL, and derived contract tests—not a language builtin or ad-hoc HTTP status alone. Examples in this product: `UnauthorizedError`, `InsufficientStockError`, `PreconditionError`. Sequential and concurrent insufficient stock share `InsufficientStockError`; missing and not-visible lookup share `PreconditionError`. Contract: OpenAPI error schemas/responses; OCL `post …Error` channels in `contracts/Reservation.ocl`.

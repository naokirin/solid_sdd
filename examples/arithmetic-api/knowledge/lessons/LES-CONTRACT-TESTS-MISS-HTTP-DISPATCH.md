---
id: LES-CONTRACT-TESTS-MISS-HTTP-DISPATCH
type: lesson
title: Green contract tests do not prove a new operation is reachable through the HTTP dispatch/whitelist layer
status: active
maturity: canonical
scope: product.arithmetic_api
aliases: []
facets:
  - acceptance-property
verified_at: "2026-08-13"
---

Contract-level tests against module logic (e.g. Calculator.pow, calculate()) exercise business logic directly and can pass fully even when the HTTP layer (src/server.ts) never routes the new operation value to that logic -- e.g. because a hand-maintained request-validation whitelist (an OPERATIONS Set/array) was not updated to include it. Passing unit/contract tests are not sufficient evidence that a new operation is actually callable end-to-end over the real transport. Verify with an HTTP-layer test that sends a real request for the new operation and asserts success, and confirm the test's sensitivity with a mutation spot-check: temporarily remove the new value from the whitelist, rerun, confirm the HTTP test (and only that test) now fails, then restore.

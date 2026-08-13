---
id: PAT-OPERATION-PRECONDITION-SCOPE
type: pattern
title: Decide each arithmetic operation's precondition scope from its own domain, not by analogy to sibling operations
status: active
maturity: canonical
scope: product.arithmetic_api
aliases: []
facets:
  - decider
verified_at: "2026-08-13"
---

When adding a new operation to POST /calculate (or any future arithmetic op in this API), decide whether it needs a PreconditionError-guarded domain restriction (like div/mod's b === 0 zero-divisor check) by examining that operation's own mathematically undefined/invalid input region -- never by defaulting to, or mechanically copying, an existing sibling operation's precondition set. An operation with no genuinely undefined native-semantics input region (e.g. pow under IEEE-754 `**`) gets no precondition; one with a real undefined region (e.g. div/mod's zero divisor) does. Absence of a precondition must be a deliberate, explicit statement in Change Context/Brief, not a silent omission.

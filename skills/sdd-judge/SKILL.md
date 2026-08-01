---
name: sdd-judge
description: >-
  Decide where to apply OpenAPI, OCL DbC, or defer formal specs for a change.
  Use when planning SDD application or before apply skills.
---

# sdd.judge

## Execution

**orchestrator** — keep planning on the parent so loop control stays coherent. See [docs/execution-model.md](../../docs/execution-model.md).

## Purpose

Emit an `ApplicationPlan` (schema: `schemas/application-plan.schema.json`).

## Judgment axes (MVP)

| Signal | Prefer |
|--------|--------|
| HTTP boundary / compatibility | `api` + `openapi`, status `apply` |
| Domain pre/post/invariants | `dbc` + `ocl`, status `apply` |
| Concurrency / deep safety proofs | `formal`, status `defer` (MVP) |
| Exploratory / unstable UX-only | `natural_only` or thin density |

## Steps

1. Read change intent and current context (`sdd-context` output if available).
2. List targets with kind, location, density, rationale, adapter_hint, status.
3. Never silently drop formal needs—use `defer` with rationale.
4. Validate the plan against the ApplicationPlan schema mentally (required fields).

## Output

JSON conforming to `schemas/application-plan.schema.json`, plus a one-paragraph summary.

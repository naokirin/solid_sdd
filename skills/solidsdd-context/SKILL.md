---
name: solidsdd-context
description: >-
  Gather repository stack, existing OpenAPI/GraphQL/OCL/formal contracts, and
  test layout for solid_sdd. Use before judge/apply/loop/run or when asked for
  SDD context.
license: MIT
---

# solidsdd.context

## Execution

**orchestrator** — run in the parent (`solidsdd.run`, `solidsdd.loop`, or the user-invoked agent). When `solidsdd-run` or `solidsdd-loop` is installed, follow that skill’s execution-model reference.

## Purpose

Produce a concise context summary so later skills do not rediscover the stack.

## References

- [contract-layout.md](references/contract-layout.md)
- [change-lifecycle.md](references/change-lifecycle.md)

## Steps

1. Detect language/runtime (TypeScript/Node, Ruby, …).
2. Locate active change (if any):
   - `.solidsdd/active-change.json` → `.solidsdd/changes/<change_id>/change-brief.json` (+ `work-plan.json` / `status.json` when present)
   - Legacy flat `.solidsdd/change-brief.json` only → note that next brief/run must migrate ([change-lifecycle.md](references/change-lifecycle.md))
3. Locate API contracts:
   - OpenAPI: `openapi/openapi.yaml` (or project-rule overrides)
   - GraphQL: `graphql/schema.graphql` if present → prefer `adapter_hint: graphql` later
4. Locate requirements: `requirements/**/*.feature` (accumulate across changes)
5. Locate OCL: `contracts/**/*.ocl`
6. Locate derived tests:
   - Vitest: `tests/contracts/**`
   - RSpec: `spec/contracts/**`
7. Locate formal artifacts: `formal/**/*.tla` (+ `.cfg`); note whether TLC tooling is documented/available
8. Note package/verify commands (`npm test`, `bundle exec rspec`, `./verify.sh`, `tools/tla/tlc.sh`, …)
9. Locate durable knowledge (if any):
   - `knowledge/**` (concepts / policies / decisions / …)
   - `.solidsdd/kg/` (`schema.yaml` / `config.yaml` / `links.yaml`)
   - Per-change snapshots: `knowledge-consult.md` / `knowledge-harvest.json` under the active change when present
   - Do **not** deeply extract policy bodies here—that is `solidsdd-knowledge` consult
10. Flag gaps (missing API SoT, OCL, tests, or formal tooling when `formal/` exists; missing `.solidsdd/kg/` when `knowledge/` exists)

## Output

Write a short markdown summary with:

- stack
- active `change_id` / Brief path (or legacy / none)
- contract artifact paths (api / dbc / formal), Feature paths, and test target (vitest / rspec)
- knowledge layout (`knowledge/` / `.solidsdd/kg/` present or absent)
- gaps
- suggested next skill (`solidsdd-knowledge` consult before intake when knowledge exists; else `solidsdd-judge`, `solidsdd-loop` for one slice, or `solidsdd-run` / `solidsdd-brief` for a new or multi-criterion change)

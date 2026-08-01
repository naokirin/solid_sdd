# Phase 3 — Formal specifications (design)

Phase 3 adds an **optional, narrow** path for machine-checkable formal specs (TLA+, Alloy, …) alongside existing API and OCL→tests routes. This document is the design slice: skills and judge rules are specified; full tooling and evaluation samples come later.

## Goals

1. Let `solidsdd-judge` set `kind=formal` with `status=apply` when conditions are met (not only `defer`).
2. Isolate formal work in dedicated skills so API/DbC loops are not mixed with model checking.
3. Keep human gates strong: early rollouts always pause before `apply.formal`.
4. Document role split so teams do not replace OpenAPI/OCL with formal specs by default.

## Non-goals (this phase)

- Teaching formal methods as a product goal
- Requiring a formal toolchain on every project
- Replacing OCL for ordinary module pre/post
- Language-native DbC (still deferred; separate opt-in design)

## Role split

| Concern | Prefer | Formal? |
|---------|--------|---------|
| HTTP/GraphQL I/O, compatibility | API adapter | No |
| Module pre/post/invariants | OCL → contract tests | Only if state space / concurrency exceeds DbC |
| Concurrent / distributed protocols, crash/recovery, safety/liveness | Formal | Yes when apply conditions hold |
| Exploratory UX | Natural / thin contracts | No |

Rule of thumb: **formal specs check properties that contract tests cannot cheaply falsify** (interleavings, global invariants across processes). If a Vitest/RSpec example is enough, stay on DbC.

## When judge may `apply` formal

All of the following:

1. Signal `concurrency_safety` (or equivalent: distributed consensus, multi-writer shared state, failover) is present **and** density would be `strict` under Phase 2 modifiers, **or** product policy marks the boundary as safety-critical.
2. A formal adapter is available for the project (`adapter_hint` e.g. `tla`, `alloy`) and toolchain is documented in project rules.
3. Scope is bounded (one protocol / one shared resource)—not “formalize the whole app.”
4. `human_gate.required: true` (mandatory in Phase 3 early rollout).

Otherwise keep `status: defer` with rationale (as in MVP/Phase 2). Never silently drop formal need.

## Proposed skills

| Skill | Role | Execution |
|-------|------|-----------|
| `solidsdd-apply-formal` | Write/update formal specs (e.g. `formal/**/*.tla`) | Subagent required from loop |
| `solidsdd-verify-formal` | Run model checker / analyzer; emit checks into VerificationReport (`kind: other` or future `formal`) | Subagent required |
| Existing `solidsdd-judge` | May emit `formal` + `apply` under rules above | Subagent required |
| Existing `solidsdd-loop` | After human gate approval: apply-formal → verify-formal; do not block API/DbC path on formal `defer` | Orchestrator |

API/DbC skills remain unchanged. Loop sequence (sketch):

```text
context → judge
  → [human_gate if any]
  → apply-api / apply-dbc → derive-tests → implement → verify
  → [if formal apply approved] apply-formal → verify-formal
```

Formal failures use `loop_action` / `failure_class` like Phase 2 (`tooling` → stop/gate; spec bug → retry apply-formal; impl mismatch may still be implement if the model is the SoT for that property).

## Adapter sketch

Default checker: **TLA+ / TLC** ([../tools/tla/README.md](../tools/tla/README.md)).

| Artifact | Path |
|----------|------|
| TLA+ modules | `formal/**/*.tla` |
| TLC configs | `formal/**/*.cfg` |
| Alloy models | `formal/**/*.als` (optional later) |

See [../adapters/formal/README.md](../adapters/formal/README.md). Evaluation sample: [../examples/memory-formal](../examples/memory-formal).

## ApplicationPlan fields (unchanged schema)

Use existing `kind: formal`, `adapter_hint` (`tla` \| `alloy` \| `defer-formal`), `status`, `human_gate`, `signals: ["concurrency_safety", …]`.

## Success criteria for Phase 3 implementation

1. [x] Judge rules allow `formal` `apply` under documented conditions
2. [x] One minimal formal sample with verify-formal / TLC green ([phase3-evaluation.md](phase3-evaluation.md))
3. [ ] Loop stops on `human_gate` before writing formal artifacts (dry-run in a project)
4. [x] OpenAPI/OCL samples still pass without requiring TLC on every clone (jar is fetched, gitignored)

## Status

**Design + first checker/sample complete.** Default checker: TLC. Sample: [../examples/memory-formal](../examples/memory-formal). Notes: [phase3-evaluation.md](phase3-evaluation.md).

Remaining: richer samples, optional Apalache/Alloy, loop gate dry-run in a consuming project.

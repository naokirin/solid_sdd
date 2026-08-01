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

Default layout (project-overridable):

| Artifact | Path |
|----------|------|
| TLA+ (example) | `formal/**/*.tla` (+ `.cfg` if needed) |
| Alloy (example) | `formal/**/*.als` |

See [../adapters/formal/README.md](../adapters/formal/README.md). First concrete checker integration is intentionally undecided (tlc / apalache / alloy analyzer)—record choice in project rule when enabling `apply`.

## ApplicationPlan fields (unchanged schema)

Use existing `kind: formal`, `adapter_hint` (`tla` \| `alloy` \| `defer-formal`), `status`, `human_gate`, `signals: ["concurrency_safety", …]`.

## Success criteria for Phase 3 implementation (later)

1. Judge unit scenarios: concurrency → `apply` only when adapter+gate; else `defer`.
2. One minimal formal sample (e.g. single-writer memory or lock protocol) with verify-formal green.
3. Loop stops on `human_gate` before writing formal artifacts.
4. OpenAPI/OCL samples still pass without a formal toolchain installed.

## Status

**Design complete for this slice.** Skill stubs: `skills/solidsdd-apply-formal`, `skills/solidsdd-verify-formal`. Evaluation sample and checker wiring: not started.

---
name: solidsdd-architecture
description: >-
  Decide whether a change affects existing system structure (modules,
  responsibilities, dependencies, dependency direction, public boundaries,
  ownership, structural constraints). When called from solidsdd-run, must run
  as an explicit Task subagent. Emits ArchitecturePlan (status: changed) or a
  status: unchanged shortcut when the change does not affect structure. Does
  not choose specification techniques (see solidsdd-judge) or edit contracts
  / implementation.
license: MIT
---

# solidsdd.architecture

## Execution

**subagent required** when invoked from `solidsdd.run` (or any orchestrator
chaining multiple phases). Parent must use Task and must not re-judge or thin
the returned plan inline. Solo user invocation may run in the current agent.

## Purpose

Emit an `ArchitecturePlan`: either `status: unchanged` (this change does not
affect existing structure) or `status: changed` with the modules,
dependencies, and structural constraints this change introduces or modifies.

This skill judges **structure only** — which modules exist, what each owns,
how they depend on each other, and which dependencies are forbidden. It does
not decide where OpenAPI / OCL / formal specs apply (that is
`solidsdd-judge` / `ApplicationPlan`) and does not describe behavior (that is
Gherkin). See "Role separation" in
[architecture-axes.md](references/architecture-axes.md).

## References

- [architecture-plan.schema.json](references/architecture-plan.schema.json)
- [architecture-axes.md](references/architecture-axes.md) — **when architecture changes, field minimality, role separation (required)**
- [human-gates.md](references/human-gates.md)
- [change-brief.md](references/change-brief.md) — scope premise
- [change-context.md](references/change-context.md) — existing structure signals (stack, layout)
- [work-plan.schema.json](references/work-plan.schema.json) — read `items[].touches` as the primary structural-change signal
- [contract-layout.md](references/contract-layout.md) — default artifact path
- [working-language.md](references/working-language.md) — `summary`/`responsibility`/`reason` string language

## Constraints

- Produce the ArchitecturePlan only (no OpenAPI / OCL / formal / implementation edits, no ApplicationPlan)
- Do not require or name a specific architectural style (DDD, Clean Architecture, Hexagonal, Onion, MVC, CQRS, Event Sourcing, …) — `ArchitecturePlan` only records modules/dependencies/ownership/constraints, not a methodology
- Judge from the existing structure (Context) plus this change's WorkPlan `touches` / Brief scope — do not redesign structure the change does not touch
- Do not pad `status: changed` with unrelated existing modules just to look complete; do not force `status: unchanged` to avoid writing a plan when `touches` implies a new module/boundary/dependency-direction change
- Populate `owns` / `public` / `dependency.kind` only when confidently derivable from context — never guess to fill out the schema
- Set `human_gate` per [human-gates.md](references/human-gates.md) (large boundary change, external-boundary change, dependency-direction reversal, or deliberate change to an existing structural constraint) — do not gate ordinary additive module/dependency additions
- JSON keys English; human-readable `summary` / `responsibility` / `reason` strings in the **working language** ([working-language.md](references/working-language.md))

## Steps

1. Read change intent, active Change Context and ChangeBrief, and the WorkPlan (`items[].touches` across all items is the primary signal for structural change). Resolve working language from project rule or Context §6.
2. Apply the "When architecture changes" / "When architecture does not change" tables in [architecture-axes.md](references/architecture-axes.md).
3. If no trigger applies: emit `{"version": "1", "status": "unchanged", "change_id": ..., "summary": "..."}` and stop.
4. If a trigger applies: list `modules` (id, responsibility, optional `owns`/`public`), `dependencies` (from, to, optional reason/kind), and `constraints` (type `forbid_dependency` or `no_cycles`, with from/to/reason as applicable) — delta only, not a full re-documentation of unrelated existing structure.
5. Apply human-gate rules in [human-gates.md](references/human-gates.md).
6. Validate against [architecture-plan.schema.json](references/architecture-plan.schema.json).

## Output

JSON conforming to the ArchitecturePlan schema, plus a one-paragraph summary.
When invoked from `solidsdd-run`, **write** the plan to
`.solidsdd/changes/<change_id>/architecture-plan.json` (caller supplies the
change_id) and return those artifacts to the parent unchanged in meaning.

---
name: solidsdd-architecture
description: >-
  Decide whether a change affects existing system structure (modules,
  responsibilities, dependencies, dependency direction, public boundaries,
  ownership, structural constraints), and when it does, edit the
  Architecture Model (Structurizr DSL subset + invariants) and record why.
  When called from solidsdd-run, must run as an explicit Task subagent.
  Emits ArchitecturePlan (status: changed, generated from the Architecture
  Model) or a status: unchanged shortcut when the change does not affect
  structure. Does not choose specification techniques (see solidsdd-judge)
  or edit contracts / implementation.
license: MIT
---

# solidsdd.architecture

## Execution

**subagent required** when invoked from `solidsdd.run` (or any orchestrator
chaining multiple phases). Parent must use Task and must not re-judge or thin
the returned plan inline. Solo user invocation may run in the current agent.

## Purpose

Decide **structure only** — which modules exist, what each owns, how they
depend on each other, which dependencies are forbidden — and, when this
change affects structure, edit the Architecture Model:

- `.solidsdd/architecture/workspace.dsl` — Structurizr DSL subset, the
  Source of Truth for structure (persistent, whole-project; see
  [structurizr-dsl.md](references/structurizr-dsl.md))
- `.solidsdd/architecture/invariants.yaml` — forbidden-dependency /
  no-cycles constraints and prose Architecture Invariants (persistent,
  whole-project)
- `.solidsdd/changes/<change_id>/architecture-reasoning.md` — **why** this
  decomposition/boundary/ownership/direction was chosen (change-local; see
  [architecture-reasoning-template.md](references/architecture-reasoning-template.md))
- `.solidsdd/changes/<change_id>/physical-design.md` — **optional**, only at
  Architecture Depth Level 3 when the Logical → Physical realization itself
  is non-obvious (change-local; see
  [physical-design.md](references/physical-design.md))

`architecture-plan.json` is still produced — now as a deterministic
**projection** of the Architecture Model for this change_id
(`scripts/solidsdd-architecture/project.py`), kept for existing consumers
(`solidsdd-lint`, `solidsdd-critique`, `solidsdd-report`). Do not hand-author
`architecture-plan.json` — generate it.

This skill does not decide where OpenAPI / OCL / formal specs apply (that is
`solidsdd-judge` / `ApplicationPlan`) and does not describe behavior (that is
Gherkin). See "Role separation" in
[architecture-axes.md](references/architecture-axes.md).

## References

- [architecture-axes.md](references/architecture-axes.md) — **when architecture changes, Logical Decomposition axes, field minimality, role separation (required)**
- [architecture-depth.md](references/architecture-depth.md) — **how deep this change needs to go (required)**
- [structurizr-dsl.md](references/structurizr-dsl.md) — DSL grammar and concept mapping (required when depth ≥ Level 1)
- [architecture-reasoning-template.md](references/architecture-reasoning-template.md) — required when depth ≥ Level 1
- [physical-design.md](references/physical-design.md) — optional, Level 3 only, when the physical realization decision is non-obvious
- [architecture-traceability.md](references/architecture-traceability.md) — when an explicit Logical → Physical mapping is worth recording; do not embed filesystem metadata in `workspace.dsl`
- [architecture-plan.schema.json](references/architecture-plan.schema.json) — shape of the generated projection
- [human-gates.md](references/human-gates.md)
- [change-brief.md](references/change-brief.md) — scope premise
- [change-context.md](references/change-context.md) — existing structure signals (stack, layout)
- [work-plan.schema.json](references/work-plan.schema.json) — read `items[].touches` as the primary structural-change signal
- [contract-layout.md](references/contract-layout.md) — default artifact paths
- [working-language.md](references/working-language.md) — `summary`/reasoning/DSL description string language

## Constraints

- Edit only the Architecture Model and its generated projection (no OpenAPI / OCL / formal / implementation edits, no ApplicationPlan)
- Do not require or name a specific architectural style (DDD, Clean Architecture, Hexagonal, Onion, MVC, CQRS, Event Sourcing, …) — the model only records modules/dependencies/ownership/constraints, not a methodology
- Decide structure from Logical Decomposition first (responsibility / state ownership / knowledge ownership / change locality), not from the directory tree — physical structure is a later, separate concern ([physical-design.md](references/physical-design.md), Level 3 only)
- When writing `physical-design.md`, stop at module/package/directory/class/process/service/database/adapter boundary and Physical Dependency allocation — do not pre-design every class, method, function, or implementation algorithm (that is Implementation)
- Never add filesystem paths/filenames as `properties` on a `workspace.dsl` element — `workspace.dsl` is the Logical Model, not a filesystem index; record Logical → Physical mappings in `physical-design.md` only when [architecture-traceability.md](references/architecture-traceability.md)'s triggers apply
- Judge from the existing Architecture Model (read it first) plus this change's WorkPlan `touches` / Brief scope — do not redesign structure the change does not touch
- Do not pad `workspace.dsl` with unrelated existing elements' `change:<id>` tags just to look complete; do not skip tagging touched elements/relationships to avoid writing a plan when `touches` implies a new module/boundary/dependency-direction change
- Populate `properties["owns"]` / `properties["public"]` / a relationship's `kind:*` tag only when confidently derivable from context — never guess to fill out the model
- Set `human_gate` on the generated `architecture-plan.json` per [human-gates.md](references/human-gates.md) (large boundary change, external-boundary change, dependency-direction reversal, or deliberate change to an existing structural constraint) — do not gate ordinary additive module/dependency additions
- Never hand-edit `architecture-plan.json` directly — always regenerate it via `scripts/solidsdd-architecture.sh project`
- DSL identifiers and JSON keys English; human-readable `description`/reasoning strings in the **working language** ([working-language.md](references/working-language.md))

## Steps

1. Read change intent, active Change Context and ChangeBrief, and the WorkPlan (`items[].touches` across all items is the primary signal for structural change). Resolve working language from project rule or Context §6.
2. Read the existing `.solidsdd/architecture/workspace.dsl` and `invariants.yaml` (treat as empty if they don't exist yet — this is the first structural change in the project).
3. Apply the "When architecture changes" / "When architecture does not change" tables in [architecture-axes.md](references/architecture-axes.md).
4. If no trigger applies: emit `{"version": "1", "status": "unchanged", "change_id": ..., "summary": "..."}` directly as `architecture-plan.json` and stop — do not touch the Architecture Model or write `architecture-reasoning.md` (Level 0, [architecture-depth.md](references/architecture-depth.md)).
5. If a trigger applies, determine the required [Architecture Depth](references/architecture-depth.md) (Level 1–4).
6. Extract Decision Drivers when this change's boundary/dependency decision needs justification beyond the trigger itself ([architecture-axes.md](references/architecture-axes.md) Decision Drivers) — most Level 1 deltas skip this.
7. At Level 2+, work through Logical Decomposition (Responsibility / State Ownership / Knowledge Ownership / Change Locality, plus Consistency Boundary / Concurrency Boundary when this change hinges on either — [architecture-axes.md](references/architecture-axes.md)) before deciding boundaries.
8. Decide the boundary and dependency direction for this change's structural delta.
9. Write `.solidsdd/changes/<change_id>/architecture-reasoning.md` from the [template](references/architecture-reasoning-template.md) — record *why*, not the structure itself, including Decision Drivers when extracted.
10. Edit `workspace.dsl`: add/modify elements and relationships per [structurizr-dsl.md](references/structurizr-dsl.md), tagging every element/relationship this change adds or modifies with `change:<change_id>` (append to existing tags, don't replace them). Edit `invariants.yaml` if a constraint or invariant is added, changed, or deliberately removed.
11. At Level 3, when one of the [explicit-traceability triggers](references/architecture-traceability.md) applies (not a trivial 1:1 rename), write `.solidsdd/changes/<change_id>/physical-design.md` from the [template](references/physical-design.md) — module/package/directory/class/process/service/database/adapter boundary and Physical Dependency, stopping short of class/method/algorithm design. Do not add filesystem paths to `workspace.dsl` itself.
12. Run `scripts/solidsdd-architecture.sh validate --project-root <project>` and fix any findings before continuing.
13. Run `scripts/solidsdd-architecture.sh project --project-root <project> --change-id <change_id> --out .solidsdd/changes/<change_id>/architecture-plan.json` to generate the projection.
14. Apply human-gate rules from [human-gates.md](references/human-gates.md) by adding `human_gate` to the generated `architecture-plan.json` when required, then re-validate against [architecture-plan.schema.json](references/architecture-plan.schema.json).

## Output

At Level 0: `architecture-plan.json` with `status: unchanged`, plus a
one-paragraph summary.

At Level 1+: the edited `.solidsdd/architecture/{workspace.dsl,invariants.yaml}`,
a new `.solidsdd/changes/<change_id>/architecture-reasoning.md`, and the
generated `.solidsdd/changes/<change_id>/architecture-plan.json`
(`status: changed`), conforming to the ArchitecturePlan schema. At Level 3,
additionally `.solidsdd/changes/<change_id>/physical-design.md` when the
physical realization decision was non-obvious enough to write one.

When invoked from `solidsdd-run`, **write** these files under the project's
`.solidsdd/` tree (caller supplies the change_id) and return the artifacts
to the parent unchanged in meaning. Known limitation: the projection is
additive-only — element/relationship deletions and renames are not
reflected in `architecture-plan.json`; note them explicitly in
`architecture-reasoning.md` instead.

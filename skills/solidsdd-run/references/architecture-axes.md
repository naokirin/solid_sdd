# Architecture axes (structural design)

`solidsdd-architecture` decides whether a change affects existing **structure**
(modules, responsibilities, dependencies, public boundaries, ownership) and, when it
does, edits the Architecture Model. This is judgment about *structure*, not about
*which specification technique applies where* (that is `solidsdd-judge` /
`ApplicationPlan` — see Role separation below) and not about *behavior*
(that is Gherkin).

Structure lives in `.solidsdd/architecture/workspace.dsl` (Structurizr DSL
subset — see [structurizr-dsl.md](structurizr-dsl.md)) and `invariants.yaml`
(forbidden dependencies / no-cycles / prose invariants), both persistent and
whole-project. `ArchitecturePlan` (`architecture-plan.json`) is still
generated per change — now as a deterministic **projection** of that model
(`scripts/solidsdd-architecture/project.py`), for existing consumers
(`solidsdd-lint`, `solidsdd-critique`, `solidsdd-report`). The *why* behind a
structural decision goes in `architecture-reasoning.md`, not in the DSL or
the projected JSON — see
[architecture-reasoning-template.md](architecture-reasoning-template.md).
How much of this a given change needs is decided by
[architecture-depth.md](architecture-depth.md); most changes stay at Level 0
(no trigger below applies) and never touch the model at all.

`ArchitecturePlan` is not a design methodology. Do not require DDD, Clean
Architecture, Hexagonal Architecture, Onion Architecture, MVC, CQRS, or Event
Sourcing. It only names modules, responsibilities, dependencies, dependency
direction, public boundaries, ownership, and structural constraints — whatever
structure this project already has, or this change proposes.

## Existing structure vs. new design

When a codebase already exists, read Context first (existing modules, directory
layout, existing OpenAPI/OCL boundaries) and treat that as the current structure.
Do not invent an "ideal" redesign of structure the change does not touch. The
judgment is:

```text
existing architecture + change requirements → proposed architecture (delta only)
```

Only describe modules/dependencies that are new or changed by this WorkPlan; do not
re-document unrelated existing structure just to have a "complete" diagram.

## Decision Drivers

Before Logical Decomposition, when this change's boundary/dependency decision
needs justification beyond the trigger itself, extract the Decision Drivers
that will be used to evaluate design alternatives:

```text
Requirement
    ↓
Decision Drivers
    ↓
Design Alternatives (Logical Decomposition)
    ↓
Architecture Decision (Boundary / Dependency)
```

A Decision Driver is a constraint, goal, or evaluation criterion the
Architecture Decision must satisfy — not a restatement of the Requirement.
Consider, only when relevant to this change: business constraints, state
ownership constraints, consistency requirements, concurrency requirements,
change locality requirements, external dependency constraints,
security/isolation constraints, and architecturally-relevant performance
constraints.

```text
Requirement: order processing must not corrupt inventory counts when two
orders race for the same stock.

Decision Drivers:
- Inventory state must have a single owner.
- Concurrent reservation must share a consistency boundary.
- Order processing must not directly mutate inventory state.
```

Do not enumerate Decision Drivers for every change — most Level 1 deltas
(see [architecture-depth.md](architecture-depth.md)) have none worth
recording. Record them in `architecture-reasoning.md`
([template](architecture-reasoning-template.md)), not as a separate
document.

## Logical Decomposition axes

Before naming modules or editing `workspace.dsl`, decide structure from
**logical** decomposition, not from the directory tree. Physical structure
(package/directory/file/class) is a later, separate concern — see
[architecture-depth.md](architecture-depth.md) Level 3. Consider, only to
the depth this change actually needs:

| Axis | Question |
|---|---|
| Responsibility | Who is responsible for this concept/behavior? |
| Cohesion | Do the elements inside one boundary share the same purpose and change reason? |
| Coupling | Is a dependency between boundaries stronger than it needs to be? |
| Change locality | Does one change reason stay inside one boundary, or does it spill into unrelated boundaries? |
| State ownership | Is there exactly one owner for this state? (`properties { "owns" ... }` in the DSL) |
| Knowledge ownership | Is this domain rule kept in one place, or duplicated/scattered? |
| Consistency | Should state that must stay consistent together live in the same boundary? |
| Concurrency | Which boundary controls a race, if any? (Architecture states *where*; TLA+/Alloy states the *transition property* — see Role separation below) |
| External boundary | Where is an external system's dependency isolated? |

Not every axis applies to every change — judge from the WorkPlan `touches` /
Brief scope, the same density philosophy as the rest of this document. A
Level 1 delta (see [architecture-depth.md](architecture-depth.md)) usually
only needs Responsibility and State/Knowledge Ownership; the rest matter
more at Level 2+ (a genuine boundary re-split).

## When architecture changes (emit status: changed)

| Trigger | Example |
|---------|---------|
| New module | This change introduces a directory/package/service that didn't exist |
| Changed module boundary or responsibility | An existing module's responsibility is redefined, split, or merged |
| Changed dependency direction | A module starts depending on something it previously didn't, or a dependency direction is reversed |
| New public boundary | A module exposes a new service/facade/API surface to other modules |
| Changed data/state owner | Ownership of an entity or piece of state moves to a different module |
| Changed external-system boundary | A new external system integration point, or an existing one changes shape |

## When architecture does not change (emit status: unchanged)

| Non-trigger | Example |
|-------------|---------|
| Internal implementation change | Refactoring inside a module without changing its responsibility or public boundary |
| Existing API's internal implementation change | Behavior fix that doesn't touch the module's boundary or dependencies |
| UI-only / presentation-only change | Local, non-structural adjustment |
| Non-structural bugfix | Fix does not add/remove/redirect a dependency or module |

When in doubt, prefer `status: unchanged` with a one-line `summary` explaining why,
over padding out empty `modules`/`dependencies`/`constraints` arrays to "look
thorough." A trivial change does not need an ArchitecturePlan (brief §6.3).

Cross-check `status` against the WorkPlan: when any item's `touches` implies a new
module directory, a new public boundary, or a changed dependency direction,
`status: unchanged` is very likely wrong (see the "status shortcut misuse" row in
[adversarial-critique.md](adversarial-critique.md)).

## Field minimality rules

These now apply to what you write in `workspace.dsl` / `invariants.yaml`
(the projection carries them into `architecture-plan.json` automatically —
see [structurizr-dsl.md](structurizr-dsl.md)):

- `properties { "owns" ... }` / `properties { "public" ... }`: populate only
  when confidently derivable from Context / the codebase / the WorkPlan — do
  not guess to fill out the model. Omitting the property is correct when
  ownership or the public surface isn't yet decided by this change.
- `dependency.kind` (projected JSON): only set when a relationship carries an
  explicit `kind:runtime` / `kind:data` / `kind:event` / `kind:api` tag; do
  not add that tag just to fill out the field.
- `constraint.type` in `invariants.yaml`: use `forbid_dependency` for a
  specific forbidden edge, and `no_cycles` (`scope: all`) only when the
  project actually wants a general "no dependency cycles" rule enforced. Do
  not introduce new constraint types — grow this enum only when a concrete
  verification need shows up (mirrors `judgment-axes.md`'s density
  philosophy: judge from real signals, not completeness).
- `reason` strings (relationship description, `invariants.yaml`
  `constraint.reason`): cite the WorkPlan `touches` / Brief scope that
  motivated the module/dependency/constraint, the same way `judgment-axes.md`
  expects `ApplicationPlan.targets[].rationale` to cite a signal id.
- `Technology` (element field) and `views` (workspace block) follow the same
  rule as `owns`/`public`, not a separate one: populate `Technology` only
  when unambiguously derivable (e.g. every WorkPlan `touches` path for that
  element shares one language/runtime extension) — leave it blank rather
  than guessing from a partial or extension-less `touches` glob. Add a
  `views` block only when it aids readability for a Level 2+ change with
  multiple elements/relationships; skip it for Level 0/1 deltas where one or
  two elements are already easy to read directly from `model {}`.

## Human gate

Gate (`human_gate.required: true`) only for: a large module/boundary change, a
change to an **external-facing** boundary, a reversal of an existing dependency
direction, or a deliberate removal/change of an existing structural `constraint`.
Do not gate ordinary additive module or dependency additions — see
[human-gates.md](human-gates.md). A project's **first-ever** Architecture
Model (no `workspace.dsl` existed before this change) counts as a large/
external-facing change by default, since there is no prior structure to
measure "ordinary additive" against — gate it unless the model is genuinely
small and entirely internal.

## Role separation

| Artifact | Answers |
|----------|---------|
| Gherkin | What behavior is required? |
| `ArchitecturePlan` | How is the system structurally organized (modules / dependencies / ownership / constraints)? |
| `ApplicationPlan` | Which specification mechanism (API / DbC / formal) applies where? |
| OpenAPI / GraphQL | What is the external API contract? |
| OCL / DbC | What local invariants/contracts must hold? |
| TLA+ / Alloy | What state/temporal properties must hold? |

Do not describe behavior in `ArchitecturePlan`. Do not use Gherkin to record module
dependencies. Do not use TLA+/Alloy to express ordinary module structure. Each
artifact stays scoped to the question above.

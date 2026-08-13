# Architecture axes (structural design)

`solidsdd-architecture` decides whether a change affects existing **structure**
(modules, responsibilities, dependencies, public boundaries, ownership) and, when it
does, emits an `ArchitecturePlan`. This is judgment about *structure*, not about
*which specification technique applies where* (that is `solidsdd-judge` /
`ApplicationPlan` — see Role separation below) and not about *behavior*
(that is Gherkin).

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

- `module.owns` / `module.public`: populate only when confidently derivable from
  Context / the codebase / the WorkPlan — do not guess to fill out the schema. An
  empty/omitted array is correct when ownership or the public surface isn't yet
  decided by this change.
- `dependency.kind`: use only when the kind (`runtime` / `data` / `event` / `api`)
  is actually known; omit rather than guess.
- `constraint.type`: use `forbid_dependency` for a specific forbidden edge, and
  `no_cycles` only when the project actually wants a general "no dependency cycles
  among these modules" rule enforced. Do not introduce new constraint types — grow
  this enum only when a concrete verification need shows up (mirrors
  `judgment-axes.md`'s density philosophy: judge from real signals, not
  completeness).
- `rationale`/`reason` strings: cite the WorkPlan `touches` / Brief scope that
  motivated the module/dependency/constraint, the same way `judgment-axes.md`
  expects `ApplicationPlan.targets[].rationale` to cite a signal id.

## Human gate

Gate (`human_gate.required: true`) only for: a large module/boundary change, a
change to an **external-facing** boundary, a reversal of an existing dependency
direction, or a deliberate removal/change of an existing structural `constraint`.
Do not gate ordinary additive module or dependency additions — see
[human-gates.md](human-gates.md).

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

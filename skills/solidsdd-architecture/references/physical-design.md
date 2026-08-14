# Physical Design

Physical Design decides **how a Logical Architecture element is realized as
actual software structure** — module, package, namespace, directory, file
boundary, class boundary, process boundary, service boundary, database
boundary, or adapter boundary. It is not a directory listing:

```text
Logical Architecture          What is responsible for what?
        ↓
Physical Design                How is that structure physically realized?
        ↓
Implementation                 Concrete files/classes/functions
```

Logical Architecture (`.solidsdd/architecture/workspace.dsl`) stays the
Source of Truth for *structure* (responsibility, ownership, dependency
direction). Physical Design is a separate, later judgment about *allocation*
— which concrete module/package/directory/process/service/database/adapter
boundary enforces a given Logical boundary. Do not let directory structure
drive the Logical decision (see [architecture-axes.md](architecture-axes.md)
"Existing structure vs. new design"); Physical Design comes after the
Logical boundary is already decided, not before.

## When to write this

Only at [Architecture Depth](architecture-depth.md) Level 3, and only when
the physical realization decision itself is non-obvious — e.g. one Logical
element maps to several physical modules, several Logical elements share one
physical module, or the boundary must be enforced through a mechanism (package
visibility, process boundary, service boundary, database boundary) that isn't
self-evident from the element's name. Skip it when the mapping is a trivial
1:1 rename (`Inventory` → `src/inventory/`) — recording that adds no
information.

## Physical Design Decisions

Consider, only to the depth this change actually needs:

| Decision | Question |
|---|---|
| Module / package / namespace | What is the physical unit that carries this Logical element's code? |
| Directory / file boundary | Where does this Logical element's code live, and where does it stop? |
| Class boundary | Does this Logical element need more than one physical class/type to stay cohesive? |
| Process / service boundary | Does this Logical element need to run as (or be split across) a separate process/service? |
| Database boundary | Does this Logical element own a separate schema/database, or share one? |
| Adapter boundary | Where does an external-system dependency get isolated in code? |

## Physical Dependency

A Logical dependency direction must be reflected in the corresponding
Physical dependency — including when the physical realization inverts it
(e.g. a port/adapter pair) to keep the Logical direction intact:

```text
Logical:                        Physical:

Order                           order/
  ↓                                ↓
Payment                         payment_port/

                                 infrastructure/payment/ → payment_port/
```

## Physical Boundary enforcement

Use whichever mechanism actually enforces the Logical boundary in this
stack — do not name all of them by default:

* package / module visibility
* namespace
* interface / port
* API (process or service boundary)
* dependency-direction rules (lint / build-time)

## Artifact

Only when Physical Design is a significant judgment for this change (see
"When to write this" above):

`.solidsdd/changes/<change_id>/physical-design.md`

```markdown
# Physical Design

## Logical Elements

- Inventory
- Reservation

## Physical Realization

| Logical Element | Physical Realization |
|---|---|
| Inventory | `src/domain/inventory/` |
| Reservation | `src/domain/inventory/reservation/` |

## Physical Boundaries

- ...

## Physical Dependencies

- ...
```

Keep entries short — one line per row is normal. Omit a section that
genuinely doesn't apply.

## Do Not

Physical Design stops at boundaries and allocation. Do not pre-design:

* every class
* every method / function
* implementation algorithm

Those are decided during Implementation, not Architecture.

## Relation to solid_sdd Skills

This is a `solidsdd-architecture` responsibility at Architecture Depth
Level 3 — there is no separate Module Skill in solid_sdd today, so this
concern does not need to be split out to avoid duplicating one. If a
dedicated skill for physical/module design is introduced later, it should
read this file rather than redefine Physical Design from scratch.

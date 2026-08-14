# Structurizr DSL (solid_sdd subset)

`.solidsdd/architecture/workspace.dsl` is the Single Source of Truth for
structure (elements, relationships, hierarchy, tags, properties, views) —
not a diagram-generation artifact. It is persistent and **whole-project**:
it accumulates across changes, unlike the per-change `architecture-plan.json`
projection (see [contract-layout.md](contract-layout.md)).

This is a real subset of Structurizr DSL syntax (not an invented dialect),
parsed and validated by `scripts/solidsdd-architecture/dsl.py` (no Java/JVM
required). A file using only this subset also parses with the real
Structurizr CLI, should that ever be introduced as an optional toolchain
(see [architecture-depth.md](architecture-depth.md) — this project does not
require it).

## Grammar

```text
workspace "Name" ["Description"] {
  model {
    [group "Label" { <softwareSystem decl>* }]
    <id> = softwareSystem "Name" ["Description"] {
      [tags "Tag1, Tag2"]
      [properties { "key" "value" ... }]
      <id> = container "Name" ["Description"] ["Technology"] {
        [tags "..."] [properties { ... }]
        <id> = component "Name" ["Description"] ["Technology"] {
          [tags "..."] [properties { ... }]
          <id> -> <id> ["desc"] ["tech"] { [tags "..."] }
        }
        <id> -> <id> ...
      }
      <id> -> <id> ...
    }
    <id> -> <id> ["desc"] ["tech"] { [tags "..."] }
  }
  views {
    (systemContext|container|component) <id> {
      include (* | <id>+)
      autoLayout [direction]
    }
  }
}
```

Identifiers must match `^[a-z][a-z0-9_]*$` (underscore, not hyphen).
`scripts/solidsdd-architecture/project.py` converts underscore to hyphen
when projecting an element id into an `ArchitecturePlan` module id, which
requires `^[a-z0-9]+(-[a-z0-9]+)*$`.

Elements nest exactly three levels deep: `softwareSystem` → `container` →
`component`. Not every change needs all three — most changes only need
`softwareSystem` (or a couple of `container`s); see
[architecture-depth.md](architecture-depth.md) for how much structure a
given change actually needs.

## Unsupported (v1)

`person`, `deploymentNode`, dynamic views, styles, themes, `!include`,
scripting, hierarchical identifiers. The parser fails closed on these —
it names the offending line rather than silently ignoring the construct.
Do not work around this by inventing ad hoc syntax; if a change genuinely
needs one of these, treat it as a signal that Structurizr CLI (optional
toolchain) may be worth introducing, and raise that as a separate decision
rather than hand-rolling support.

## How solid_sdd concepts map onto the DSL

| Concept (see [architecture-axes.md](architecture-axes.md)) | DSL representation |
|---|---|
| Module / responsibility | An element (`softwareSystem`/`container`/`component`); `description` is the responsibility |
| State ownership | `properties { "owns" "Thing1, Thing2" }` on the owning element |
| Knowledge ownership | Same as state ownership, or a one-line note in [architecture-reasoning.md](architecture-reasoning-template.md) when it's a rule, not a data item |
| Public boundary | `properties { "public" "Name1, Name2" }`, and/or `tags "Public"` on a `component` that other modules may depend on directly |
| Dependency / dependency direction | A relationship `<id> -> <id>` |
| Forbidden dependency / no-cycles constraint | `.solidsdd/architecture/invariants.yaml` `constraints[]` — **not** expressed in the DSL, since Structurizr models only positive relationships |
| Architecture Invariant (prose) | `invariants.yaml` `invariants[]` — not mechanically verified, kept as a durable readable list |
| Change attribution | `tags` includes `change:<change_id>` on elements/relationships this change added or modified (existing tags are preserved, not replaced) |

Do not duplicate the same structural fact in both the DSL and
`invariants.yaml` — elements/relationships/hierarchy/tags/properties live
in the DSL; only rules *about* that structure (forbidden edges, cycle
policy, prose invariants) live in `invariants.yaml`.

## Limitations (v1)

- **Additive only.** `scripts/solidsdd-architecture/project.py` derives the
  per-change `architecture-plan.json` from `change:<change_id>` tags. It
  does not detect deletions or renames of elements/relationships — note
  those explicitly in `architecture-reasoning.md` when they happen.
- **Prose invariants are not mechanically checked.** Only `constraints[]`
  entries (`forbid_dependency`, `no_cycles`) are verified by
  `scripts/solidsdd-architecture/validate.py`.

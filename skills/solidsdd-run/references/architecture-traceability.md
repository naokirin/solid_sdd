# Architecture Traceability

Makes the `Requirement → Logical Architecture → Physical Design` chain
traceable **when it matters**, without turning every mapping into a
maintained artifact:

```text
Requirement
    ↓
Logical Architecture     .solidsdd/architecture/workspace.dsl
    ↓
Physical Design           .solidsdd/changes/<change_id>/physical-design.md (optional — see below)
    ↓
Implementation             actual source — see "Implementation Conformance" below
```

The first three links are traceability in the ordinary sense: each is a
lookup between two **declared** artifacts. The last link (Physical Design →
Implementation) is different in kind — see "Implementation Conformance"
below — do not conflate the two.

## Logical → Physical

When [physical-design.md](physical-design.md) exists, its "Physical
Realization" table already **is** the Logical → Physical trace — a Logical
element id maps to one or more concrete paths. Do not maintain a second,
separate mapping artifact for the same fact.

## Physical → Implementation: Implementation Conformance

Physical Design entries name real repository paths, so **finding** the
implementation is a lookup, not a separate concern: read the path from
`physical-design.md`'s table (or, when no `physical-design.md` was written,
the element's `name`/`description` in `workspace.dsl`) and it points at
where the code should live. This lookup holds by construction — that part
genuinely is traceability.

Whether the code **at that path still does what was declared** — the
boundary is actually enforced, the allocation hasn't silently drifted since
the change that wrote `physical-design.md` — is a different question:
**Implementation Conformance**, not traceability. Traceability only answers
"where do I look"; conformance answers "does what's there still match the
plan". solid_sdd does not verify conformance mechanically —
`scripts/solidsdd-architecture/physical.py` only cross-checks
`physical-design.md` against the Architecture Model itself (declared facts
against declared facts, e.g. that a Physical Dependency doesn't violate a
`forbid_dependency` constraint — never against actual source; no
import-graph / directory-convention static analysis). Conformance stays a
`solidsdd-critique` / human-review concern, and it can drift silently after
`physical-design.md` is written, since code keeps changing while the
Architecture artifact usually doesn't.

## When explicit traceability is required

Only bother recording an explicit Logical → Physical mapping (in
`physical-design.md`) when at least one applies:

* Logical boundary and Physical boundary diverge significantly
* one Logical element spans several Physical modules
* several Logical elements are realized by one Physical module
* migration in progress: old and new physical structure coexist for the same
  Logical element — list both rows with a short note on which is being
  phased out, rather than inventing a separate migration-tracking artifact
* the mapping is itself an architecturally significant decision

Otherwise (`Inventory` → `src/inventory/`), don't record it — it is
self-evident from the code. This is the same density philosophy as the rest
of this reference set (see [architecture-axes.md](architecture-axes.md)
Field minimality rules): record signal, not completeness.

## Do Not

* Don't embed filesystem metadata (paths, filenames) as `properties` in
  `workspace.dsl` — the Structurizr Model is the Logical Architecture Source
  of Truth, not a filesystem index. Put path mappings in
  [physical-design.md](physical-design.md) instead — see
  [structurizr-dsl.md](structurizr-dsl.md).
* Don't record traceability for every element by default — most changes need
  none.
* Don't introduce a new persistent Source of Truth for mappings.
  `physical-design.md` is change-local reasoning (like
  `architecture-reasoning.md`), not a living database that must be kept in
  sync forever; there is no requirement to retroactively update it when a
  later, unrelated change moves files.
* Don't treat Logical → Physical traceability as proof of Implementation
  Conformance — they are different guarantees. A correct, up-to-date mapping
  table says nothing about whether the code at that path still honors it.

## Relation to ArchitecturePlan

`architecture-plan.json` stays a projection of **Logical** structure only
(modules/dependencies/ownership/constraints — schema:
[architecture-plan.schema.json](architecture-plan.schema.json), which does
not accept unknown fields). It does not gain fields for physical paths or
mappings. Traceability information lives in `physical-design.md` alongside
the reasoning that produced it, never inside the generated projection.

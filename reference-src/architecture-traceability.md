# Architecture Traceability

Makes the `Requirement → Logical Architecture → Physical Design →
Implementation` chain traceable **when it matters**, without turning every
mapping into a maintained artifact:

```text
Requirement
    ↓
Logical Architecture     .solidsdd/architecture/workspace.dsl
    ↓
Physical Design           .solidsdd/changes/<change_id>/physical-design.md (optional — see below)
    ↓
Implementation             actual source
```

## Logical → Physical

When [physical-design.md](physical-design.md) exists, its "Physical
Realization" table already **is** the Logical → Physical trace — a Logical
element id maps to one or more concrete paths. Do not maintain a second,
separate mapping artifact for the same fact.

## Physical → Implementation

Physical Design entries name real repository paths, so Physical →
Implementation traceability holds by construction: read the path from
`physical-design.md`'s table (or, when no `physical-design.md` was written,
the element's `name`/`description` in `workspace.dsl`) and it points at the
actual source. No extra bookkeeping is needed beyond that, except for the
migration case below.

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

## Relation to ArchitecturePlan

`architecture-plan.json` stays a projection of **Logical** structure only
(modules/dependencies/ownership/constraints — schema:
[architecture-plan.schema.json](architecture-plan.schema.json), which does
not accept unknown fields). It does not gain fields for physical paths or
mappings. Traceability information lives in `physical-design.md` alongside
the reasoning that produced it, never inside the generated projection.

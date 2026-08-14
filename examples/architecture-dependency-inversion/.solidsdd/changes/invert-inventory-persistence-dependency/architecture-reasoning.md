# Architecture Reasoning

## Change

invert-inventory-persistence-dependency

## Design Problem

`establish-inventory-persistence` left Inventory (domain) depending
directly on `PostgresInventoryStore` (a concrete infrastructure
implementation):

```text
Before:  Inventory -> PostgresInventoryStore
```

This couples the domain module to one specific persistence technology.
Swapping stores, or testing Inventory without a real Postgres instance,
requires touching the domain module itself.

## Logical Decomposition

### Responsibility

Unchanged from `establish-inventory-persistence`: Inventory owns available
stock; PostgresInventoryStore is a concrete persistence mechanism. What
changes is *how* they relate, not what each is responsible for.

### Change Locality

Today, a persistence-technology change (e.g. moving off Postgres) would
force a change to Inventory's dependency, even though Inventory's own
responsibility (owning stock) hasn't changed. Inverting the dependency
keeps that reason for change (persistence technology) local to the
infrastructure side.

## Boundary Decisions

Add `inventory_repository_port`, a `container` nested inside `inventory`:
the persistence abstraction Inventory depends on. It is tagged `Public` —
this is the one internal element of `inventory` that other systems are
allowed to depend on directly (see
[structurizr-dsl.md](../../../../../reference-src/structurizr-dsl.md) on
why crossing into an untagged internal `component` would otherwise be
flagged as boundary leakage; a `container`-level port is the right
granularity for this).

## Dependency Decisions

```text
After:  Inventory -> InventoryRepositoryPort <- PostgresInventoryStore
```

- `inventory -> inventory_repository_port`: Inventory depends on the
  abstraction it owns, not on a concrete implementation.
- `postgres_store -> inventory_repository_port`: PostgresInventoryStore
  implements/depends on the port instead of being depended upon.
- The old `inventory -> postgres_store` edge is removed entirely (compare
  this change's `workspace.dsl` against `establish-inventory-persistence`'s
  via `git diff` — the direct edge is gone, replaced by two edges into the
  port).
- `postgres_store -> inventory` is now explicitly forbidden in
  `invariants.yaml`, so a future change can't silently reintroduce the
  direct coupling this change removes.

Direction reversal like this is exactly the kind of change
[human-gates.md](../../../../../reference-src/human-gates.md) calls out for
human review in a real project (dependency-direction reversal); it's
demonstrated here for illustration.

## Alternatives Considered

Keeping the direct dependency and only adding tests with a real Postgres
instance was considered and rejected: it doesn't remove the coupling, it
just hides the cost of it.

## Trade-offs

One extra element (the port) and one extra hop for what is, in this
minimal example, a single persistence technology. Accepted because the
example's whole purpose is to show *when* this trade-off is worth taking
(when persistence swap/testability actually matters), not to claim it's
always worth it — see [architecture-axes.md](../../../../../reference-src/architecture-axes.md)
on judging structure from real signals, not completeness.

## Architecture Invariants

- Inventory owns available stock per SKU.
- Inventory depends only on the persistence port, never on a concrete
  persistence technology directly.
- PostgresInventoryStore must not depend on Inventory directly
  (`forbid_dependency` in `invariants.yaml`).

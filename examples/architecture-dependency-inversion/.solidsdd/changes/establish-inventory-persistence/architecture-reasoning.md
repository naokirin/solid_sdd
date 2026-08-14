# Architecture Reasoning

## Change

establish-inventory-persistence

## Design Problem

Inventory needs somewhere to persist stock rows. This change establishes
the simplest possible baseline: Inventory (domain) depends directly on a
concrete PostgreSQL persistence module.

## Logical Decomposition

### Responsibility

- Inventory: own available stock per SKU.
- PostgresInventoryStore: concrete PostgreSQL persistence for stock rows.

### State Ownership

Inventory owns `Stock`. PostgresInventoryStore has no owned domain state of
its own — it is a persistence mechanism, not a state owner.

## Boundary Decisions

Two systems: `inventory` (domain) and `postgres_store` (infrastructure).

## Dependency Decisions

`inventory -> postgres_store`, direct: Inventory reads/writes stock rows
through this dependency. This is deliberately the naive baseline — Domain
depending directly on a concrete Infrastructure implementation — used as
the "Before" state for the follow-on change
`invert-inventory-persistence-dependency`, which introduces a port and
inverts this dependency. See that change's `architecture-reasoning.md` for
why this direct dependency is a problem worth fixing.

## Trade-offs

Simple, but couples Inventory to one specific persistence technology and
makes Inventory hard to test without a real (or heavily mocked) Postgres
store. Accepted here only as an illustrative starting point.

## Architecture Invariants

- Inventory owns available stock per SKU.

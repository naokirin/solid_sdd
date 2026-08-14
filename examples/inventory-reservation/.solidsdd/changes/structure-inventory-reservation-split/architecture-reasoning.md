# Architecture Reasoning

## Change

structure-inventory-reservation-split

## Design Problem

The sample's reservation logic and stock ownership live in a single
`reservation.ts` module. Future stock-related work (e.g. multi-warehouse)
would have to carry hold/TTL/authZ concerns along with it, even though
those concerns have nothing to do with stock ownership.

## Logical Decomposition

### Responsibility

- Inventory is responsible for available stock per SKU.
- Reservation is responsible for hold lifecycle (reserve/release/expire/lookup)
  and TTL/authZ enforcement.

### State Ownership

Inventory owns `Stock`. Reservation owns `Hold`. Neither currently reads or
mutates the other's owned state directly — Reservation calls Inventory's
public surface instead.

### Knowledge Ownership

The rule for what counts as "available" stock stays in Inventory.
Reservation does not independently recompute availability; it depends on
Inventory's `InventoryService` for that.

### Change Locality

A future multi-warehouse change only needs to touch Inventory. A future
change to hold expiry/authZ policy only needs to touch Reservation. Today,
both reasons for change are entangled in one file.

## Boundary Decisions

Two modules, `inventory` and `reservation`, each with one public
facade (`InventoryService` / `ReservationService`) so callers don't depend
on internal storage details.

## Dependency Decisions

`reservation -> inventory`: reserving/releasing a hold must read and adjust
available stock, so the dependency is necessary and this direction is the
only one that keeps Inventory reusable independent of Reservation. The
reverse edge (`inventory -> reservation`) is explicitly forbidden in
`invariants.yaml` — Inventory must not need to know about holds/TTL/authZ.

## Alternatives Considered

Keeping a single module was considered and rejected: it would require every
consumer of stock data to accept the hold/TTL/authZ dependency, which isn't
needed for e.g. a future multi-warehouse read path.

## Trade-offs

Two modules with an explicit facade each adds a small amount of ceremony
(a `ReservationService`/`InventoryService` boundary) for what is currently a
small sample. Accepted because the split's whole purpose is to keep that
ceremony from growing unbounded later.

## Architecture Invariants

- Inventory owns available stock per SKU.
- Reservation owns hold lifecycle and TTL/authZ enforcement.
- Inventory must not depend on Reservation (`forbid_dependency` in
  `invariants.yaml`).

## Known limitations

Design-only: this repository's implementation intentionally stays a single
`reservation.ts` file for now (see README "Out of scope"). Physical
decomposition into separate modules/files is not part of this change.

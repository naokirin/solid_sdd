# Architecture Reasoning

## Change

establish-exclusive-memory-architecture

## Design Problem

Multiple clients need to safely increment a shared register without lost
updates from overlapping writes. `formal/ExclusiveMemory.tla` already
checks this property, but nothing recorded *which module owns the state*
or *why* the boundary is drawn the way it is — this change adds that.

## Logical Decomposition

### Responsibility

- `MemoryRegister`: own the shared register and the exclusive-ownership
  protocol (acquire / add / release).
- `Client`: request ownership, mutate once, release.

### State Ownership

`MemoryRegister` owns `Mem`. No client mutates `Mem` directly — every
mutation goes through `MemoryRegister`'s acquire/add/release surface.

### Concurrency

`MemoryRegister`'s ownership protocol (the `owner` field in the TLA+ model)
*is* the concurrency boundary: only the current owner may execute an add.
This is a structural decision — who is allowed to touch the state, and
through what surface — not a formal property by itself. The formal
property (mutual exclusion always holds, no interleaving loses an update)
is what TLA+ checks; see "Where each layer picks up" below.

## Boundary Decisions

Two modules: `memory_register`, `client`. `client -> memory_register` is
the only dependency; there is no reverse edge.

## Dependency Decisions

`client -> memory_register`: a client depends on the register's
acquire/add/release surface. This is the only direction that lets
`MemoryRegister` remain the sole authority over `Mem` — if the register
depended on clients instead, ownership could not be enforced centrally.

## Trade-offs

None beyond the two-module split itself, which is minimal by design for
this sample.

## Architecture Invariants

- MemoryRegister owns `Mem`; only the current owner may mutate it.
- At most one Client holds ownership at a time (mutual exclusion).

## Where each layer picks up from here

- **Architecture** (this file + `workspace.dsl`): *who* owns `Mem`, and
  that mutation must go through the owner protocol.
- **BDD** ([`requirements/exclusive-memory.feature`](../../../requirements/exclusive-memory.feature)):
  the behavior in Given/When/Then form — a client adds; concurrent clients
  don't lose updates.
- **TLA+** ([`formal/ExclusiveMemory.tla`](../../../formal/ExclusiveMemory.tla)):
  the precise state/transition property that formalizes "only the owner
  mutates, and no interleaving loses an update" — `TypeOK` bounds the
  state, `FinalOK` checks the outcome.

Architecture states *who owns the state and where the boundary is*; TLA+
states the *exact transition semantics*. Neither substitutes for the
other — see the Role separation table in
[architecture-axes.md](../../../../../reference-src/architecture-axes.md).

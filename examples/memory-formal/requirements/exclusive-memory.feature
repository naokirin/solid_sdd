Feature: Exclusive memory register add
  MemoryRegister owns the shared register and enforces mutual exclusion via
  an acquire/add/release protocol, so concurrent adds never lose an update.
  See .solidsdd/architecture/workspace.dsl for the module that owns this
  state and formal/ExclusiveMemory.tla for the checked concurrency property.

  @R1
  Scenario: A single client adds to the register
    Given a memory register owned by MemoryRegister with mem = 0
    When a client acquires ownership and adds once
    Then mem becomes 1
    And the client releases ownership

  @R2
  Scenario: Concurrent clients never lose an update
    Given a memory register owned by MemoryRegister
    And two clients each wanting to add multiple times
    When both clients repeatedly acquire, add, and release, in any interleaving
    Then mem equals the total number of adds performed by both clients
    And at most one client holds ownership at any point in time

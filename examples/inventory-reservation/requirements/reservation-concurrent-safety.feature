Feature: Concurrent last-unit reservation safety
  Under concurrent authorized reserves against the same SKU, available stock
  never goes negative and the last unit yields at most one soft-hold. Race
  losers fail with the same named InsufficientStockError as sequential
  insufficient stock. Opaque-principal AuthZ remains in force. Checkability
  is elevated via additive OpenAPI and UML OCL, then a bounded TLA+/TLC model
  under formal/.

  @R3 @R5 @R6 @SC3 @SC5
  Scenario: OpenAPI and OCL elevate InsufficientStockError and non-negative stock vocabulary
    Given the reservation OpenAPI and module OCL surfaces for soft-hold reserve
    When insufficient-stock and race-loser failure channels and available-stock invariants are inspected
    Then reserve documents named InsufficientStockError for sequential insufficient stock and concurrent race losers on the same named channel
    And OpenAPI elevation is additive without removing or renaming prior success or error surfaces
    And UML OCL makes InsufficientStockError naming and non-negative available stock checkable for sequential and contract-testable paths
    And UnauthorizedError remains the named channel for unauthorized callers

  @R1 @R2 @R3 @R4 @R7 @SC1 @SC2 @SC3 @SC4 @SC5
  Scenario: Concurrent last-unit reserves yield at most one hold and never-negative stock
    Given a reservation service with a SKU whose available stock is one
    And concurrent authorized opaque principals racing to reserve that last unit
    When those principals request soft-hold reservations against that SKU concurrently
    Then available stock never goes negative for any checkable interleaving
    And at most one soft-hold is created
    And race losers fail with named InsufficientStockError and create no extra hold
    And unauthorized concurrent reserve attempts fail with UnauthorizedError without mutating stock or holds
    And a bounded TLA+/TLC model under formal/ is checkable for last-unit exclusivity and non-negative available stock

Feature: Inventory soft-hold reservation
  An authorized opaque principal soft-holds SKU quantity for a TTL,
  reducing available stock. Insufficient stock and unauthorized callers
  fail with named domain errors without creating a hold or mutating stock.
  Authorized release and TTL expiry restore held quantity to available stock.
  Behaviors must be checkable via the HTTP/API and module contracts.

  @R1 @R6 @R7 @SC1 @SC6
  Scenario: Authorized reserve creates a soft-hold and reduces available stock
    Given a reservation service with a SKU whose available stock is at least the requested quantity
    And an authorized opaque principal
    When the principal requests a soft-hold reservation of a quantity against that SKU
    Then a hold is created for a TTL
    And available stock decreases by the reserved quantity

  @R2 @R6 @R7 @SC2 @SC6
  Scenario: Reserve fails when available stock is below the requested quantity
    Given a reservation service with a SKU whose available stock is below the requested quantity
    And an authorized opaque principal
    When the principal requests a soft-hold reservation of that quantity against the SKU
    Then the operation fails with a named domain error
    And no hold is created
    And available stock is unchanged

  @R3 @R6 @R7 @SC3 @SC6
  Scenario: Unauthorized reserve or release fails with a named domain error
    Given a reservation service with stock and holds
    And an unauthorized caller
    When the caller attempts to reserve or release
    Then the operation fails with a named domain error
    And no hold is created by the failed attempt
    And available stock and existing holds are unchanged

  @R4 @R6 @R7 @SC4 @SC6
  Scenario: Authorized release restores held quantity to available stock
    Given an existing soft-hold created by an authorized opaque principal
    When that principal releases the hold
    Then the held quantity is restored to available stock

  @R5 @R6 @R7 @SC5 @SC6
  Scenario: Hold past TTL expires and restores available stock
    Given an existing soft-hold whose TTL has elapsed
    When the reservation service treats the hold as expired
    Then the held quantity is restored to available stock

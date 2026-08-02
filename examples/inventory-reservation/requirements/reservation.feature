Feature: Inventory soft-hold reservation
  Property-level acceptance for the initial-reservation change.

  @R1 @R6 @R7 @SC1 @SC4
  Scenario: Authorized reserve creates a soft hold
    Given an authorized caller and a SKU whose available stock is at least the requested quantity
    When the caller reserves a positive quantity
    Then a soft hold exists for that quantity
    And available stock decreases by that quantity

  @R2 @R6 @R7 @SC2 @SC4
  Scenario: Stock below request fails with a named domain error
    Given an authorized caller and a SKU whose available stock is below the requested quantity
    When the caller reserves that quantity
    Then the operation fails with a named domain error
    And no hold is created
    And available stock is unchanged

  @R3 @R6 @R7 @SC2 @SC4
  Scenario: Unauthorized caller fails with a named domain error
    Given a caller that is not authorized for the SKU
    And the SKU has available stock at least the requested quantity
    When the caller reserves a positive quantity
    Then the operation fails with a named authorization domain error
    And no hold is created
    And available stock is unchanged

  @R4 @R6 @R7 @SC3 @SC4
  Scenario: Release restores held quantity
    Given an authorized caller owns an active hold for a SKU quantity
    When the caller releases that hold
    Then the hold is no longer active
    And available stock increases by the previously held quantity

  @R5 @R6 @R7 @SC3 @SC4
  Scenario: Expired hold restores availability
    Given an active hold whose TTL is in the past
    When the service expires that hold
    Then the hold is no longer active
    And available stock increases by the previously held quantity

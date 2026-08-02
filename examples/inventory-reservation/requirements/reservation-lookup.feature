Feature: Soft-hold reservation lookup by id
  An authorized opaque principal looks up an existing visible soft-hold by id
  and receives hold details without mutating stock or holds. Missing or
  not-visible holds and unauthorized callers fail with named domain errors
  without mutation. Behaviors must be checkable via additive HTTP/API and
  module contracts without breaking prior reserve/release/expire surfaces.

  @R1 @R4 @R5 @SC1 @SC4
  Scenario: Authorized lookup returns an existing visible soft-hold without mutation
    Given a reservation service with an existing visible soft-hold
    And an authorized opaque principal
    When the principal looks up that soft-hold by id
    Then the service returns that hold's details
    And stock and holds are unchanged

  @R2 @R3 @SC2 @SC3 @SC4
  Scenario: Lookup fails with named domain errors without mutation for missing holds and unauthorized callers
    Given a reservation service with stock and soft-holds
    When lookup is attempted for a missing or not-visible soft-hold by an authorized principal, or for an existing soft-hold by an unauthorized caller
    Then the operation fails with a named domain error
    And stock and holds are unchanged

Feature: Soft-hold lookup includes availableStock
  Authorized opaque principals looking up an existing visible soft-hold by id
  receive existing hold details plus current availableStock for that hold's SKU
  without mutating stock or holds. Unauthorized and missing/not-visible paths
  keep named UnauthorizedError / PreconditionError without mutation. OpenAPI
  documents additive availableStock on LookupResponse while prior
  reserve/release/expire/lookup operations remain.

  @R4 @SC4
  Scenario: LookupResponse documents additive availableStock on authorized success
    Given the reservation lookup OpenAPI surface
    When LookupResponse for authorized get-by-id success is inspected
    Then LookupResponse retains holdId, sku, quantity, and expiresAt
    And LookupResponse includes additive availableStock
    And prior reserve, release, expire, and lookup operations remain

  @R1 @R2 @R3 @R5 @SC1 @SC2 @SC3 @SC4
  Scenario: Authorized lookup returns availableStock and preserves named failure channels without mutation
    Given a reservation service with an existing visible soft-hold and stock for that hold's SKU
    And an authorized opaque principal
    When the principal looks up that soft-hold by id
    Then the service returns holdId, sku, quantity, expiresAt, and current availableStock for that hold's SKU
    And stock and holds are unchanged
    And lookup of a missing or not-visible soft-hold fails with PreconditionError without mutation
    And unauthorized lookup fails with UnauthorizedError without mutation

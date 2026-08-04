Feature: Soft-hold collection list
  An authorized opaque principal lists all currently visible soft-holds in the
  same visibility universe as get-by-id, receiving one full dump of
  LookupResponse-equivalent items including availableStock (empty collection
  when none are visible) without filter dimensions and without mutating stock
  or holds. Unauthorized callers fail with UnauthorizedError without mutation.
  Additive OpenAPI GET /reservations and UML OCL with derived Vitest make the
  behaviors checkable without breaking prior reserve/release/expire/lookup/
  concurrent surfaces.

  @R4 @R5 @SC4
  Scenario: OpenAPI and OCL elevate collection list vocabulary for GET /reservations
    Given the reservation OpenAPI and module OCL surfaces
    When the collection list operation and list failure channels are inspected
    Then OpenAPI documents additive GET /reservations alongside existing POST /reservations and GET /reservations/{holdId}
    And prior reserve, release, expire, lookup, and concurrent surfaces remain
    And UML OCL makes authorized full-dump list success (including empty) and UnauthorizedError on list checkable

  @R1 @R2 @SC1 @SC2
  Scenario: Authorized list returns a full dump of visible soft-holds without mutation
    Given a reservation service with zero or more currently visible soft-holds
    And an authorized opaque principal
    When the principal lists soft-holds
    Then the service returns all currently visible soft-holds in the same visibility universe as get-by-id
    And the response is one full dump with no paging and no sku, status, or time filter dimensions
    And each item is LookupResponse-equivalent with holdId, sku, quantity, expiresAt, and availableStock
    And the collection is empty when none are visible
    And stock and holds are unchanged

  @R3 @SC3
  Scenario: Unauthorized list fails with UnauthorizedError without mutation
    Given a reservation service with stock and soft-holds
    And an unauthorized caller
    When the caller attempts to list soft-holds
    Then the operation fails with UnauthorizedError
    And stock and holds are unchanged

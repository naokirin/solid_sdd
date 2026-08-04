Feature: Soft-hold collection list sorted by expiresAt
  Authorized soft-hold collection list already returns an unfiltered full dump
  of currently visible soft-holds (same visibility as get-by-id,
  LookupResponse-equivalent items). This change adds a deterministic order:
  expiresAt ascending (earlier expiry first); equal expiresAt may use any
  stable order. Unauthorized list remains UnauthorizedError without mutation.
  Extending existing GET /reservations / Reservation::list contracts (OpenAPI
  and/or UML OCL + Vitest) makes the sorted success and UnauthorizedError
  checkable without filters, paging, DTO changes, or prior Feature rewrites.

  @R1 @R2 @SC1 @SC2 @SC3
  Scenario: Authorized list returns visible soft-holds sorted by expiresAt ascending without mutating AuthZ or dump shape
    Given a reservation service with zero or more currently visible soft-holds
    And an authorized opaque principal
    When the principal lists soft-holds
    Then the service returns the currently visible soft-holds ordered by expiresAt ascending (earlier first)
    And equal expiresAt may appear in any stable order
    And the response remains one unfiltered full dump of LookupResponse-equivalent items with no paging and no DTO field changes
    And stock and holds are unchanged
    And when an unauthorized caller attempts to list soft-holds the operation fails with UnauthorizedError without mutating stock or holds
    And openapi/openapi.yaml and/or contracts/**/*.ocl plus passing tests/contracts/** make authorized sorted-list success and UnauthorizedError on list checkable
    And prior reserve, release, expire, lookup, concurrent, and list AuthZ/visibility/DTO surfaces remain unbroken

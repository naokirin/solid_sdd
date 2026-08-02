Feature: Calculator single-slot memory
  The calculator exposes a simple single-slot memory that
  starts at zero and supports clear, recall, add-to-memory,
  and subtract-from-memory. No multi-user memory or history.
  Behaviors must be checkable via the HTTP/API and module contracts.

  Scenario: Memory starts at zero
    Given a fresh calculator memory
    When the client recalls memory
    Then the recalled value is zero

  Scenario: Memory clear yields zero on subsequent recall
    Given calculator memory holds a non-zero value
    When the client clears memory
    Then recalling memory yields zero

  Scenario: Add-to-memory increases the single slot by the addend
    Given calculator memory holds a known value
    When the client adds a number to memory
    Then recalling memory yields the previous value plus that number

  Scenario: Subtract-from-memory decreases the single slot by the subtrahend
    Given calculator memory holds a known value
    When the client subtracts a number from memory
    Then recalling memory yields the previous value minus that number

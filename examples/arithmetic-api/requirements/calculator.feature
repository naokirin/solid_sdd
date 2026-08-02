Feature: Arithmetic calculator operations
  Clients use an arithmetic calculator service for the usual
  binary operations and remainder. Invalid uses—especially
  division or remainder by zero—must fail with a named domain
  error, not an opaque language or runtime error. Behaviors
  must be checkable via the HTTP/API and module contracts.

  @R1 @R5 @R6 @SC1 @SC4
  Scenario: Addition returns the sum of its operands
    Given a calculator service available to clients
    When the client adds two numbers
    Then the result equals the mathematical sum of those operands

  @R1 @R5 @R6 @SC1 @SC4
  Scenario: Subtraction returns the difference of its operands
    Given a calculator service available to clients
    When the client subtracts one number from another
    Then the result equals the mathematical difference of those operands

  @R1 @R5 @R6 @SC1 @SC4
  Scenario: Multiplication returns the product of its operands
    Given a calculator service available to clients
    When the client multiplies two numbers
    Then the result equals the mathematical product of those operands

  @R1 @R5 @R6 @SC1 @SC4
  Scenario: Division returns the quotient of its operands
    Given a calculator service available to clients
    And a non-zero divisor
    When the client divides one number by another
    Then the result equals the mathematical quotient of those operands

  @R1 @R5 @R6 @SC1 @SC4
  Scenario: Remainder returns the modulo of its operands
    Given a calculator service available to clients
    And a non-zero divisor
    When the client takes the remainder of one number divided by another
    Then the result equals the mathematical remainder of those operands

  @R2 @R5 @R6 @SC2 @SC4
  Scenario: Division by zero fails with a named domain error
    Given a calculator service available to clients
    When the client divides by zero
    Then the operation fails with a named domain error
    And the failure is not an opaque language or runtime error

  @R2 @R5 @R6 @SC2 @SC4
  Scenario: Remainder by zero fails with a named domain error
    Given a calculator service available to clients
    When the client takes the remainder with a zero divisor
    Then the operation fails with a named domain error
    And the failure is not an opaque language or runtime error

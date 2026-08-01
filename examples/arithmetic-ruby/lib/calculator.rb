# frozen_string_literal: true

# Domain calculator. Contracts: contracts/Calculator.ocl
module Calculator
  class PreconditionError < StandardError; end

  module_function

  def add(a, b)
    a + b
  end

  def sub(a, b)
    a - b
  end

  def mul(a, b)
    a * b
  end

  def div(a, b)
    raise PreconditionError, "divisor must be non-zero" if b.zero?

    a.to_f / b
  end

  # Remainder with dividend sign (Ruby `%` / Integer#% toward-zero quotient style
  # matches JS for Integer operands used in the eval sample).
  def mod(a, b)
    raise PreconditionError, "divisor must be non-zero" if b.zero?

    a % b
  end
end

/**
 * Contract tests derived from contracts/Calculator.ocl
 * (hand-authored baseline for MVP evaluation; sdd.derive.tests should regenerate).
 */
import { describe, expect, it } from "vitest";
import { Calculator, PreconditionError } from "../../src/calculator.js";

describe("OCL Calculator::add", () => {
  it("post ResultIsSum: result = a + b", () => {
    expect(Calculator.add(2, 3)).toBe(5);
    expect(Calculator.add(-1, 1)).toBe(0);
  });
});

describe("OCL Calculator::sub", () => {
  it("post ResultIsDifference: result = a - b", () => {
    expect(Calculator.sub(5, 3)).toBe(2);
  });
});

describe("OCL Calculator::mul", () => {
  it("post ResultIsProduct: result = a * b", () => {
    expect(Calculator.mul(4, 3)).toBe(12);
  });
});

describe("OCL Calculator::div", () => {
  it("pre DivisorIsNonZero: b <> 0 is enforced", () => {
    expect(() => Calculator.div(1, 0)).toThrow(PreconditionError);
  });

  it("post ResultIsQuotient: result = a / b", () => {
    expect(Calculator.div(6, 3)).toBe(2);
  });
});

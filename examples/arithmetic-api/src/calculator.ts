export type Operation = "add" | "sub" | "mul" | "div";

export class PreconditionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PreconditionError";
  }
}

export const Calculator = {
  add(a: number, b: number): number {
    return a + b;
  },

  sub(a: number, b: number): number {
    return a - b;
  },

  mul(a: number, b: number): number {
    return a * b;
  },

  div(a: number, b: number): number {
    if (b === 0) {
      throw new PreconditionError("divisor must be non-zero");
    }
    return a / b;
  },
};

export function calculate(op: Operation, a: number, b: number): number {
  switch (op) {
    case "add":
      return Calculator.add(a, b);
    case "sub":
      return Calculator.sub(a, b);
    case "mul":
      return Calculator.mul(a, b);
    case "div":
      return Calculator.div(a, b);
    default: {
      const _exhaustive: never = op;
      return _exhaustive;
    }
  }
}

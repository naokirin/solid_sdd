export type Operation = "add" | "sub" | "mul" | "div" | "mod" | "pow" | "avg";

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

  mod(a: number, b: number): number {
    if (b === 0) {
      throw new PreconditionError("divisor must be non-zero");
    }
    return a % b;
  },

  pow(a: number, b: number): number {
    return a ** b;
  },

  avg(a: number, b: number): number {
    return (a + b) / 2;
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
    case "mod":
      return Calculator.mod(a, b);
    case "pow":
      return Calculator.pow(a, b);
    case "avg":
      return Calculator.avg(a, b);
    default: {
      const _exhaustive: never = op;
      return _exhaustive;
    }
  }
}

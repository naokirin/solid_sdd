export type Operation = "add" | "sub" | "mul" | "div" | "mod";

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
};

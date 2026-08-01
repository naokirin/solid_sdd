/**
 * Single calculator memory register (initial 0).
 * Contracts: contracts/Memory.ocl
 */
export class Memory {
  #memory = 0;

  clear(): number {
    this.#memory = 0;
    return 0;
  }

  recall(): number {
    return this.#memory;
  }

  add(value: number): number {
    this.#memory += value;
    return this.#memory;
  }

  subtract(value: number): number {
    this.#memory -= value;
    return this.#memory;
  }
}

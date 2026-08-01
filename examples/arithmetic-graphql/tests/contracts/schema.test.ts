/**
 * GraphQL SDL validity + boundary smoke tests (adapter_hint: graphql).
 */
import { describe, expect, it } from "vitest";
import {
  createRootValue,
  executeGraphql,
  loadSchema,
} from "../../src/schema.js";
import { Memory } from "../../src/memory.js";

describe("GraphQL schema", () => {
  it("parses and builds graphql/schema.graphql", () => {
    const schema = loadSchema();
    expect(schema.getQueryType()?.name).toBe("Query");
    expect(schema.getMutationType()?.name).toBe("Mutation");
  });
});

describe("GraphQL calculate boundary", () => {
  it("returns sum for calculate(add)", async () => {
    const result = await executeGraphql(
      loadSchema(),
      createRootValue(),
      "query { calculate(op: add, a: 2, b: 3) }",
    );
    expect(result.errors).toBeUndefined();
    expect(result.data).toEqual({ calculate: 5 });
  });

  it("errors when div by zero (pre DivisorIsNonZero)", async () => {
    const result = await executeGraphql(
      loadSchema(),
      createRootValue(),
      "query { calculate(op: div, a: 1, b: 0) }",
    );
    expect(result.errors?.[0]?.message).toMatch(/non-zero/i);
    expect(result.errors?.[0]?.extensions?.code).toBe("PRECONDITION_FAILED");
  });
});

describe("GraphQL memory boundary", () => {
  it("supports clear / add / recall via GraphQL", async () => {
    const memory = new Memory();
    const root = createRootValue(memory);
    const schema = loadSchema();

    await executeGraphql(schema, root, "mutation { memoryAdd(value: 5) }");
    const recalled = await executeGraphql(schema, root, "query { memory }");
    expect(recalled.data).toEqual({ memory: 5 });

    const cleared = await executeGraphql(
      schema,
      root,
      "mutation { memoryClear }",
    );
    expect(cleared.data).toEqual({ memoryClear: 0 });
  });
});

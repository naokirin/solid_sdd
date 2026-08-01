import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildSchema,
  GraphQLError,
  graphql,
  type GraphQLSchema,
} from "graphql";
import { Calculator, PreconditionError, type Operation } from "./calculator.js";
import { Memory } from "./memory.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

export function loadSchema(): GraphQLSchema {
  const sdl = readFileSync(join(root, "graphql/schema.graphql"), "utf8");
  return buildSchema(sdl);
}

export function createRootValue(memory: Memory = new Memory()) {
  return {
    memory: () => memory.recall(),
    calculate: ({
      op,
      a,
      b,
    }: {
      op: Operation;
      a: number;
      b: number;
    }) => {
      try {
        return Calculator[op](a, b);
      } catch (err) {
        if (err instanceof PreconditionError) {
          throw new GraphQLError(err.message, {
            extensions: { code: "PRECONDITION_FAILED" },
          });
        }
        throw err;
      }
    },
    memoryClear: () => memory.clear(),
    memoryAdd: ({ value }: { value: number }) => memory.add(value),
    memorySubtract: ({ value }: { value: number }) => memory.subtract(value),
  };
}

export async function executeGraphql(
  schema: GraphQLSchema,
  rootValue: ReturnType<typeof createRootValue>,
  source: string,
  variableValues?: Record<string, unknown>,
) {
  return graphql({
    schema,
    source,
    rootValue,
    variableValues,
  });
}

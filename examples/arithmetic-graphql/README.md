# arithmetic-graphql (evaluation sample)

TypeScript sample for arithmetic (+ mod) and calculator memory over a **GraphQL SDL** boundary. Used to evaluate solid_sdd’s `adapter_hint: graphql` + OCL→contract-test path.

OpenAPI variant: [../arithmetic-api](../arithmetic-api).

## Scenario

### Query

| Field | Args | Meaning |
|-------|------|---------|
| `calculate` | `op`, `a`, `b` | Arithmetic + mod |
| `memory` | (none) | MR (current value) |

`op`: `add` \| `sub` \| `mul` \| `div` \| `mod`  
`div` / `mod` with `b === 0` → GraphQL error (precondition).

### Mutation

| Field | Args | Meaning |
|-------|------|---------|
| `memoryClear` | (none) | MC |
| `memoryAdd` | `value` | M+ |
| `memorySubtract` | `value` | M- |

## Contract locations

| Kind | Path |
|------|------|
| GraphQL SDL | `graphql/schema.graphql` |
| OCL | `contracts/Calculator.ocl`, `contracts/Memory.ocl` |
| Contract tests | `tests/contracts/*.test.ts` |

## Setup

```bash
npm install
npm test
npm start
```

Examples (without GraphiQL):

```bash
curl -s localhost:4000/graphql -H 'content-type: application/json' \
  -d '{"query":"query { calculate(op: add, a: 2, b: 3) }"}'

curl -s localhost:4000/graphql -H 'content-type: application/json' \
  -d '{"query":"mutation { memoryAdd(value: 5) }"}'
```

## Using with solid_sdd

1. Expect `solidsdd-judge` to emit `kind=api`, `adapter_hint=graphql`
2. `solidsdd-apply-api` / `solidsdd-apply-dbc` / `solidsdd-derive-tests` / `solidsdd-implement` / `solidsdd-verify`
3. Or `solidsdd-loop`

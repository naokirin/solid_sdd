# arithmetic-api (evaluation sample)

A small TypeScript API for arithmetic (+ mod, pow, avg) and calculator memory (MC / MR / M+ / M-). Used to evaluate solid_sdd’s OpenAPI + OCL→contract-test path.

## Scenario

### Calculate

- `POST /calculate` with `{ "op", "a", "b" }` returns the result
- `op`: `add` | `sub` | `mul` | `div` | `mod` | `pow` | `avg`
- `div` / `mod` with `b === 0` → 400

### Memory

Single Real register (initial value 0).

| Op | HTTP | Body | Meaning |
|----|------|------|---------|
| MC | `POST /memory/clear` | (empty OK) | Set memory to 0 |
| MR | `POST /memory/recall` | (empty OK) | Return current value |
| M+ | `POST /memory/add` | `{ "value": number }` | Add |
| M- | `POST /memory/subtract` | `{ "value": number }` | Subtract |

Response shape: `{ "memory": number }`. Invalid JSON / missing `value` → 400.

## Contract locations

| Kind | Path |
|------|------|
| OpenAPI | `openapi/openapi.yaml` |
| OCL | `contracts/Calculator.ocl`, `contracts/Memory.ocl` |
| Contract tests | `tests/contracts/*.test.ts` |

## Setup

```bash
npm install
npm test
npm start
```

Examples:

```bash
curl -s localhost:3000/calculate -H 'content-type: application/json' \
  -d '{"op":"add","a":2,"b":3}'

curl -s localhost:3000/memory/add -H 'content-type: application/json' \
  -d '{"value":5}'

curl -s localhost:3000/memory/recall -X POST
```

## Using with solid_sdd

1. Manually run `solidsdd-context` → `solidsdd-judge`, etc.
2. Or run `solidsdd-loop` automatically
3. Intentionally break the implementation and confirm `solidsdd-verify` fails

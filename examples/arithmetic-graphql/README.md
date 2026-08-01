# arithmetic-graphql（評価用サンプル）

四則演算（+ mod）と電卓メモリを **GraphQL SDL** 境界で扱う TypeScript サンプル。solid_sdd の `adapter_hint: graphql` + OCL→契約テスト経路を評価する題材。

OpenAPI 版は [../arithmetic-api](../arithmetic-api) を参照。

## シナリオ

### Query

| Field | 引数 | 意味 |
|-------|------|------|
| `calculate` | `op`, `a`, `b` | 四則 + mod |
| `memory` | （なし） | MR（現在値） |

`op`: `add` \| `sub` \| `mul` \| `div` \| `mod`  
`div` / `mod` で `b === 0` のときは GraphQL error（precondition）。

### Mutation

| Field | 引数 | 意味 |
|-------|------|------|
| `memoryClear` | （なし） | MC |
| `memoryAdd` | `value` | M+ |
| `memorySubtract` | `value` | M- |

## 契約の置き場

| 種類 | パス |
|------|------|
| GraphQL SDL | `graphql/schema.graphql` |
| OCL | `contracts/Calculator.ocl`, `contracts/Memory.ocl` |
| 契約テスト | `tests/contracts/*.test.ts` |

## セットアップ

```bash
npm install
npm test
npm start
```

例（GraphiQL 無しの場合）:

```bash
curl -s localhost:4000/graphql -H 'content-type: application/json' \
  -d '{"query":"query { calculate(op: add, a: 2, b: 3) }"}'

curl -s localhost:4000/graphql -H 'content-type: application/json' \
  -d '{"query":"mutation { memoryAdd(value: 5) }"}'
```

## solid_sdd での使い方

1. `solidsdd-judge` で `kind=api`, `adapter_hint=graphql` を期待
2. `solidsdd-apply-api` / `solidsdd-apply-dbc` / `solidsdd-derive-tests` / `solidsdd-implement` / `solidsdd-verify`
3. または `solidsdd-loop`

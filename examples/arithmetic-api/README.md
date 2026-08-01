# arithmetic-api（評価用サンプル）

リクエストで四則演算を行う小さな TypeScript API。solid_sdd の MVP（OpenAPI + OCL→契約テスト）を手で／ループで回すための題材。

## シナリオ

- `POST /calculate` に `{ "op", "a", "b" }` を送り、計算結果を返す
- `op`: `add` | `sub` | `mul` | `div`
- `div` で `b === 0` のときは 400

複雑度を上げる拡張案: 電卓メモリ（M+ / MR / MC 等）。

## 契約の置き場

| 種類 | パス |
|------|------|
| OpenAPI | `openapi/openapi.yaml` |
| OCL | `contracts/Calculator.ocl` |
| 契約テスト（OCL 由来想定） | `tests/contracts/calculator.test.ts` |

## セットアップ

```bash
npm install
npm test
npm start
```

例:

```bash
curl -s localhost:3000/calculate -H 'content-type: application/json' \
  -d '{"op":"add","a":2,"b":3}'
```

## solid_sdd での使い方

1. このディレクトリを対象に `solidsdd-context` → `solidsdd-judge` などを手動実行する
2. または `solidsdd-loop` で自動実行する
3. 意図的に実装を壊して `solidsdd-verify` が fail することを確認する

# arithmetic-api（評価用サンプル）

リクエストで四則演算（+ mod）と電卓メモリ（MC / MR / M+ / M-）を扱う小さな TypeScript API。solid_sdd の OpenAPI + OCL→契約テスト経路を評価する題材。

## シナリオ

### 計算

- `POST /calculate` に `{ "op", "a", "b" }` を送り、計算結果を返す
- `op`: `add` | `sub` | `mul` | `div` | `mod`
- `div` / `mod` で `b === 0` のときは 400

### メモリ

単一の Real レジスタ（初期値 0）。

| 操作 | HTTP | ボディ | 意味 |
|------|------|--------|------|
| MC | `POST /memory/clear` | （空可） | メモリを 0 に |
| MR | `POST /memory/recall` | （空可） | 現在値を返す |
| M+ | `POST /memory/add` | `{ "value": number }` | 加算 |
| M- | `POST /memory/subtract` | `{ "value": number }` | 減算 |

応答は `{ "memory": number }`。不正 JSON / `value` 欠落は 400。

## 契約の置き場

| 種類 | パス |
|------|------|
| OpenAPI | `openapi/openapi.yaml` |
| OCL | `contracts/Calculator.ocl`, `contracts/Memory.ocl` |
| 契約テスト | `tests/contracts/*.test.ts` |

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

curl -s localhost:3000/memory/add -H 'content-type: application/json' \
  -d '{"value":5}'

curl -s localhost:3000/memory/recall -X POST
```

## solid_sdd での使い方

1. `solidsdd-context` → `solidsdd-judge` などを手動実行する
2. または `solidsdd-loop` で自動実行する
3. 意図的に実装を壊して `solidsdd-verify` が fail することを確認する

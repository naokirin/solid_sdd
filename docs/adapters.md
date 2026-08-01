# アダプタ方針

MVP で固定した初期アダプタと、Phase 2 で追加した骨格。詳細は各アダプタ README とスキルを参照。

## API: OpenAPI 3.x（既定）

- **成果物**: `openapi/openapi.yaml`（またはプロジェクト規約上の同等パス）
- **役割**: HTTP 境界のリクエスト／レスポンス・エラー形・互換性の契約
- **検証**: スキーマ妥当性 + 実装が契約に沿うことのチェック（契約テストまたはレスポンス検証）

## API: GraphQL SDL（Phase 2）

- **成果物**: `graphql/schema.graphql`（任意で operations ドキュメント）
- **役割**: GraphQL-first プロジェクト向けの境界契約（OpenAPI の代替）
- **評価サンプル**: [../examples/arithmetic-graphql](../examples/arithmetic-graphql)
- **規約**: [../adapters/graphql/README.md](../adapters/graphql/README.md)

## DbC: UML OCL → 契約テスト（サブエージェント）

言語組み込みの contract 機能には依存しない。

1. **人が／`solidsdd.apply.dbc` が書く第一級成果物**: OCL（事前条件・事後条件・不変条件）
2. **サブエージェントが生成する従属物**: OCL から導出したテストコード
3. **検証**: そのテストの実行結果で契約遵守を判定する

```text
OCL (source of truth)
        │
        ▼
  solidsdd.derive.tests（Subagent 必須）
        │
        ▼
  契約テストコード ──solidsdd.verify (Subagent)──▶ pass / fail
```

オーケストレータからの呼び出し時の隔離ルールは [execution-model.md](execution-model.md) を参照。

OCL をソース・オブ・トゥルースに固定し、テストは再生成可能な従属物として扱う。実装言語はアダプタの「テスト生成先」として差し替える。

### テスト生成先: Ruby / RSpec（Phase 2）

- **成果物**: `spec/contracts/**/*_spec.rb`
- **規約**: [../adapters/ruby-rspec/README.md](../adapters/ruby-rspec/README.md)
- **評価サンプル**: [../examples/arithmetic-ruby](../examples/arithmetic-ruby)（Calculator のみ）

言語ネイティブの contracts gem 等は **必須にしない**（後回し・オプトイン）。

## 評価用スタック

- **既定**: TypeScript（Node.js）+ Vitest — [../examples/arithmetic-api](../examples/arithmetic-api)（OpenAPI）、[../examples/arithmetic-graphql](../examples/arithmetic-graphql)（GraphQL）
- **代替テスト生成先**: Ruby + RSpec — [../examples/arithmetic-ruby](../examples/arithmetic-ruby)
- **将来候補**: フル Rails アプリ（現状は RSpec 生成先で代替経路を証明）

## 評価シナリオ

同ドメイン（四則 + 必要ならメモリ）を API 境界の形だけ差し替えて比較する。

# arithmetic-ruby（評価用サンプル）

四則演算（+ mod）の **Ruby + RSpec** 最小サンプル。OCL を SoT のまま、契約テスト生成先を Vitest から RSpec に差し替えた経路を評価する題材。

HTTP / GraphQL 境界は含まない（API 境界は [../arithmetic-api](../arithmetic-api) / [../arithmetic-graphql](../arithmetic-graphql)）。

言語ネイティブの contracts gem は **使わない**（任意導入は後回し・オプトイン前提）。

## 契約の置き場

| 種類 | パス |
|------|------|
| OCL | `contracts/Calculator.ocl` |
| 契約スペック | `spec/contracts/calculator_spec.rb` |
| 実装 | `lib/calculator.rb` |

## セットアップ

```bash
bundle install
bundle exec rspec
```

## solid_sdd での使い方

1. `solidsdd-apply-dbc` → OCL
2. `solidsdd-derive-tests`（生成先: RSpec / `adapters/ruby-rspec`）
3. `solidsdd-implement` → `lib/`
4. `solidsdd-verify` → `bundle exec rspec`

# ロードマップ

## 評価の前提

最終系のつながり（判断 → 適用 → 実装 → 検証）が無いと、「想定した構成が機能するか」を評価しにくい。そのため MVP では **形式仕様を除く主要経路を一通りつなぐ**。

形式仕様は有効だが導入が重く、適用範囲も狭くなりやすいため **意図的に後回し** する。ただし判断モデル上は `formal` を欠番にせず、`defer` として理由を残せるようにする。

## フェーズ 0: 構想・設計

- [x] 問題意識と目標の明文化（[vision.md](vision.md)）
- [x] ルール／スキル構成の方針（[architecture.md](architecture.md)）
- [x] MVP と後続の切り分け（本ドキュメント）
- [x] 初期アダプタ選定: OpenAPI + OCL→契約テスト（[adapters.md](adapters.md)）
- [x] 評価シナリオ選定: TypeScript 四則演算 API（[../examples/arithmetic-api](../examples/arithmetic-api)）
- [x] スキル入出力スキーマ（`ApplicationPlan` 等）
- [x] スキル定義スケルトン（`skills/`）
- [x] 利用側への導入手順（[install.md](install.md) — `gh skill` 自己完結スキル）
- [x] `skills/*/references/` 同期スクリプト（`scripts/sync-skill-references.sh`）
- [x] Cursor / Claude Code Hook + git pre-commit（ずれ時はエラーと手順表示）
- [ ] GitHub 公開後の `gh skill publish`（release / `agent-skills` topic）

## フェーズ 1: MVP（つながった最小構成）

**状態: 評価完了**（詳細は [mvp-evaluation.md](mvp-evaluation.md)）。配布（`gh skill publish`）は後回し。

**含むもの**

| 要素 | 内容 |
|------|------|
| ルール | 適用方針・成果物配置・検証必須の最小セット |
| `solidsdd.context` | スタック・既存契約の把握 |
| `solidsdd.judge` | API / DbC / 見送り（formal は defer 可） |
| `solidsdd.apply.api` | OpenAPI 3.x |
| `solidsdd.apply.dbc` | UML OCL |
| `solidsdd.derive.tests` | OCL→契約テスト（サブエージェント） |
| `solidsdd.implement` | 契約に沿った実装の更新 |
| `solidsdd.verify` | OpenAPI 検証 + 契約テスト実行 |
| `solidsdd.loop` | 上記の自動オーケストレーション |

**含まないもの（意図的）**

- TLA+ / Alloy / VDM 等の形式仕様の適用・モデル検査
- 多数スタックの網羅的アダプタ
- 高度な信頼度推定や大規模ポリシーエンジン

**MVP の成功基準**

1. [x] サンプル変更に対し、人手でスキルを順に実行して契約が残り、検証が通る／意図的に壊すと検出できる
2. [x] 同じ変更を `solidsdd.loop` だけでも同等の結果に近づく
3. [x] `solidsdd.judge` が「なぜ API / DbC / skip か」を軸に沿って説明できる
4. [x] 形式仕様が望ましいケースでは `defer` と理由が出る（黙って無視しない）

## フェーズ 2: 適用判断とアダプタの強化

**状態: 完了**（詳細は [phase2.md](phase2.md)）。言語ネイティブ契約は意図的に後回し。

- [x] 判断軸の精度向上（破壊的変更、権限・金銭境界、変更頻度、信頼度など）— [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md)
- [x] GraphQL アダプタ + 評価サンプル — [../adapters/graphql/README.md](../adapters/graphql/README.md), [../examples/arithmetic-graphql](../examples/arithmetic-graphql)
- [x] 別言語の契約テスト生成先（Ruby / RSpec）— [../adapters/ruby-rspec/README.md](../adapters/ruby-rspec/README.md), [../examples/arithmetic-ruby](../examples/arithmetic-ruby)
- [x] 人間ゲート条件の整備（低信頼度・破壊的変更等）— [../reference-src/human-gates.md](../reference-src/human-gates.md)
- [x] 検証レポートの標準化とループ復帰条件 — schema + [../reference-src/loop-retry.md](../reference-src/loop-retry.md)
- [x] GraphQL / Ruby サンプルの通し評価 — [phase2-evaluation.md](phase2-evaluation.md)
- [ ] 言語ネイティブ DbC（任意 gem 等）— **後回し**（プロジェクト拒否を前提にオプトイン設計が必要）

## フェーズ 3: 形式仕様の導入

**状態: 完了**（[phase3.md](phase3.md), [phase3-evaluation.md](phase3-evaluation.md), [phase3-gate-dryrun.md](phase3-gate-dryrun.md)）。

- [x] `solidsdd.apply.formal` / `solidsdd.verify.formal` スキル骨格
- [x] `solidsdd.judge` が `formal` を `apply` にしうる条件 — [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md) + [phase3.md](phase3.md)
- [x] 適用範囲が狭い前提の導入ガイド（役割分担）— [phase3.md](phase3.md)
- [x] 既存の API / DbC 経路との役割分担の再確認
- [x] 具体チェッカー統合（**TLC**）と最小評価サンプル — [../tools/tla](../tools/tla), [../examples/memory-formal](../examples/memory-formal)
- [x] Phase 3 通し評価の記録（サンプル TLC）— [phase3-evaluation.md](phase3-evaluation.md)
- [x] ループ上の human_gate → apply-formal ドライラン — [phase3-gate-dryrun.md](phase3-gate-dryrun.md)

## フェーズ 4: 運用・エコシステム

**状態: 文書スライス着手**（[phase4.md](phase4.md)）。公開・実プロフィードバックは未。

- [x] 他 SDD ツールとの共存パターン — [coexistence.md](coexistence.md)
- [x] 導入チェックリスト拡充 — [install.md](install.md)
- [x] プロジェクトテンプレートレイアウト — [project-template.md](project-template.md)
- [x] 評価コーパスに基づくルール調整（Pass 1）— [feedback-tuning.md](feedback-tuning.md)
- [x] 敵対的評価スキル（`solidsdd-critique`）と loop 組み込み — [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md)
- [ ] テンプレートリポジトリの GitHub 公開
- [ ] 外部実プロジェクトからの追加フィードバック

## 直近の次アクション

1. GitHub remote / `gh skill publish`（配布）
2. 外部プロジェクト導入 → [feedback-tuning.md](feedback-tuning.md) に intake、または言語ネイティブ DbC のオプトイン設計

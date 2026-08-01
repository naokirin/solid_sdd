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
- [ ] GitHub 公開後の `gh skill publish`（release / `agent-skills` topic）

## フェーズ 1: MVP（つながった最小構成）

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

**MVP の成功基準（仮説）**

1. サンプル変更に対し、人手でスキルを順に実行して契約が残り、検証が通る／意図的に壊すと検出できる
2. 同じ変更を `solidsdd.loop` だけでも同等の結果に近づく
3. `solidsdd.judge` が「なぜ API / DbC / skip か」を軸に沿って説明できる
4. 形式仕様が望ましいケースでは `defer` と理由が出る（黙って無視しない）

## フェーズ 2: 適用判断とアダプタの強化

- 判断軸の精度向上（破壊的変更、権限・金銭境界、変更頻度など）
- API / DbC アダプタの追加（GraphQL、別言語の contract 等）
- 人間ゲート条件の整備（低信頼度・破壊的変更）
- 検証レポートの標準化とループ復帰条件の明確化

## フェーズ 3: 形式仕様の導入

- `solidsdd.apply.formal` / `solidsdd.verify.formal` の追加
- `solidsdd.judge` が `formal` を `apply` にしうる条件の定義
- 適用範囲が狭い前提での導入ガイド（分散・並行・安全クリティカル等）
- 既存の API / DbC 経路との役割分担の再確認

## フェーズ 4: 運用・エコシステム

- 他 SDD ツールとの共存パターンの文書化
- テンプレートリポジトリ / 導入チェックリスト
- 実プロジェクトでのフィードバックに基づくルールのチューニング

## 直近の次アクション

1. `examples/arithmetic-api` で手動フェーズ実行が通るか確認する
2. `solidsdd.loop` が judge/apply/derive/implement/verify を **Task サブエージェント**で起動する通し確認
3. GitHub remote 設定後に `gh skill publish --dry-run` → `gh skill publish --tag v0.1.0`
4. （任意）電卓メモリ機能をシナリオ拡張として追加する
5. adapters/schemas/docs 変更時に `skills/*/references/` を同期する運用を習慣化する

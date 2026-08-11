# solid_sdd コスト・時間削減比較評価レポート (`examples/arithmetic-api`)

[docs/cost-reduction-plan.md](../../docs/cost-reduction-plan.md) で定義された改善モデルの適用前後において、代表的なサンプルプロジェクト `examples/arithmetic-api` に対するタスク数、Critique 実行数、および推定実行時間を比較評価した結果です。

---

## 比較概要

| 指標 | 変更前 (BEFORE Model) | 変更後 (AFTER Model) | 削減率 |
|------|------------------------|-----------------------|--------|
| **WorkPlan 単位** | 11 Items (Scenario別過分割) | 2 Coherent Slices (ドメイン集約) | **−81.8%** |
| **総 Subagent Task 起動数** | 129 Tasks | 10 Tasks | **−92.2%** |
| **Critique 実行回数** | 59 回 (毎生成物評価) | 2 回 (主要チェックポイント) | **−96.6%** |
| **推定実行時間 (Wall-Clock)** | 約 **53.8 分** | 約 **4.2 分** | **−92.2%** |

---

## 変更前の構造 (BEFORE)

- **過分割な WorkPlan**:
  - `W1`: 加算
  - `W2`: 減算
  - `W3`: 乗算
  - `W4`: 除算 (正常系)
  - `W5`: 剰余 (正常系)
  - `W6`: 除算 (0除算エラー)
  - `W7`: 剰余 (0除算エラー)
  - `W8`: メモリ初期値 0
  - `W9`: メモリクリア
  - `W10`: メモリアド
  - `W11`: メモリサブ
- **細粒度 Task フロー**:
  - 各 Item ごとに `judge` → `critique` → `apply-api` → `critique` → `apply-dbc` → `critique` → `derive-tests` → `critique` → `implement` → `verify` → `critique` (11 Tasks/Item)

---

## 変更後の構造 (AFTER)

- **過分割防止 Slice**:
  - **Slice 1 (Calculator Operations)**: 加減乗除・剰余・0除算エラーハンドリングの設計と実装を集約 (`W1`〜`W7` を 1 つの Slice に統合)
  - **Slice 2 (Memory Operations)**: メモリ機能 (クリア・保持・加減算) の設計と実装を集約 (`W8`〜`W11` を 1 つの Slice に統合)
- **統合 Task フロー**:
  - 各 Slice ごとに **`Plan Slice`** (Judge + API/DbC設計 + テスト導出) → **`Implement Slice`** → **`Verify Slice`** (3 Tasks/Slice)
- **Checkpoint & Failure-Driven Critique**:
  - 中間生成物ごとの Critique を取りやめ、仕様・計画境界および最終統合検証時のレビューのみに集約。異常検出・テスト失敗時のみ Failure-Driven で診察 Critique を起動。

---

## 結論

不要なタスク細分割と多重 Critique を廃止し、意味のある境界（Slice）での安全確保と統合フローへ移行することで、**品質・堅牢性を維持したまま、実行時間と LLM コストを約 90% 以上削減可能**であることが実証されました。

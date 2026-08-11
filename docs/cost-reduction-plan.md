# solid_sdd 実行効率改善計画

## Why — 改善したいこと

`solidsdd-run` は、要件・仕様・実装・検証を分離し、Critique による品質チェックを行うことで安定した実行結果を得られている。

一方で、現在は以下の要因により実行コストが過大になっている。

* Task が細かく分割され、Task 起動回数が多い
* 個々の成果物に対して Critique が繰り返し実行される
* WorkPlan が Scenario 単位に過分割され、関連する変更が複数の Slice / Loop に分散する
* 小さな処理まで独立した Agent Task として実行される

その結果、単純な実装では約10分で完了する処理が、`solidsdd-run` では約1時間かかる場合がある。

**目標は品質・堅牢性を維持しながら、不要な Task / Critique / Loop を削減し、実行時間と LLM コストを大幅に削減すること。**

---

## What — やること

### 1. WorkPlan の過分割を解消する

* `Scenario` と `Slice` の役割を明確に分離する
* Scenario は「検証する振る舞い」
* Slice は「一貫した実装変更の単位」とする
* 同じ実装境界・関連ファイル・ドメインを共有する Scenario は同一 Slice にまとめる
* `vocabulary-only`、`schema-only`、`test-only`、`verify-only` などの小さすぎる WorkPlan item を原則として作らない
* WorkPlan 生成時に「この分割は独立した実装単位として意味があるか」を評価する

### 2. Task の粒度を大きくする

現在の細粒度 Task を、意味のある工程単位に統合する。

基本構造を以下に近づける。

```text
Plan Slice
  ↓
Implement Slice
  ↓
Verify Slice
```

例えば、

```text
judge
API design
DBC design
derive tests
```

を、それぞれ独立 Task とせず、Slice の Planning / Implementation Context の中でまとめて扱う。

単純なファイル参照・検索・機械的処理などは、原則として独立した Agent Task にしない。

### 3. Critique をチェックポイント化する

すべての成果物に Critique を付けるのではなく、重要な品質境界に限定する。

基本的には、

```text
Specification
    ↓ Review
WorkPlan
    ↓ Review
Implementation
    ↓ Verify
Final / Integration Review
```

程度を基本とする。

特に以下の個別 Critique は統合を検討する。

* `critique(judge)`
* `critique(API)`
* `critique(DB)`
* `critique(derived tests)`

個々の成果物ではなく、**Slice / Property / Invariant を横断してレビューする**。

### 4. Critique を failure-driven にする

通常経路では Critique の回数を限定する。

```text
正常系:
Plan → Review → Implement → Verify

失敗時:
Verify → Diagnosis / Critique → Fix → Verify
```

問題が発生した場合のみ追加の Critique / Diagnosis を起動する。

### 5. Task 数・Critique 数を計測可能にする

改善前後を比較できるよう、少なくとも以下を run 単位で記録する。

* Total execution time
* Task launch count
* Critique count
* WorkPlan item / Slice count
* Scenario count
* 各 Task の実行時間
* 各 Slice の実行時間
* Retry / failure count

最適化は「Task 数を減らすこと」自体ではなく、**品質を維持したまま不要な実行を減らすこと**を基準とする。

---

# How — フェーズ計画

## Phase 1: 現状計測

まず現在の `solidsdd-run` を変更せず、実行コストを可視化する。

* Task launch を記録
* Critique を記録
* WorkPlan / Slice 数を記録
* Task ごとの wall-clock time を記録
* 代表的なケースで baseline を取得

**成果物:** 実行コストの baseline

---

## Phase 2: WorkPlan の再設計

WorkPlan の分割ルールを変更する。

* Scenario と Slice を分離
* 関連 Scenario を同一 Slice に統合
* 小さすぎる WorkPlan item を禁止
* `touches` / dependency / implementation boundary を分割判断に利用

**成果物:** 過分割されにくい WorkPlan

---

## Phase 3: Task の統合

`solidsdd-loop` / `solidsdd-run` の Task 構成を見直す。

```text
Before:
judge → critique → API → critique → DB → critique → tests → critique → implement → verify

After:
plan → implement → verify
```

* 細粒度 Task を統合
* 機械的処理を inline 化
* Agent を起動する必要がある判断だけを Task 化

**成果物:** 少ない Task 数で同等の処理を行う実行モデル

---

## Phase 4: Critique の再設計

* 個別 artifact Critique を統合
* Slice / Property / Invariant 単位の Review に変更
* Review checkpoint を限定
* failure 時のみ追加 Critique を実行
* Critique findings を後続処理に引き継ぐ

**成果物:** 品質を維持しつつ Critique 数を削減した実行モデル

---

## Phase 5: 品質・性能の比較

改善前後で同一ケースを実行し、以下を比較する。

```text
                 Before       After
Task count
Critique count
WorkPlan items
Slice count
Execution time
LLM cost
Retry count
Verification result
```

性能だけでなく、

* 要件の取りこぼし
* 仕様違反
* テスト不足
* 実装品質
* Verify failure

なども比較し、**品質低下がないことを確認する**。

---

## 最終的な設計目標

`solid_sdd` を、

> **すべてを細かい Task と Critique に分解することで安全性を作るモデル**

から、

> **Specification / Slice / Verification という意味のある境界で安全性を確保し、Agent Task は必要な箇所だけに使うモデル**

へ進化させる。

最終的には、

```text
Specification
      │
      ▼
  WorkPlan
      │
   Review
      │
      ▼
   Slice 1 ──┐
   Slice 2 ──┼─→ Verify
   Slice 3 ──┘
                 │
                 ▼
          Integration Review
```

という構造を基本形とし、**品質・堅牢性を維持しながら Task 数、Critique 数、WorkPlan の過分割を最小化する。**

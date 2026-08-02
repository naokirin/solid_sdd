# Change report: initial-calculator

- **言語**: 日本語（呼び出し指定）
- **change 状態**: `done`
- **生成元**: `solidsdd-report`（ビューのみ。SoT ではない）

## Status overview

| 章 | 状態 | 主なソース / 不足時のスキル |
|----|------|------------------------------|
| 1. 要求と課題 | 実施済 | `change-context.md` |
| 2. 機能要件 | 実施済 | `change-brief.json` + Features |
| 3. 非機能要件 | 実施済 | `change-context.md` §4 |
| 4. 技術選定 | 実施済 | `change-context.md` §5 |
| 5. 設計 — WorkPlan | 実施済 | `work-plan.json` |
| 5. 設計 — ApplicationPlan | 未実施 | `solidsdd-judge` |
| 5. 設計 — API 契約 | 実施済 | `openapi/openapi.yaml` |
| 5. 設計 — DbC (OCL) | 実施済 | `contracts/*.ocl` |
| 5. 設計 — Formal | 未実施 | `solidsdd-apply-formal`（本 change では適用しない判断） |
| 6. 判断とトレードオフ | 実施済 | `change-context.md` §6 |
| 7. 未解決事項 | 実施済 | Context §7（Brief の open_questions は空） |

## 1. 要求と課題

### 課題（Demand）

クライアントが HTTP 経由で呼べる小型の算術計算機サービスが必要である。四則演算に加え剰余を提供し、除数がゼロのときは明確に失敗すること。単一スロットのメモリ（クリア / リコール / 加算 / 減算）を持ち、初期値はゼロとする。無効な利用に対して、言語・ランタイムの不透明なエラーは許容しない。

### 推進要因・制約

- solid_sdd の評価・サンプル用サービス（契約は機械検証可能であること）
- 製品としての認証、マルチテナントメモリ、履歴、永続化は要求しない
- 既存の TypeScript HTTP サンプル構成があれば再利用を優先する

### 機能意図（要約）

- 二項演算: 加算・減算・乗算・除算・剰余
- ゼロ除算 / ゼロ剰余時は名前付きドメインエラー
- プロセス内の単一メモリスロット（初期 0、clear / recall / add / subtract）
- 詳細と受入は ChangeBrief + Gherkin に委ねる

## 2. 機能要件

### ゴール

クライアントは検証可能なサービス面で加算・減算・乗算・除算・剰余を実行できる。無効な利用は名前付きドメインエラーで失敗する。単一メモリスロットはゼロ開始で、clear / recall / add-to-memory / subtract-from-memory をサポートする。

### スコープ内 (`in_scope`)

- 二項演算: add / subtract / multiply / divide / remainder (mod)
- 無効利用（特にゼロ除算・ゼロ剰余）に対する明確な名前付きドメインエラー（不透明な言語エラーではない）
- ゼロ初期化の単一スロット計算機メモリ
- メモリ操作: clear / recall / add-to-memory / subtract-from-memory
- 計算とメモリをクライアント・テストが行使できる HTTP/API 面
- 同じ振る舞いを検証可能にするモジュール契約

### スコープ外 (`out_of_scope`)

- 認証・認可・セッション・API キー
- マルチユーザー / マルチスロットメモリ
- 操作履歴・undo/redo・式ログ
- 科学演算・ビット演算など add/sub/mul/div/remainder を超える数学
- 永続ストレージ / DB（プロセス再起動をまたぐメモリ）
- UI / フロントエンド / SDK / 第三者連携
- レート制限・クォータ・観測製品機能・マルチテナンシー

### 成功基準

- 有効入力に対し、各演算が正しい数値結果を返す
- ゼロ除算・ゼロ剰余はサービス境界で観測可能な名前付きドメインエラーになる
- メモリはゼロ開始; clear / recall / add / subtract が仕様どおり単一スロットを更新する
- HTTP/API とモジュール契約により、実装内部だけに頼らず上記を検証できる

### 受入シナリオ（Gherkin）

Feature 本文・Scenario 名はソースどおり（英語）。

**`requirements/calculator.feature`**

| Scenario | 要約 |
|----------|------|
| Addition returns the sum of its operands | 二数の和を返す |
| Subtraction returns the difference of its operands | 二数の差を返す |
| Multiplication returns the product of its operands | 二数の積を返す |
| Division returns the quotient of its operands | 非ゼロ除数で商を返す |
| Remainder returns the modulo of its operands | 非ゼロ除数で剰余を返す |
| Division by zero fails with a named domain error | ゼロ除算は名前付きドメインエラー |
| Remainder by zero fails with a named domain error | ゼロ剰余は名前付きドメインエラー |

**`requirements/memory.feature`**

| Scenario | 要約 |
|----------|------|
| Memory starts at zero | 新規メモリの recall は 0 |
| Memory clear yields zero on subsequent recall | clear 後の recall は 0 |
| Add-to-memory increases the single slot by the addend | M+ でスロット増加 |
| Subtract-from-memory decreases the single slot by the subtrahend | M- でスロット減少 |

## 3. 非機能要件

| 品質 | 要件 | 根拠 | 検証 / 延期 |
|------|------|------|-------------|
| 信頼性 / エラー処理 | 無効な算術（特に / と rem by 0）は**名前付きドメインエラー**で失敗し、不透明な言語エラーにしない | 呼び出し側と契約テストに安定した信号が必要 | 契約テスト + API エラー経路; OCL `pre` |
| セキュリティ | 本 change では N/A | 認証は明示的にスコープ外 | 延期 / スコープ外 |
| 性能 | 特別なレイテンシ・スループット目標なし | サンプル負荷 | N/A |
| 運用性 | HTTP/API とモジュール契約で振る舞いを検証可能（不透明な内部に依存しない） | solid_sdd 評価パス | OpenAPI + OCL 由来テスト |
| 互換性 | 加算的なサンプル API; 既存外部クライアントの明示なし | グリーンフィールド | OpenAPI が面を文書化 |
| 保守性 | UML OCL を DbC SoT とし、テストは導出 | solid_sdd アダプタ方針に合致 | OCL + derive-tests |

## 4. 技術選定

| 決定事項 | 選択 | 検討した代替 | 根拠 | 出典 |
|----------|------|--------------|------|------|
| 言語 / ランタイム | TypeScript / Node | Ruby のみ、Go など | 既存 arithmetic-api 評価スタック; Vitest 契約 | `repo_existing` |
| API スタイル | HTTP + OpenAPI 3.x | GraphQL SDL, Protobuf | サンプルが OpenAPI 志向; HTTP 境界の lint が容易 | `repo_existing` + `agent_default` |
| 永続化 | なし（プロセス内メモリ） | DB バックのメモリ | スコープ外; 単一スロットで十分 | `user`（スコープ） |
| モジュール契約 | UML OCL → Vitest 契約テスト | 言語ネイティブ契約 gem 等 | solid_sdd 既定 DbC 経路 | `agent_default` |
| 形式手法 | 本 change では適用しない | メモリ並行向け TLA+ | 単スレッド前提; concurrency_safety は要求にない | `agent_default` |

## 5. 設計

### WorkPlan — 実施済

全体受入の要約: 加減乗除・剰余、ゼロ除数の名前付きエラー、単一スロットメモリ（開始ゼロ / clear / add / subtract）、および検証可能な HTTP/API・モジュール面。認証・マルチユーザーメモリ・履歴は不要。

| ID | 意図（要約） | Scenario | Feature | 状態 | 依存 |
|----|--------------|----------|---------|------|------|
| W1 | 加算 | Addition returns the sum of its operands | calculator.feature | ready | — |
| W2 | 減算 | Subtraction returns the difference of its operands | calculator.feature | ready | — |
| W3 | 乗算 | Multiplication returns the product of its operands | calculator.feature | ready | — |
| W4 | 除算（非ゼロ） | Division returns the quotient of its operands | calculator.feature | ready | — |
| W5 | 剰余（非ゼロ） | Remainder returns the modulo of its operands | calculator.feature | ready | — |
| W6 | ゼロ除算エラー | Division by zero fails with a named domain error | calculator.feature | ready | — |
| W7 | ゼロ剰余エラー | Remainder by zero fails with a named domain error | calculator.feature | ready | — |
| W8 | メモリ初期ゼロ | Memory starts at zero | memory.feature | ready | — |
| W9 | メモリ clear | Memory clear yields zero on subsequent recall | memory.feature | ready | — |
| W10 | メモリ加算 | Add-to-memory increases the single slot by the addend | memory.feature | ready | — |
| W11 | メモリ減算 | Subtract-from-memory decreases the single slot by the subtrahend | memory.feature | ready | — |

詳細: [work-plan.json](work-plan.json)

### ApplicationPlan — 未実施

`.solidsdd/changes/initial-calculator/` および関連パスに ApplicationPlan JSON が見つからない。契約密度・適用判断の記録は `solidsdd-judge` の成果物が必要。

（リポジトリ上には OpenAPI / OCL が存在するが、本レポートでは ApplicationPlan 自体は未実施として扱う。）

### API 契約 — 実施済

自然言語要約:

- OpenAPI 3.0.3、タイトル Arithmetic API（v0.2.0）
- `POST /calculate`（`operationId: calculate`）: 二項演算。成功 200、前提違反等は 400 + ErrorResponse
- メモリ: `POST /memory/clear` / `recall` / `add` / `subtract`（MC / MR / M+ / M-）
- 演算 enum: `add`, `sub`, `mul`, `div`, `mod`

Raw 本文は Markdown では埋め込まない。ソース: [openapi/openapi.yaml](../../../openapi/openapi.yaml)

### DbC (OCL) — 実施済

自然言語要約:

- **Calculator**（[Calculator.ocl](../../../contracts/Calculator.ocl)）
  - `add` — post: 和（`a + b`）
  - `sub` — post: 差（`a - b`）
  - `mul` — post: 積（`a * b`）
  - `div` — pre: `b <> 0` / post: 商（`a / b`）
  - `mod` — pre: `b <> 0` / post: 剰余（JS `%` 相当。符号は被除数側、`truncatedTowardZero`）
- **Memory**（[Memory.ocl](../../../contracts/Memory.ocl)）
  - 属性: `memory: Real`
  - `clear` — メモリを `0` にし、戻り値も `0`
  - `recall` — 現在の `memory` を返す
  - `add` — `memory@pre + value` に更新し、更新後の値を返す
  - `subtract` — `memory@pre - value` に更新し、更新後の値を返す

### Formal — 未実施

`formal/` なし。技術選定でも本 change では形式手法を適用しない。

## 6. 判断とトレードオフ

- 「検証可能な HTTP + モジュール契約」を成功条件とするが、密度・アダプタ適用は `solidsdd-judge` に委ねる（ここでは OpenAPI フィールド一覧を過度に固定しない）
- 生の `ZeroDivisionError` より**名前付きドメインエラー**を優先し、API とテストで失敗語彙を共有する
- 認証・マルチユーザーメモリ・履歴・永続化を外し、サンプルの境界を保つ

## 7. 未解決事項

Change Context §7 より:

- 負数に対する剰余 / 除算の符号規約: 当面 OCL / 実装規約（例: JS `%`）に委ね、必要なら後続 change で締める
- 正確な HTTP パスとエラー JSON 形状: OpenAPI apply に延期（現 OpenAPI に実装済みの面あり）

ChangeBrief の `open_questions`: （空）

## 8. Source artifacts

- `.solidsdd/active-change.json`
- `.solidsdd/changes/initial-calculator/status.json`
- `.solidsdd/changes/initial-calculator/change-context.md`
- `.solidsdd/changes/initial-calculator/change-context-gate.json`
- `.solidsdd/changes/initial-calculator/change-brief.json`
- `.solidsdd/changes/initial-calculator/work-plan.json`
- `requirements/calculator.feature`
- `requirements/memory.feature`
- `openapi/openapi.yaml`
- `contracts/Calculator.ocl`
- `contracts/Memory.ocl`
- ApplicationPlan: （なし → 未実施）
- Formal: （なし → 未実施）

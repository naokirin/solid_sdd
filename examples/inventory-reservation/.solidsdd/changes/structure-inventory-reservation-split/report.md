# Change report: structure-inventory-reservation-split

- **言語**: 日本語（依頼文の言語から解決 — working_language 未設定のため）
- **change 状態**: `active`（設計のみ。実装は未着手 — 後述）
- **対象 change_id**: 明示指定（`active-change.json` は別 change `add-list-sort-expires` を指しているため上書き）
- **生成元**: `solidsdd-report`（ビューのみ。SoT ではない）

## Status overview

| 章 | 状態 | 主なソース / 不足時のスキル |
|----|------|------------------------------|
| 1. 要求と課題 | 未実施 | `solidsdd-intake`（`change-context.md` 未作成） |
| 2. 機能要件 | 実施済（部分） | `change-brief.json`（Feature/Scenario 連携は未実施 — `solidsdd-decompose`） |
| 3. 非機能要件 | 実施済 | `nfr.json` |
| 4. 技術選定 | 未実施 | `solidsdd-intake`（`change-context.md` §5 未作成） |
| 5. 設計 — WorkPlan | 未実施 | `solidsdd-decompose` |
| 5. 設計 — ArchitecturePlan | 実施済 | `architecture-plan.json`（`status: changed`） |
| 5. 設計 — ApplicationPlan | 未実施 | `solidsdd-judge` |
| 5. 設計 — API 契約 | 実施済（既存・本 change では未変更） | `openapi/openapi.yaml`（先行 change から継続） |
| 5. 設計 — DbC (OCL) | 実施済（既存・本 change では未変更） | `contracts/Reservation.ocl`（先行 change から継続） |
| 5. 設計 — Formal | 未実施 | `solidsdd-apply-formal`（本 change では適用しない） |
| 6. 判断とトレードオフ | 実施済（部分） | ArchitecturePlan rationale + critique |
| 7. 未解決事項 | 実施済 | Brief `open_questions` は空;Context 未作成のため章自体は該当なし |

## 1. 要求と課題

`change-context.md` が未作成のため、本章は未実施です（`solidsdd-intake` が生成する章）。

## 2. 機能要件

### ゴール

在庫所有権（stock ownership）を、hold の TTL・authZ といった予約特有の関心事から構造的に独立させ、将来（例: マルチ倉庫対応）在庫だけを再利用できるようにする。予約ドメインがこれ以上複雑化する前に、この構造を明示しておく。

### スコープ内 (`in_scope`)

- **R1** — inventory と reservation を、方向付き依存（reservation → inventory）と禁止された逆依存（inventory → reservation）を持つ別モジュールとして定義する

### スコープ外 (`out_of_scope`)

- **X1** — `src/` での分割実装。本 change は構造設計の成果物にとどまり、サンプルの実装は単一ファイル `reservation.ts` のままとする
- **X2** — 振る舞いの変更、新規エンドポイント、新規 OCL/TLA+ 契約

### 成功基準

- **SC1** — ArchitecturePlan がモジュールの責務、`reservation → inventory` 依存、`inventory → reservation` の `forbid_dependency` 制約を記録し、`solidsdd-lint` / `critique(architecture_plan)` を通過すること

### 受入シナリオ（Gherkin）

本 change に紐づく Feature / Scenario はありません（`solidsdd-decompose` 未実施のため未実施）。

## 3. 非機能要件

| ID | 品質 | 状態 | 要件 | 根拠 | 閾値 / 検証 |
|----|------|------|------|------|-------------|
| NFR1 | 信頼性 | out_of_scope | N/A | 設計のみで実行時の振る舞い変更なし | — |
| NFR2 | セキュリティ | out_of_scope | N/A | 新しい境界・authZ 面は追加しない | — |
| NFR3 | 性能 | out_of_scope | N/A | 実装変更がなく計測対象がない | — |
| NFR4 | 運用性 | out_of_scope | N/A | 設計のみの change でデプロイ物の変更なし | — |
| NFR5 | 互換性 | out_of_scope | N/A | API・契約の変更なし（X2） | — |
| NFR6 | 保守性 | **in_scope** | 在庫所有権（inventory）は hold/TTL/authZ の関心事（reservation）から構造的に独立し続けること。将来の利用者（例: マルチ倉庫）が inventory だけに依存できるようにする | 今回の分割の目的そのもの（ゴール参照） | 閾値: `inventory → reservation` の `forbid_dependency` 違反ゼロ / 検証: `scripts/solidsdd-lint.sh` の構造チェック（依存先存在・禁止依存・循環） |

## 4. 技術選定

`change-context.md` §5 が未作成のため、本章は未実施です（`solidsdd-intake`）。

## 5. 設計

### WorkPlan — 未実施

本 change には `work-plan.json` がありません（`solidsdd-decompose` 未実施）。構造設計（ArchitecturePlan）は WorkPlan 分解前の設計段階で止まっています。

### ArchitecturePlan — 実施済

`status: changed`。単一ファイル `src/reservation.ts` が現在まとめて持っている「在庫」と「hold ライフサイクル」の2つの関心事を、モジュールとして分離する設計です。

**モジュール**

| id | 責務 | owns | public |
|----|------|------|--------|
| `inventory` | SKU ごとの在庫を所有し、在庫の読み取り・増減操作を公開する | `Stock` | `InventoryService` |
| `reservation` | hold のライフサイクル（reserve / release / expire / lookup）と TTL・authZ の適用を所有する | `Hold` | `ReservationService` |

**依存関係**

| from | to | 理由 | kind |
|------|----|------|------|
| `reservation` | `inventory` | hold の予約・解放時に在庫の読み取り・増減が必要 | `runtime` |

**構造上の制約**

| type | from | to | 理由 |
|------|------|----|------|
| `forbid_dependency` | `inventory` | `reservation` | 在庫所有権は hold/TTL/authZ の関心事から独立させ、（例: マルチ倉庫のような）将来の利用者が reservation ロジックを引き連れずに inventory だけを再利用できるようにする |

**Critique (`architecture_plan`) — pass**

責務・境界・所有権・依存方向のいずれにも checkability 上の問題なし。`minor` 指摘が1件: `ReservationService` は単一ファサードだが、standard density では許容範囲（将来、読み取り専用の lookup ポートを分離してもよい）。

詳細: [architecture-plan.json](architecture-plan.json) / [critique-architecture-plan.json](critique-architecture-plan.json)

### ApplicationPlan — 未実施

`.solidsdd/changes/structure-inventory-reservation-split/` 配下に ApplicationPlan JSON は見つかりません（`solidsdd-judge` 未実施）。本 change は構造設計のみで、契約（API / DbC / formal）の適用判断は行っていません。

### API 契約 — 実施済（既存・本 change では未変更）

自然言語要約（先行 change 由来。本 change はこれを変更していません）:

- OpenAPI 3.x、タイトル *Inventory Reservation API*（v0.1.0）
- `GET /reservations`（`listReservations`）、`POST /reservations`（`reserve`）、`GET /reservations/{holdId}`（`getReservation`）、`POST /reservations/{holdId}/release`（`release`）、`POST /reservations/{holdId}/expire`（`expire`）

現在の API は `reservation` 境界のみを表しており、本 change が提案する `inventory` / `reservation` の分割はまだ反映されていません（設計のみのため）。

ソース: [openapi/openapi.yaml](../../../openapi/openapi.yaml)

### DbC (OCL) — 実施済（既存・本 change では未変更）

自然言語要約（先行 change 由来。本 change はこれを変更していません）:

- **Reservation**（[Reservation.ocl](../../../contracts/Reservation.ocl)）
  - `reserve` — pre: 認可済み principal / 数量 > 0 / 十分な在庫。post: TTL 付き hold 生成、在庫減少、在庫不足時は `InsufficientStockError`、未認可時は `UnauthorizedError`
  - `release` — pre: 認可済み principal / hold が存在。post: 在庫復元、hold 削除、未認可時は `UnauthorizedError`
  - `expire` — pre: hold が存在 / TTL 超過。post: 在庫復元、hold 削除

現状の OCL コンテキストは `Reservation` 単一のままで、`inventory` / `reservation` への分割はまだ反映されていません。

### Formal — 未実施

`formal/` に本 change に関連する仕様はありません。技術選定自体が未実施（Context 未作成）のため、形式手法の適用判断もしていません。

## 6. 判断とトレードオフ

- 在庫（`inventory`）と hold ライフサイクル（`reservation`）を分離し、依存方向を `reservation → inventory` に固定。逆方向は `forbid_dependency` で明示的に禁止し、在庫を将来（マルチ倉庫等）再利用可能に保つことを狙いとする
- 本 change は設計のみに留め、`src/` の実装分割は意図的にスコープ外（X1）とした — サンプルの実装は単一ファイルのまま
- Critique の `minor` 指摘（`ReservationService` を単一ファサードとする点）は standard density では許容と判断し、修正は求めていない

## 7. 未解決事項

- ChangeBrief の `open_questions`: （空）
- `change-context.md` が未作成のため、Context §7 由来の未解決事項は該当なし

## 8. Source artifacts

- `.solidsdd/changes/structure-inventory-reservation-split/status.json`
- `.solidsdd/changes/structure-inventory-reservation-split/change-brief.json`
- `.solidsdd/changes/structure-inventory-reservation-split/nfr.json`
- `.solidsdd/changes/structure-inventory-reservation-split/architecture-plan.json`
- `.solidsdd/changes/structure-inventory-reservation-split/critique-architecture-plan.json`
- `openapi/openapi.yaml`（先行 change から継続、本 change では未変更）
- `contracts/Reservation.ocl`（先行 change から継続、本 change では未変更）
- change-context.md: （なし → 未実施）
- work-plan.json: （なし → 未実施）
- ApplicationPlan: （なし → 未実施）
- Formal: （なし → 未実施）

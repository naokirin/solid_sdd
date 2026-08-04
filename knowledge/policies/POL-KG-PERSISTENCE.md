---
id: POL-KG-PERSISTENCE
type: policy
title: 知識層には更新が稀で非自明な普遍的知見のみを載せる
status: active
maturity: canonical
scope: org.solid_sdd
aliases:
  - knowledge permanence
  - ナレッジ永続化方針
tags: [kg]
owner: solid_sdd
confidence: high
verified_at: "2026-08-04"
supersedes: []
superseded_by: []
rationale:
  - KG-DEC-002-REQ-AUTHORITY
---

solid_sdd は change 単位の要求・契約を living documentation として保守しない。
一方、用語定義・横断ポリシー・ADR・教訓など、**機能廃止後も残すべき普遍性の高い知見**は `knowledge/` に独立ノードとして保持する。

## 適用範囲

- concept / policy / invariant / pattern / decision / lesson

## 載せ方の判定（必須）

候補は次を**すべて**満たすこと:

1. **普遍性** — 複数 change / 後続エージェントが従うべき横断規範・用語・ADR・教訓である
2. **非自明性** — ドメインに詳しい担当者が「当然」と言い切れない、または後続が黙って誤りやすい**選択・例外・境界**がある
3. **低更新頻度** — 毎回の change で書き換えない前提で保守できる

自明な命題は情報価値が低く、ノード数が増えるほど陳腐化防止や整合確認の**保守コストだけが増える**。普遍的でも自明なら載せない（Brief / Gherkin / 契約の SoT に任せる）。

### Means と tech selection

- **Means（判断基準）** — 「サーバを権威とする」「opaque principal AuthZ のみ」など、迷ったときに戻る規範。Change Context §6 や ADR 由来で、`knowledge/` の主候補。
- **Tech selection（今回のスタック選択）** — 言語・API スタイル・永続化など Change Context §5。**一回限り／リポジトリ継承の選択は Context に閉じ**、原則 harvest しない。

### 成熟度（`maturity`）

lifecycle の `status`（`draft` / `active` / …）とは別。認識論的確度:

| maturity | 意味 |
|----------|------|
| `hypothesized` | 推定のみ。consult では下位。Brief `assumptions` 扱い可 |
| `confirmed` | 対話・レビューで確認済み（欠落時のデフォルト） |
| `canonical` | 下流を縛る基準。human-gated harvest apply の既定 |

### 非自明性の目安

| 寄せやすい | 載せない（自明・tautology） |
|------------|------------------------------|
| 繰り返されやすい境界選択（例: opaque principal AuthZ のみ／フル IAM 除外） | ドメイン公理の言い換えだけ（例: 「在庫は負にならない」単体） |
| 後続が分岐しがちなエラー／検証チャネルの固定 | 契約や Feature が既に機械検査しているだけの再掲 |
| 例外が稀な推奨慣行で、代替を黙って採るとドリフトする ADR／pattern | 「正しく実装せよ」級の一般論 |

非自明性は `knowledge-harvest.json` の各候補 `rationale` に明示する（普遍性・再利用に加え、何が自明でないかを書く）。

## 載せないもの

- 個別 change の in/out of scope や一時的な受入シナリオ全文
- 契約（OpenAPI / OCL）の本文（既存 SoT に任せる）
- 自明・tautological な命題（上記「非自明性」を満たさないもの）

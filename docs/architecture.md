# アーキテクチャ方針

## 全体像

solid_sdd は、次の二層で動くことを想定する。

1. **ルール（持続的制約）**  
   いつ・何を・どの品質で仕様化するかを、プロジェクトに常駐する指針として持つ。
2. **スキル（呼び出し可能なフェーズ単位の手続き）**  
   ユーザーまたはオーケストレータが、任意の手順で実行できるコマンド相当。

Kiro 等の SDD ツールと同様、**人手の段階実行**と **AI による自動実行**が同じスキル集合を共有する。

```text
┌─────────────────────────────────────────┐
│              Rules（常駐制約）            │
│  適用方針 / 成果物配置 / 検証必須条件 など │
└──────────────────┬──────────────────────┘
                   │ 制約・文脈
┌──────────────────▼──────────────────────┐
│   Orchestrator = solidsdd.loop / 親エージェント │
│   context は親。judge 以降は Subagent 必須 │
└──────────────────┬──────────────────────┘
                   │ Task（明示的 Subagent）
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   judge / apply.*   derive.tests   implement / verify
```

実行ポリシーの詳細は [execution-model.md](execution-model.md)。

## 設計原則

1. **スキルは単体で完結し、組み合わせ可能**  
   「適用判断だけ」「API 契約の更新だけ」も可能。自動ループはそれらの合成。
2. **判断と具体化を分離**  
   「何を載せるべきか」と「OpenAPI / 言語契約としてどう書くか」を混ぜない。
3. **検証をループの必須ノードにする**  
   生成して終わりにしない。契約と実装のずれを検出して戻す。
4. **スタックはアダプタで吸収**  
   コアは契約の種類と検証結果のモデルを持ち、具体技術はプラグイン的に扱う。
5. **人が介在する点を明示する**  
   デフォルトは自動。承認・例外・方針変更だけを人間ゲートにする（ゲートの有無はルールで設定可能）。
6. **関心の隔離は Subagent で強制する**  
   適用判断・適用・テスト導出・実装・検証を同一エージェント文脈で連続実行しない（判断の偏り・自己採点・契約の弱体化を防ぐ）。

## コアスキル（MVP 想定）

| スキル | 責務 | 実行ポリシー | 主な入出力 |
|--------|------|--------------|------------|
| `solidsdd.loop` | オーケストレーション | orchestrator のみ | ループログ・最終状態 |
| `solidsdd.context` | スタック・既存契約の把握 | orchestrator | コンテキスト要約 |
| `solidsdd.judge` | 適用判断 | **subagent 必須** | ApplicationPlan |
| `solidsdd.apply.api` | OpenAPI 追加・更新 | **subagent 必須** | OpenAPI 差分 |
| `solidsdd.apply.dbc` | OCL 追加・更新 | **subagent 必須** | `.ocl` 差分 |
| `solidsdd.derive.tests` | OCL→契約テスト | **subagent 必須** | テスト差分 |
| `solidsdd.implement` | 契約に従う実装 | **subagent 必須** | コード差分 |
| `solidsdd.verify` | OpenAPI + 契約テスト検証 | **subagent 必須** | VerificationReport |

形式仕様向け（例: `solidsdd.apply.formal` / `solidsdd.verify.formal`）は [roadmap.md](roadmap.md) の後続フェーズで追加する。MVP の `solidsdd.judge` は「形式仕様が望ましいが未対応」と明示して見送り可能にする。

## 適用判断（`solidsdd.judge`）の出力モデル

共有スキーマ: [../schemas/application-plan.schema.json](../schemas/application-plan.schema.json)

```text
ApplicationPlan:
  human_gate? / confidence?          … Phase 2（任意）
  targets[]:
    kind: api | dbc | formal | natural_only
    location: 境界やモジュールの識別子
    density: thin | standard | strict
    rationale: 判断理由（軸への参照）
    adapter_hint: openapi | graphql | ocl | ...
    status: apply | defer | skip
    signals? / breaking? / confidence? / human_gate?  … Phase 2
```

`formal` は MVP では主に `defer`（理由付き）となる。

判断に使う軸は [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md)（Phase 2）と [vision.md](vision.md)。ルールでプロジェクト固有の閾値を上書きできる。人間ゲートとループ復帰は [phase2.md](phase2.md)。

## アダプタ層

MVP の初期アダプタは次で固定する（詳細は [adapters.md](adapters.md)）。Phase 2 で GraphQL 骨格を追加。

```text
Contract Kind          Adapter
─────────────          ─────────────────────────────
API boundary    →      OpenAPI 3.x（既定） / GraphQL SDL
Module DbC      →      UML OCL → 契約テスト（Vitest 既定 / RSpec 可）
Formal          →      TLA+ / Alloy 等（Phase 3 設計。judge は条件付き apply 可、早期はゲート必須）
```

OCL 経路のポイント: OCL がソース・オブ・トゥルース。テストコードはサブエージェントが OCL から生成する従属物であり、`solidsdd.verify` はそのテスト実行で契約遵守を見る。言語ネイティブ契約は任意・後回し。形式仕様の役割分担は [phase3.md](phase3.md)。

アダプタの責務:

- 成果物の配置規約（パス、命名）
- 生成・更新のテンプレート
- 検証の呼び出し方（OpenAPI 検証、OCL 由来テストの実行等）
- スタック未検出時のフォールバック（提案のみ / 人間ゲート）

## ルール層で持つもの（例）

- デフォルトの適用密度（探索的領域は thin、金銭・権限境界は strict など）
- 検証なしのマージ/完了を禁止するか
- API 破壊的変更の扱い（警告 / ブロック / 承認必須）
- オーケストレータの最大ループ回数・失敗時のエスカレーション
- 人間ゲートの条件（初回導入、破壊的変更、判断信頼度が低い場合など）

## 手動実行と自動実行

| モード | 振る舞い |
|--------|----------|
| 手動 | ユーザーがスキルを単体指定。その会話エージェントが実行してよい。連続チェイン時は subagent 必須スキルを Task で切ることを推奨 |
| 自動 | `solidsdd.loop`（親）が context を行い、judge・apply・derive・implement・verify は **必ず Subagent**。失敗時も Subagent で再実行 |

両方で **同じルール・同じスキル・同じ成果物配置** を使う。自動だけが特別な裏道を持たない。

## リポジトリ配置

```text
solid_sdd/
  README.md
  docs/                 # 構想・設計
  schemas/              # ApplicationPlan 等の共有スキーマ
  adapters/             # OpenAPI / GraphQL / OCL / ruby-rspec / formal アダプタ規約
  skills/               # Cursor Skill 形式のスキル定義
  rules/                # 常駐ルール（順次追加）
  examples/             # 評価用サンプル
```

スキルは Cursor / Agent Skills（`SKILL.md`）形式で、**`references/` 込みの自己完結パッケージ**として定義する。利用側は `gh skill install` が主経路（[install.md](install.md)）。

## 未決事項

- 検証の「どこまでを必須にするか」のデフォルト閾値
- OCL 方言・ツールチェーン（構文チェックをどこまで機械化するか）
- 言語ネイティブ DbC のオプトイン設計（gem 拒否を前提）
- 他 SDD ツール（Kiro 等）との共存・置き換えの境界

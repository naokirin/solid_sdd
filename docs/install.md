# プロジェクトへの導入手順

solid_sdd のスキルは **自己完結** です。アダプタ要約・スキーマ・実行モデルは各スキルの `references/` に同梱しており、`gh skill` でインストールするだけで MVP を回せます。

## 前提

- GitHub CLI **v2.90.0 以降**（`gh skill` コマンド）
- [Cursor](https://cursor.com/) など Agent Skills 対応ホスト（`--agent cursor` 等）
- MVP: **OpenAPI 3.x + OCL → 契約テスト**（TypeScript / Vitest を評価サンプルとする）

`gh skill` は preview 機能です。仕様変更の可能性があります。

## 推奨: `gh skill` でインストール

リポジトリが GitHub に公開され、`gh skill publish` 済み（または default branch から install 可能）である前提:

```bash
# 利用側プロジェクトのルートで
gh skill install <OWNER>/solid_sdd --all --agent cursor --scope project
```

個別インストール例:

```bash
gh skill install <OWNER>/solid_sdd solidsdd-loop --agent cursor --scope project
gh skill preview <OWNER>/solid_sdd solidsdd-loop   # 導入前の確認
```

ピン留め:

```bash
gh skill install <OWNER>/solid_sdd --all --agent cursor --scope project --pin v0.1.0
```

### インストール先

Cursor の project scope では、多くの場合 **`.agents/skills/solidsdd-*`** に配置されます（Copilot 等と共有ディレクトリ）。従来の `.cursor/skills/` とは異なることがあります。実際のパスは `gh skill list` で確認してください。

### プロジェクトルール（任意だが推奨）

`gh skill` は Project Rule を自動では入れません。初回のみ:

```bash
# インストール後のパスは環境により異なる
cp .agents/skills/solidsdd-loop/references/project-rule.mdc .cursor/rules/solidsdd.mdc
```

パスが違う場合は `gh skill list` やファイル検索で `solidsdd-loop/references/project-rule.mdc` を見つけてコピーしてください。

## ローカル検証（未公開リポジトリ）

```bash
gh skill install --from-local /path/to/solid_sdd --all --agent cursor --scope project
gh skill publish --dry-run /path/to/solid_sdd   # 配布前バリデーション
```

## 利用側に用意する契約レイアウト

スキルが参照するデフォルト（ルールで上書き可）:

```text
your-project/
  openapi/
    openapi.yaml
  contracts/
    *.ocl
  tests/
    contracts/
      *.test.ts
  .agents/skills/solidsdd-*/   # gh skill が配置
  .cursor/rules/solidsdd.mdc   # 上記からコピー（推奨）
```

未作成でも導入可能です。`solidsdd-context` → `solidsdd-judge`（または `solidsdd-loop` / `solidsdd-run`）で不足を検出・生成する想定です。

## 動作確認

1. `gh skill list` で `solidsdd-*` が出ること
2. Agent に「`solidsdd-context` を実行して」「`solidsdd-loop` を回して」（1 slice）、または「`solidsdd-run` を回して」（複数受け入れ条件）と依頼
3. スキルが `references/` 配下を読んでいること
4. （任意）本リポジトリの [examples/arithmetic-api](../examples/arithmetic-api) で通し確認

自動実行時:

- **1 つの検証可能な受け入れ条件**が既に分かっている → `solidsdd-loop`
- **要件が複数条件・大きめ** → `solidsdd-run`（decompose → 各 item で loop → 統合 verify）

親が context 以外の subagent 必須スキルを Task で起動すること（各スキルの `references/execution-model.md`）。

## メンテナー向け: 配布準備

スキル本体の変更後:

```bash
gh skill publish --dry-run
# remote・認証済みなら（このドキュメントの範囲外）:
# gh skill publish --tag v0.1.0
```

- リポジトリ topic に `agent-skills` が付く（publish 時に案内）
- 各 `SKILL.md` に `license: MIT` を含め済み
- `adapters/`・`schemas/`・`docs/`・`rules/`・`reference-src/` は編集用ソース。**配布物の正は `skills/*/references/`**
- ソースを直したら必ず同期する:

```bash
scripts/sync-skill-references.sh
scripts/sync-skill-references.sh --check   # ずれ検出
```

AI エージェント経由の編集では次が自動で sync します。

- Cursor: `.cursor/hooks.json`（`afterFileEdit`）
- Claude Code: `.claude/settings.json`（`PostToolUse` / `Edit|Write|MultiEdit`）

コミット時は `scripts/git-hooks/pre-commit` が `--check` し、ずれていれば失敗して実行コマンドを示します。初回のみ:

```bash
scripts/install-git-hooks.sh
```

## 更新

```bash
gh skill update --all
# または
gh skill update solidsdd-loop
```

`project-rule.mdc` をローカル改変している場合は、上書きコピーに注意してください。

## 導入チェックリスト

### 必須（MVP: OpenAPI + OCL）

- [ ] `gh skill install ... --all --agent cursor` が成功した（または `--from-local`）
- [ ] `gh skill list` に `solidsdd-*` がある（run / loop / context / decompose / judge / **critique** / apply-api / apply-dbc / derive-tests / implement / verify、および formal 系）
- [ ] （推奨）`project-rule.mdc` を Project Rules へコピーした
- [ ] 契約レイアウト方針を共有した（[project-template.md](project-template.md)）
- [ ] `solidsdd-context`、`solidsdd-loop`、または `solidsdd-run` のスモークが通る（生産者の直後に `solidsdd-critique` が Task 起動される）
- [ ] 契約テストがプロジェクトの `npm test` / `bundle exec rspec` 等で走る

### 任意（スタック別）

- [ ] GraphQL を使う場合: `graphql/schema.graphql` と `adapter_hint: graphql`
- [ ] Ruby の場合: `spec/contracts` + ruby-rspec 生成先
- [ ] Formal を使う場合: JDK 17+、`tla2tools` 取得手順、**human_gate** 運用をチームで合意（[phase3-gate-dryrun.md](phase3-gate-dryrun.md)）

### 共存

- [ ] NL SDD ツールとの役割分担を読んだ（[coexistence.md](coexistence.md)）

## 関連ドキュメント

- [adapters.md](adapters.md) — OpenAPI / GraphQL / OCL / formal の役割
- [execution-model.md](execution-model.md) — 実行モデル（スキルにも同梱）
- [architecture.md](architecture.md) — 全体構成
- [phase4.md](phase4.md) — 運用・エコシステム
- [../skills/README.md](../skills/README.md) — スキル一覧

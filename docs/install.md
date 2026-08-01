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

未作成でも導入可能です。`solidsdd-context` → `solidsdd-judge`（または `solidsdd-loop`）で不足を検出・生成する想定です。

## 動作確認

1. `gh skill list` で `solidsdd-*` が出ること
2. Agent に「`solidsdd-context` を実行して」または「`solidsdd-loop` を回して」と依頼
3. スキルが `references/` 配下を読んでいること
4. （任意）本リポジトリの [examples/arithmetic-api](../examples/arithmetic-api) で通し確認

自動実行時は `solidsdd-loop` を指定し、親が context 以外を Task サブエージェントで起動すること（各スキルの `references/execution-model.md` または loop 同梱版）。

## メンテナー向け: 配布準備

スキル本体の変更後:

```bash
gh skill publish --dry-run
# remote・認証済みなら（このドキュメントの範囲外）:
# gh skill publish --tag v0.1.0
```

- リポジトリ topic に `agent-skills` が付く（publish 時に案内）
- 各 `SKILL.md` に `license: MIT` を含め済み
- `adapters/`・`schemas/`・`docs/` はリポジトリ内の編集用ソース。**配布物の正は `skills/*/references/`**（自己完結）。ソースを直したら該当スキルの `references/` へ反映すること

## 更新

```bash
gh skill update --all
# または
gh skill update solidsdd-loop
```

`project-rule.mdc` をローカル改変している場合は、上書きコピーに注意してください。

## 導入チェックリスト

- [ ] `gh skill install ... --all --agent cursor` が成功した
- [ ] `gh skill list` に 8 スキル（`solidsdd-*`）がある
- [ ] （推奨）`project-rule.mdc` を Project Rules へコピーした
- [ ] `openapi/`・`contracts/`・`tests/contracts/` の方針を共有した
- [ ] `solidsdd-context` または `solidsdd-loop` のスモークが通る

## 関連ドキュメント

- [adapters.md](adapters.md) — OpenAPI / OCL の役割（リポジトリ説明用）
- [execution-model.md](execution-model.md) — 実行モデル（スキルにも同梱）
- [architecture.md](architecture.md) — 全体構成
- [../skills/README.md](../skills/README.md) — スキル一覧

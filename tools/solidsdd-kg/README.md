# solidsdd-kg

solid_sdd 内の知識グラフ基盤（Phase 1）。

テキスト正本（`knowledge/` + ChangeBrief / Gherkin 由来 ID）をパースし、派生 SQLite インデックスを構築する。要求の正本は ChangeBrief / Gherkin であり、知識層は普遍性が高く**非自明な**横断知見専用。

Optional frontmatter: `maturity` (`hypothesized` \| `confirmed` \| `canonical`; missing → confirmed) and `facets` (`vocabulary` \| `invariant` \| `decider` \| `acceptance-property`). `context` ranks by type then maturity; promote apply writes `maturity: canonical`.

## Phase status

| Phase | 内容 | 状態 |
|------|------|------|
| 1 | フルビルド / dangling / fmt | ✅ |
| 2 | schema ルール・カバレッジ・impact・baseline | ✅ |
| 3 | 知識層検査・scope 解決 | ✅ |
| 4 | context 抽出・増分ビルド | ✅ |
| 5 | 昇格候補・重複検出（自動実行なし） | ✅ (`contract_vocabulary` from OCL/OpenAPI) |

## 配置

| パス | 役割 |
|------|------|
| `.solidsdd/config.yaml` | **プロジェクト全体のパス SoT**（`paths.*`）。未配置時は下表のデフォルト |
| `.solidsdd/kg/schema.yaml` | ノード／エッジ型／検証ルール |
| `.solidsdd/kg/config.yaml` | kg 固有設定（`freshness_days` 等）と走査パスの **上書き** |
| `.solidsdd/kg/links.yaml` | アノテーション不可領域のエッジ |
| `.solidsdd/kg/baseline.json` | 既知違反（`--baseline` / `--update-baseline`） |
| `knowledge/**` | 知識ノード（1 ファイル = 1 ノード） |
| `.solidsdd-cache/kg.db` | 派生物（gitignore） |

走査パス（`knowledge_dirs` / `brief_glob` / `feature_glob` / `cache_dir` / `schema_path` / `links_files`）は、まず `.solidsdd/config.yaml` の `paths` から既定値を取り、その後 `kg/config.yaml` で overlay する。パス変更はプロジェクト config を推奨し、kg config は kg 固有項目と明示上書き用。
## ビルド

```bash
export PATH="$HOME/.local/go/bin:$PATH"   # またはシステム Go
cd tools/solidsdd-kg
go build -o ../../bin/solidsdd-kg ./cmd/solidsdd-kg
```

リポジトリルートから:

```bash
./scripts/solidsdd-kg.sh build --root .
./scripts/solidsdd-kg.sh check --root .
./scripts/solidsdd-kg.sh check --root . --baseline
./scripts/solidsdd-kg.sh check --root . --update-baseline
./scripts/solidsdd-kg.sh impact POL-KG-PERSISTENCE --direction out --hops 2
./scripts/solidsdd-kg.sh scope org.solid_sdd.kg
./scripts/solidsdd-kg.sh context POL-KG-PERSISTENCE --hops 2 --budget 8k
./scripts/solidsdd-kg.sh promote suggest --root .
# JSON includes contract_vocabulary hints for OCL/OpenAPI terms without concept nodes
./scripts/solidsdd-kg.sh promote suggest --root . --json
./scripts/solidsdd-kg.sh promote apply --approve --type decision --id DEC-X --title "…"
./scripts/solidsdd-kg.sh build --root .          # skips when unchanged
./scripts/solidsdd-kg.sh build --root . --force
./scripts/solidsdd-kg.sh fmt --root .
./scripts/solidsdd-kg.sh fmt --root . --check
```

SDD 組み込み: スキル [`solidsdd-knowledge`](../../skills/solidsdd-knowledge/SKILL.md)（`consult` / `harvest`）が本 CLI を呼び、`solidsdd-run` の作業の一貫としてナレッジを消費・収穫する。手順は [reference-src/knowledge.md](../../reference-src/knowledge.md)。

カバレッジ（implements / verifies）は **warn** 既定。導入時は `--update-baseline` で既存穴を記録し、`--baseline` で新規違反のみをエラーにする（RQ-010 / FR-213）。

## 設計メモ

- requirement ID は `<change_id>/<id>`（例: `initial-reservation/R1`）
- 詳細は `knowledge/decisions/KG-DEC-*.md`

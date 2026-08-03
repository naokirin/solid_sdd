# solidsdd-kg

solid_sdd 内の知識グラフ基盤（Phase 1）。

テキスト正本（`knowledge/` + ChangeBrief / Gherkin 由来 ID）をパースし、派生 SQLite インデックスを構築する。要求の正本は ChangeBrief / Gherkin であり、知識層は普遍性の高い横断知見専用。

## Phase 1 範囲

| 機能 | 状態 |
|------|------|
| フルビルド（FR-101, 103, 104） | ✅ |
| dangling reference（FR-202） | ✅ |
| frontmatter フォーマッタ（FR-701） | ✅ |
| 増分ビルド・カバレッジ検査・コンテキスト抽出 | 未（Phase 2+） |

## 配置

| パス | 役割 |
|------|------|
| `.solidsdd/kg/schema.yaml` | ノード／エッジ型 |
| `.solidsdd/kg/config.yaml` | 走査パス |
| `.solidsdd/kg/links.yaml` | アノテーション不可領域のエッジ |
| `knowledge/**` | 知識ノード（1 ファイル = 1 ノード） |
| `.solidsdd-cache/kg.db` | 派生物（gitignore） |

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
./scripts/solidsdd-kg.sh fmt --root .
./scripts/solidsdd-kg.sh fmt --root . --check
```

## 設計メモ

- requirement ID は `<change_id>/<id>`（例: `initial-reservation/R1`）
- 詳細は `knowledge/decisions/KG-DEC-*.md`

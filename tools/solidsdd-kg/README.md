# solidsdd-kg

solid_sdd 内の知識グラフ基盤（Phase 1）。

テキスト正本（`knowledge/` + ChangeBrief / Gherkin 由来 ID）をパースし、派生 SQLite インデックスを構築する。要求の正本は ChangeBrief / Gherkin であり、知識層は普遍性の高い横断知見専用。

## Phase status

| Phase | 内容 | 状態 |
|------|------|------|
| 1 | フルビルド / dangling / fmt | ✅ |
| 2 | schema ルール・カバレッジ・impact・baseline | ✅ |
| 3 | 知識層検査・scope 解決 | ✅ |
| 4+ | context 抽出・昇格 | 未 |

## 配置

| パス | 役割 |
|------|------|
| `.solidsdd/kg/schema.yaml` | ノード／エッジ型／検証ルール |
| `.solidsdd/kg/config.yaml` | 走査パス |
| `.solidsdd/kg/links.yaml` | アノテーション不可領域のエッジ |
| `.solidsdd/kg/baseline.json` | 既知違反（`--baseline` / `--update-baseline`） |
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
./scripts/solidsdd-kg.sh check --root . --baseline
./scripts/solidsdd-kg.sh check --root . --update-baseline
./scripts/solidsdd-kg.sh impact POL-KG-PERSISTENCE --direction out --hops 2
./scripts/solidsdd-kg.sh scope org.solid_sdd.kg
./scripts/solidsdd-kg.sh fmt --root .
./scripts/solidsdd-kg.sh fmt --root . --check
```

カバレッジ（implements / verifies）は **warn** 既定。導入時は `--update-baseline` で既存穴を記録し、`--baseline` で新規違反のみをエラーにする（RQ-010 / FR-213）。

## 設計メモ

- requirement ID は `<change_id>/<id>`（例: `initial-reservation/R1`）
- 詳細は `knowledge/decisions/KG-DEC-*.md`

# solid_sdd

機械可読な仕様（API 契約・契約による設計など）を、AI 開発ループの中で **適用判断から検証まで人の介在を最小化して回す** ための、ルール／スキル型 Spec-Driven Development（SDD）基盤です。

現行の多くの SDD ツールは、自然言語仕様から実装・テストを生成するループが中心です。本プロジェクトはそれに加え、次を第一級の関心事にします。

- **どこに・どの仕様技術を載せるか** の判断の仕組み化
- **スタックに応じた契約の具体化**（OpenAPI 等 / Design by Contract 等）
- **生成 → 検証 → フィードバック** の自動ループへの組み込み

## 現状

構想・設計に加え、MVP アダプタ（OpenAPI + OCL→契約テスト）、評価用サンプル、**`gh skill` 向け自己完結スキル**まで整備しています。

## 導入（要約）

```bash
gh skill install <OWNER>/solid_sdd --all --agent cursor --scope project
cp .agents/skills/solidsdd-loop/references/project-rule.mdc .cursor/rules/solidsdd.mdc  # パスは環境による
```

詳細は [docs/install.md](docs/install.md)。

メンテナーが `adapters/` 等を直したあと:

```bash
scripts/sync-skill-references.sh
scripts/sync-skill-references.sh --check
scripts/install-git-hooks.sh   # 初回のみ（pre-commit 有効化）
```

Cursor / Claude Code ではソース編集時に Hook が sync を自動実行します（`.cursor/hooks.json` / `.claude/settings.json`）。

## ドキュメント

| 文書 | 内容 |
|------|------|
| [docs/install.md](docs/install.md) | **導入手順（gh skill 推奨）** |
| [docs/vision.md](docs/vision.md) | 問題意識・目標・使い分けの軸 |
| [docs/architecture.md](docs/architecture.md) | ルール・エージェント／スキル構成 |
| [docs/adapters.md](docs/adapters.md) | アダプタ方針（OpenAPI / GraphQL / OCL） |
| [docs/execution-model.md](docs/execution-model.md) | Orchestrator / Subagent の実行ポリシー |
| [docs/roadmap.md](docs/roadmap.md) | MVP 範囲と段階的導入 |
| [docs/mvp-evaluation.md](docs/mvp-evaluation.md) | MVP 通し評価の記録 |
| [docs/phase2.md](docs/phase2.md) | Phase 2（判断軸・ゲート・アダプタ） |
| [docs/phase2-evaluation.md](docs/phase2-evaluation.md) | Phase 2 サンプル評価 |
| [docs/phase3.md](docs/phase3.md) | Phase 3 形式仕様の設計 |
| [docs/phase3-evaluation.md](docs/phase3-evaluation.md) | Phase 3 TLC サンプル評価 |
| [examples/arithmetic-api](examples/arithmetic-api) | OpenAPI 評価サンプル |
| [examples/arithmetic-graphql](examples/arithmetic-graphql) | GraphQL 評価サンプル |
| [examples/arithmetic-ruby](examples/arithmetic-ruby) | Ruby/RSpec 評価サンプル |
| [examples/memory-formal](examples/memory-formal) | TLA+/TLC 評価サンプル |

## 実行イメージ（要約）

Kiro 等と同様に、ユーザーがフェーズ単位のスキルを任意に呼び出せる一方、オーケストレータ（エージェント）が同じスキル群を使って自動実行もできます。

詳細は [docs/architecture.md](docs/architecture.md) を参照してください。

## スコープ方針（要約）

- **MVP 中核**: OpenAPI、OCL による DbC（サブエージェントがテスト生成）、適用判断、検証ループ
- **評価サンプル**: TypeScript の四則演算 API（拡張時は電卓メモリ等）
- **後回し**: 形式仕様記述言語（TLA+ / Alloy / VDM 等）

詳細は [docs/adapters.md](docs/adapters.md) と [docs/roadmap.md](docs/roadmap.md) を参照してください。

## ライセンス

[MIT](LICENSE)

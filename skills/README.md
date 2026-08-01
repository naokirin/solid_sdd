# Skills index

Agent Skills for solid_sdd（[agentskills.io](https://agentskills.io) / `gh skill` 対応）。

各スキルは **自己完結** です。必要なアダプタ・スキーマ・実行モデルは `references/` に同梱しています。導入は [docs/install.md](../docs/install.md)。

実行ポリシーの詳細: 各スキルの `references/`、または [../docs/execution-model.md](../docs/execution-model.md)

| Skill | Command-like id | Role | Execution |
|-------|-----------------|------|-----------|
| [solidsdd-loop](solidsdd-loop/SKILL.md) | `solidsdd.loop` | Orchestration | orchestrator only |
| [solidsdd-context](solidsdd-context/SKILL.md) | `solidsdd.context` | Stack / contract discovery | orchestrator |
| [solidsdd-judge](solidsdd-judge/SKILL.md) | `solidsdd.judge` | ApplicationPlan | **subagent required** |
| [solidsdd-apply-api](solidsdd-apply-api/SKILL.md) | `solidsdd.apply.api` | OpenAPI | **subagent required** |
| [solidsdd-apply-dbc](solidsdd-apply-dbc/SKILL.md) | `solidsdd.apply.dbc` | OCL | **subagent required** |
| [solidsdd-derive-tests](solidsdd-derive-tests/SKILL.md) | `solidsdd.derive.tests` | OCL → contract tests | **subagent required** |
| [solidsdd-implement](solidsdd-implement/SKILL.md) | `solidsdd.implement` | Implementation | **subagent required** |
| [solidsdd-verify](solidsdd-verify/SKILL.md) | `solidsdd.verify` | VerificationReport | **subagent required** |

- Manual: user may run one skill in the current agent.
- Automatic (`solidsdd-loop`): parent must launch **subagent required** skills via Task (or equivalent); never execute those skill bodies in the parent.

## Maintainer: keep `references/` in sync

編集ソース → `skills/*/references/` のコピーは **手で直さず**、スクリプトで同期します。

| ソース | 例 |
|--------|-----|
| `adapters/openapi/README.md` | `*/openapi-adapter.md` |
| `adapters/ocl/README.md` | `*/ocl-adapter.md`（実行モデルへのパス書き換えあり） |
| `docs/execution-model.md` | `solidsdd-loop/references/execution-model.md` |
| `schemas/*.json` | judge / verify |
| `rules/solidsdd.mdc` | `solidsdd-loop/references/project-rule.mdc` |
| `reference-src/*` | contract-layout / judgment-axes |

```bash
# 手動
scripts/sync-skill-references.sh
scripts/sync-skill-references.sh --check

# AI 編集時（自動）
# - Cursor: .cursor/hooks.json → afterFileEdit
# - Claude Code: .claude/settings.json → PostToolUse (Edit|Write|MultiEdit)

# コミット時（ずれなら失敗し、実行すべきコマンドを表示）
scripts/install-git-hooks.sh   # 一度だけ: core.hooksPath=scripts/git-hooks
```
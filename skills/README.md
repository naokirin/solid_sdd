# Skills index

Agent Skills for solid_sdd（[agentskills.io](https://agentskills.io) / `gh skill` 対応）。

各スキルは **自己完結** です。必要なアダプタ・スキーマ・実行モデルは当該スキルの `references/` に同梱しています（`gh skill` で個別インストールしても他パスを読みません）。導入は [docs/install.md](../docs/install.md)。

実行ポリシー: `solidsdd-run/references/execution-model.md` または `solidsdd-loop/references/execution-model.md`（リポジトリ内の設計メモは [../docs/execution-model.md](../docs/execution-model.md)）。

| Skill | Command-like id | Role | Execution |
|-------|-----------------|------|-----------|
| [solidsdd-run](solidsdd-run/SKILL.md) | `solidsdd.run` | Outer orchestration (WorkPlan → loops → integration verify) | orchestrator only |
| [solidsdd-loop](solidsdd-loop/SKILL.md) | `solidsdd.loop` | Slice orchestration (one intent) | orchestrator only |
| [solidsdd-context](solidsdd-context/SKILL.md) | `solidsdd.context` | Stack / contract discovery | orchestrator |
| [solidsdd-decompose](solidsdd-decompose/SKILL.md) | `solidsdd.decompose` | WorkPlan (one verifiable AC per item) | **subagent required** |
| [solidsdd-judge](solidsdd-judge/SKILL.md) | `solidsdd.judge` | ApplicationPlan | **subagent required** |
| [solidsdd-critique](solidsdd-critique/SKILL.md) | `solidsdd.critique` | CritiqueReport (adversarial phase gate) | **subagent required** |
| [solidsdd-apply-api](solidsdd-apply-api/SKILL.md) | `solidsdd.apply.api` | OpenAPI | **subagent required** |
| [solidsdd-apply-dbc](solidsdd-apply-dbc/SKILL.md) | `solidsdd.apply.dbc` | OCL | **subagent required** |
| [solidsdd-derive-tests](solidsdd-derive-tests/SKILL.md) | `solidsdd.derive.tests` | OCL → contract tests | **subagent required** |
| [solidsdd-implement](solidsdd-implement/SKILL.md) | `solidsdd.implement` | Implementation | **subagent required** |
| [solidsdd-verify](solidsdd-verify/SKILL.md) | `solidsdd.verify` | VerificationReport | **subagent required** |
| [solidsdd-apply-formal](solidsdd-apply-formal/SKILL.md) | `solidsdd.apply.formal` | Formal specs (TLA+) | **subagent required** |
| [solidsdd-verify-formal](solidsdd-verify-formal/SKILL.md) | `solidsdd.verify.formal` | Formal VerificationReport | **subagent required** |

- Manual: user may run one skill in the current agent.
- Automatic (`solidsdd-run`): parent decomposes, runs **parallel** `solidsdd-loop` waves for ready items (serialize only on path contention), then integration verify; never inline subagent-required skills.
- Automatic (`solidsdd-loop`): parent must launch **subagent required** skills via Task (or equivalent); never execute those skill bodies in the parent. After each producer step, launch `solidsdd-critique` as its own Task.

## Maintainer: keep `references/` in sync

編集ソース → `skills/*/references/` のコピーは **手で直さず**、スクリプトで同期します。

| ソース | 例 |
|--------|-----|
| `adapters/openapi/README.md` | `*/openapi-adapter.md` |
| `adapters/graphql/README.md` | `*/graphql-adapter.md` |
| `adapters/ruby-rspec/README.md` | `*/ruby-rspec-adapter.md` |
| `adapters/ocl/README.md` | `*/ocl-adapter.md` |
| `adapters/formal/README.md` | `*/formal-adapter.md` |
| `docs/execution-model.md` | `solidsdd-loop` / `solidsdd-run` `references/execution-model.md` |
| `schemas/*.json` | judge / decompose / verify / verify-formal / critique / run |
| `rules/solidsdd.mdc` | loop / run `references/project-rule.mdc` |
| `reference-src/*` | contract-layout / judgment-axes / human-gates / loop-retry / adversarial-critique / work-decomposition |

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

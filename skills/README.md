# Skills index

Cursor Agent Skill definitions for solid_sdd. Copy or link into a project's `.cursor/skills/` to use.

実行ポリシーの詳細: [../docs/execution-model.md](../docs/execution-model.md)

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

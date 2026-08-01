# Skills index

Cursor Agent Skill definitions for solid_sdd. Copy or link into a project's `.cursor/skills/` to use.

実行ポリシーの詳細: [../docs/execution-model.md](../docs/execution-model.md)

| Skill | Command-like id | Role | Execution |
|-------|-----------------|------|-----------|
| [sdd-loop](sdd-loop/SKILL.md) | `sdd.loop` | Orchestration | orchestrator only |
| [sdd-context](sdd-context/SKILL.md) | `sdd.context` | Stack / contract discovery | orchestrator |
| [sdd-judge](sdd-judge/SKILL.md) | `sdd.judge` | ApplicationPlan | orchestrator |
| [sdd-apply-api](sdd-apply-api/SKILL.md) | `sdd.apply.api` | OpenAPI | **subagent required** |
| [sdd-apply-dbc](sdd-apply-dbc/SKILL.md) | `sdd.apply.dbc` | OCL | **subagent required** |
| [sdd-derive-tests](sdd-derive-tests/SKILL.md) | `sdd.derive.tests` | OCL → contract tests | **subagent required** |
| [sdd-implement](sdd-implement/SKILL.md) | `sdd.implement` | Implementation | **subagent required** |
| [sdd-verify](sdd-verify/SKILL.md) | `sdd.verify` | VerificationReport | **subagent required** |

- Manual: user may run one skill in the current agent.
- Automatic (`sdd-loop`): parent must launch **subagent required** skills via Task (or equivalent); never execute those skill bodies in the parent.

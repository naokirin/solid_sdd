# solid_sdd

A rules-and-skills Spec-Driven Development (SDD) foundation that runs machine-readable specs (structured requirements, API contracts, Design by Contract, and more) through an AI development loop—from **application judgment through verification with minimal human intervention**.

Most SDD tools center on loops that go from natural-language specs to design, implementation, and tests. This project treats the following as first-class concerns on top of that:

- **Structured change framing** (Change Context Markdown: demand, NFRs, tech selection)—before Brief
- **Human-readable change report** (optional Markdown/HTML snapshot via `solidsdd-report`)
- **Structured change premise** (ChangeBrief: goals, in/out of scope)—return point when judgment is ambiguous
- **Structured requirement intake** (property-level Gherkin Scenarios → WorkPlan slices)—not free-form prose alone
- **Systematizing judgment** of *where* and *which* specification techniques to apply
- **Stack-specific materialization** of contracts (OpenAPI, Design by Contract, etc.)
- **Wiring generate → verify → feedback** into an automated loop

Artifacts prioritize **gap reduction and mechanical checks** for the active change—not everlasting living documentation. Contract reuse fitness is situational (see [docs/vision.md](docs/vision.md)).

## Status

Vision and design are in place, plus MVP adapters (OpenAPI + OCL→contract tests), evaluation samples, and **self-contained skills for `gh skill`**.

## Install (summary)

```bash
gh skill install naokirin/solid_sdd --all --agent cursor --scope project
cp .agents/skills/solidsdd-loop/references/project-rule.mdc .cursor/rules/solidsdd.mdc  # path may vary by environment
# Optional: set Working language in that rule (`Working language: ja` for Japanese .solidsdd prose)
```

Details: [docs/install.md](docs/install.md). Working language policy: [reference-src/working-language.md](reference-src/working-language.md).

After maintainers change `adapters/` and related sources:

```bash
scripts/sync-skill-references.sh
scripts/sync-skill-references.sh --check
scripts/install-git-hooks.sh   # once (enable pre-commit)
```

In Cursor / Claude Code, hooks run sync automatically on source edits (`.cursor/hooks.json` / `.claude/settings.json`).

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/install.md](docs/install.md) | **Install guide (`gh skill` recommended)** |
| [docs/vision.md](docs/vision.md) | Problem framing, goals, selection axes |
| [docs/architecture.md](docs/architecture.md) | Rules, agents, and skill layout |
| [docs/adapters.md](docs/adapters.md) | Adapter policy (OpenAPI / GraphQL / OCL) |
| [docs/execution-model.md](docs/execution-model.md) | Orchestrator / Subagent execution policy |
| [docs/run-cost.md](docs/run-cost.md) | Live-run wall-clock cost and greenfield mitigations |
| [docs/roadmap.md](docs/roadmap.md) | MVP scope and phased rollout |
| [docs/mvp-evaluation.md](docs/mvp-evaluation.md) | MVP end-to-end evaluation notes |
| [docs/phase2.md](docs/phase2.md) | Judgment axes, gates, and adapters |
| [docs/phase2-evaluation.md](docs/phase2-evaluation.md) | GraphQL / Ruby sample evaluation |
| [docs/phase3.md](docs/phase3.md) | Formal-spec design |
| [docs/phase3-evaluation.md](docs/phase3-evaluation.md) | TLC sample evaluation |
| [docs/phase3-gate-dryrun.md](docs/phase3-gate-dryrun.md) | Formal human_gate dry run |
| [docs/phase4.md](docs/phase4.md) | Operations and ecosystem |
| [docs/intent-inspired-improvements.md](docs/intent-inspired-improvements.md) | Maturity, Grill, Means, clarifications, facets, `solidsdd-next` |
| [tools/solidsdd-kg](tools/solidsdd-kg) | Knowledge graph CLI (engine for `solidsdd-knowledge`) |
| [scripts/solidsdd-host-toolchain.sh](scripts/solidsdd-host-toolchain.sh) | Host toolchain preflight (`.solidsdd/host-toolchain.json`; detect env thrash vs run cost) |
| [scripts/solidsdd-next.sh](scripts/solidsdd-next.sh) | Deterministic next-action / declared-step validate (read-only) |
| [skills/solidsdd-knowledge](skills/solidsdd-knowledge) | SDD consult / harvest of durable knowledge |
| [skills/solidsdd-grill](skills/solidsdd-grill) | Conditional structured interview → clarifications |
| [docs/coexistence.md](docs/coexistence.md) | Coexistence with other SDD tools |
| [docs/project-template.md](docs/project-template.md) | Consuming-project layout |
| [docs/feedback-tuning.md](docs/feedback-tuning.md) | Feedback and rule tuning |
| [examples/arithmetic-api](examples/arithmetic-api) | OpenAPI evaluation sample |
| [examples/inventory-reservation](examples/inventory-reservation) | Soft-hold inventory E2E sample (OpenAPI + OCL + Vitest) |
| [examples/arithmetic-graphql](examples/arithmetic-graphql) | GraphQL evaluation sample |
| [examples/arithmetic-ruby](examples/arithmetic-ruby) | Ruby/RSpec evaluation sample |
| [examples/memory-formal](examples/memory-formal) | TLA+/TLC evaluation sample |

## Execution sketch (summary)

As with Kiro and similar tools, users can invoke phase skills manually, while an orchestrator can also run the same skill set automatically.

- **`solidsdd-run`**: knowledge consult → [optional Grill] → Change Context → ChangeBrief → property-level Gherkin WorkPlan → parallel `solidsdd-loop` waves → integration verify → knowledge harvest (human-gated) → done (prefer `scripts/solidsdd-next.sh` for sequencing)
- **`solidsdd-loop`**: Contract loop for one slice (one Scenario / change intent)
- **`solidsdd-knowledge`**: Durable `knowledge/` consult / harvest (CLI: `tools/solidsdd-kg`)
- **`solidsdd-grill`**: Conditional framing interview → `clarifications/open.json`

See [docs/architecture.md](docs/architecture.md) and [docs/execution-model.md](docs/execution-model.md).

## Scope policy (summary)

- **Core**: Change Context, ChangeBrief, property-level Gherkin intake, OpenAPI, OCL-based DbC (subagent generates tests), application judgment, verification loop, knowledge consult/harvest
- **Evaluation sample**: TypeScript arithmetic API (extendable with calculator memory, etc.)
- **Optional / gated**: Formal specification languages (TLA+ / Alloy / VDM, etc.)

See [docs/adapters.md](docs/adapters.md) and [docs/roadmap.md](docs/roadmap.md).

## License

[MIT](LICENSE)

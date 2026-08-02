# reference-src

Edit sources for skill-bundled docs that do **not** live under repo-root `adapters/`, `schemas/`, `docs/`, or `rules/`.

| File | Example distribute-to |
|------|------------------------|
| `contract-layout.md` | context / implement / loop |
| `judgment-axes.md` | judge / critique |
| `human-gates.md` | judge / loop |
| `loop-retry.md` | verify / critique / loop |
| `adversarial-critique.md` | critique / loop / run |
| `work-decomposition.md` | decompose / run |
| `gherkin-requirements.md` | decompose / run / critique |
| `change-brief.md` | brief / run / decompose / critique / judge |

Sync with `scripts/sync-skill-references.sh`. Do not hand-edit `skills/*/references/` (they will be overwritten).

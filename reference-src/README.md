# reference-src

Skill `references/` のうち、repo 直下の `adapters/` / `schemas/` / `docs/` / `rules/` に無い **スキル同梱用の編集ソース** を置く場所です。

| ファイル | 配布先（例） |
|----------|----------------|
| `contract-layout.md` | context / implement / loop |
| `judgment-axes.md` | judge |

同期は `scripts/sync-skill-references.sh` を使います。`skills/*/references/` を手で編集しないでください（上書きされます）。

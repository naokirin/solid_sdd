# Ruby / RSpec test-target adapter (Phase 2)

編集用ソース。OCL は引き続きソース・オブ・トゥルース。本アダプタは **契約テストの生成先** を Vitest から RSpec に差し替えるときの規約。

同期先: `skills/solidsdd-derive-tests/references/ruby-rspec-adapter.md`（および verify / apply-dbc が参照する場合）。ソース変更後:

```bash
scripts/sync-skill-references.sh
```

## Role

Map UML OCL → **RSpec** examples under `spec/contracts/`, for Ruby (and Rails-ready) stacks that keep OCL as SoT and do **not** require a language-native contracts gem.

Language-native contract libraries (e.g. optional gems) are **out of scope** here and remain deferred—projects must be able to refuse them.

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| OCL contracts | `contracts/**/*.ocl` |
| Generated contract specs | `spec/contracts/**/*_spec.rb` |
| Domain code (typical) | `lib/**/*.rb` |

## Pipeline

Same as the OCL adapter; only the derive/verify test runner changes:

```text
solidsdd.apply.dbc      →  write/update .ocl
solidsdd.derive.tests   →  OCL → RSpec (this adapter)
solidsdd.implement      →  satisfy contracts in Ruby
solidsdd.verify         →  bundle exec rspec spec/contracts
```

## Derivation conventions

- One OCL type → one `*_spec.rb` when practical (`Calculator.ocl` → `calculator_spec.rb`)
- `pre` failures → expect a domain error / ArgumentError (project-chosen); document in README
- `post` → assert return values and observable state
- Do not invent requirements absent from OCL
- Prefer regenerating whole spec files over drifting patches

## Skill mapping

- Write/update OCL: `solidsdd-apply-dbc`
- Derive tests: `solidsdd-derive-tests` with test-target hint `rspec` / `ruby-rspec`
- Check: `solidsdd-verify` (project test script)

## Evaluation sample

[../../examples/arithmetic-ruby](../../examples/arithmetic-ruby) — Calculator only (no HTTP / GraphQL).

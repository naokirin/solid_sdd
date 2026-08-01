# Formal specification adapter (Phase 3)

編集用ソース。同期: `skills/solidsdd-apply-formal|verify-formal/references/formal-adapter.md`。ソース変更後:

```bash
scripts/sync-skill-references.sh
```

## Role

Express **safety / liveness / concurrency** properties that API contracts and OCL→tests do not cheaply cover. Formal specs are **optional** and narrow-scope. Prefer OpenAPI/GraphQL + OCL unless [docs/phase3.md](../../docs/phase3.md) apply conditions hold.

## Default checker: TLA+ / TLC

| Choice | Role |
|--------|------|
| **TLC** (default) | Model-check `.tla` + `.cfg` via `tools/tla/tlc.sh` |
| Apalache | Optional later (inductive invariants) |
| Alloy | Optional alternate notation (`adapter_hint: alloy`) |

Setup: [../../tools/tla/README.md](../../tools/tla/README.md) (`fetch-tla2tools.sh`, JDK 17+).

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| TLA+ modules | `formal/**/*.tla` |
| TLC configs | `formal/**/*.cfg` |
| Alloy models | `formal/**/*.als` (optional) |

## Responsibilities

- Keep models small (one protocol / shared resource)
- Name invariants and temporal properties explicitly
- Do not duplicate OpenAPI field lists or OCL arithmetic posts in the formal model
- Flag tooling gaps; never pretend a model was checked if the checker did not run

## Verification hooks

- Parse / type-check via TLC
- Run `tools/tla/tlc.sh <Spec.tla> -config <Spec.cfg>` (or project wrapper)
- On missing jar/JDK: `failure_class: tooling`, `loop_action: stop` or `human_gate`
- On invariant violation: prefer `solidsdd-apply-formal` (spec) unless implementation SoT is clearer

## Skill mapping

- Write/update: `solidsdd-apply-formal` (`adapter_hint: tla`)
- Check: `solidsdd-verify-formal` (VerificationReport check kind `formal`)

## Evaluation sample

[../../examples/memory-formal](../../examples/memory-formal) — exclusive shared-memory adds; `./verify.sh` must report no TLC error.

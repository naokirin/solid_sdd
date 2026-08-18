# Triage / Execution Profile regression fixtures

Deterministic fixtures for [triage.md](../../reference-src/triage.md) calibration — mirrors [evals/critique/](../critique/) in shape and in scope limits.

## Layout

```text
evals/triage/cases/<id>/
  case.json           # { "id", "description", "scenario" }
  triage-result.json  # candidate TriageResult ([schemas/triage-result.schema.json](../../schemas/triage-result.schema.json))
  expected.json       # { "schema_valid", "requested_profile"?, "required_minimum_profile"?, "effective_profile"?, "invariant_violation"? }
```

## Run

```bash
python3 scripts/solidsdd-triage-eval.py
python3 scripts/solidsdd-triage-eval.py --case 004-auth-change-forces-full-despite-thin-request
```

Requires `jsonschema` (same as `solidsdd-lint`).

## What this checks — and what it does not

These fixtures check **mechanical** invariants only:

1. `triage-result.json` validates against `triage-result.schema.json`
2. `effective_profile` ranks at or above `required_minimum_profile` (the explicit-profile safety override)
3. A hand-verified scenario's `required_minimum_profile` / `effective_profile` match the documented priority table

They do **not** test whether an LLM performing Triage would independently derive the same classification from the `scenario` prose — that variance is out of scope here, the same limit [evals/critique/README.md](../critique/README.md) documents for full LLM critique judgment. `triage-result.json` in each case is the fixture's fixed, hand-authored "known-correct" (or, for `006-*`, deliberately-broken) output; the runner only checks it against the schema and the safety-override invariant, and against the case's declared expected profile fields.

## Cases

| id | Exercises |
|----|-----------|
| `001-typo-fix-direct` | Local + low risk/complexity → `direct` |
| `002-small-additive-feature-thin` | Small additive, local impact confirmed → `thin` |
| `003-public-api-change-standard` | Additive but published contract change → `standard` |
| `004-auth-change-forces-full-despite-thin-request` | Explicit `--profile thin` on a high-risk category is overridden to `full` |
| `005-uncertain-change-escalates` | `uncertain: true` must not resolve to `direct`/`thin` |
| `006-effective-below-minimum-is-invalid` | Negative case: `effective_profile` below `required_minimum_profile` is flagged even though the JSON is schema-valid on its own |

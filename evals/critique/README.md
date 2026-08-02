# Critique / lint regression fixtures

Deterministic fixtures for [adversarial-critique.md](../../reference-src/adversarial-critique.md) calibration (F10: polish ≠ major).

## Layout

```text
evals/critique/cases/<id>/
  case.json       # { "id", "checker", "description" }
  expected.json   # { "result", "must_include": [...], "forbidden": [...] }
  fixture/        # mini consuming project (.solidsdd/, optional openapi/, contracts/)
```

## Run

```bash
python3 scripts/solidsdd-critique-eval.py
python3 scripts/solidsdd-critique-eval.py --case 010-clean-standard-density
```

Requires `jsonschema` (same as `solidsdd-lint`).

## Checkers

| checker | What it exercises |
|---------|-------------------|
| `lint` | `scripts/solidsdd-lint.sh` (schema, covers, Gherkin, NFR, …) |
| `static_ocl` | Vacuous `pre: true` in OCL |
| `static_openapi` | Happy-path-only API (no 4xx/default) |
| `lint_and_static` | Union |

~Half of cases are **must-pass** (`010+`) so F10 over-strictness is caught.

Full LLM critique variance (3× runs) is **out of CI** for M3; these fixtures cover mechanical major triggers.

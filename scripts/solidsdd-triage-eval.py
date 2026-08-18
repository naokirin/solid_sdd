#!/usr/bin/env python3
"""Run deterministic Triage regression fixtures under evals/triage/cases/.

Each case has:
  case.json           — metadata (id, description, scenario)
  triage-result.json  — candidate TriageResult to check
  expected.json        — { "schema_valid", "requested_profile", "required_minimum_profile",
                            "effective_profile", "invariant_violation"? }

These are mechanical checks only: schema validity, the safety-override
invariant (effective_profile must rank >= required_minimum_profile), and that
a hand-verified scenario's classification matches the documented priority
table in reference-src/triage.md. Full LLM Triage judgment variance is out of
scope here, the same limit evals/critique/README.md documents for critique.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    print("solidsdd-triage-eval requires the jsonschema package", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "triage" / "cases"
SCHEMA = ROOT / "schemas" / "triage-result.schema.json"

PROFILE_RANK = {"direct": 0, "thin": 1, "standard": 2, "full": 3}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_schema(candidate: dict) -> str | None:
    schema = load(SCHEMA)
    try:
        Draft202012Validator(schema).validate(candidate)
    except jsonschema.ValidationError as e:
        return e.message
    return None


def run_case(case_dir: Path) -> tuple[bool, str]:
    expected = load(case_dir / "expected.json")
    candidate = load(case_dir / "triage-result.json")

    schema_error = check_schema(candidate)
    schema_valid = schema_error is None
    if schema_valid != expected.get("schema_valid", True):
        return False, f"schema_valid want {expected.get('schema_valid', True)!r} got {schema_valid!r} ({schema_error})"
    if not schema_valid:
        # Nothing further to check meaningfully once the shape itself is wrong.
        return True, "ok (schema-invalid as expected)"

    effective = candidate.get("effective_profile")
    required_min = candidate.get("required_minimum_profile")
    invariant_ok = PROFILE_RANK.get(effective, -1) >= PROFILE_RANK.get(required_min, 99)
    invariant_violation = not invariant_ok
    if invariant_violation != expected.get("invariant_violation", False):
        return False, (
            f"invariant_violation want {expected.get('invariant_violation', False)!r} "
            f"got {invariant_violation!r} (effective={effective!r}, required_minimum={required_min!r})"
        )

    for field in ("requested_profile", "required_minimum_profile", "effective_profile"):
        if field in expected and candidate.get(field) != expected[field]:
            return False, f"{field} want {expected[field]!r} got {candidate.get(field)!r}"

    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="Run a single case id")
    args = parser.parse_args()
    cases = sorted(p for p in CASES.iterdir() if p.is_dir()) if CASES.is_dir() else []
    if args.case:
        cases = [CASES / args.case]
    if not cases:
        print("no cases found", file=sys.stderr)
        return 2
    failed = 0
    for case_dir in cases:
        if not (case_dir / "case.json").is_file():
            continue
        cid = case_dir.name
        ok, msg = run_case(case_dir)
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {cid}  {msg}")
        if not ok:
            failed += 1
    print(f"\n{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

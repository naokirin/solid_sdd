#!/usr/bin/env python3
"""Run deterministic critique/lint regression fixtures under evals/critique/cases/.

Each case has:
  case.json — metadata (id, checker, description)
  expected.json — { "result": "pass"|"fail", "must_include": [ {severity, category? } ], ... }
  fixture/ — a mini project root with .solidsdd/ (and optional openapi/, contracts/)

Checkers:
  lint — run solidsdd-lint against fixture/
  static_ocl — flag vacuous `pre:` true / empty pre in .ocl
  static_openapi — flag operations with no 4xx/default error response
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "critique" / "cases"
LINT = ROOT / "scripts" / "solidsdd-lint.sh"

PRE_TRUE = re.compile(r"\bpre\s*:\s*true\b", re.I)
PRE_EMPTY = re.compile(r"\bpre\s*:\s*$", re.M)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_lint(fixture: Path) -> dict:
    proc = subprocess.run(
        [str(LINT), "--project-root", str(fixture)],
        capture_output=True,
        text=True,
        check=False,
    )
    if not proc.stdout.strip():
        raise RuntimeError(f"lint produced no stdout: {proc.stderr}")
    return json.loads(proc.stdout)


def static_ocl(fixture: Path) -> list[dict]:
    findings = []
    for path in sorted((fixture / "contracts").rglob("*.ocl")) if (fixture / "contracts").is_dir() else []:
        text = path.read_text(encoding="utf-8")
        if PRE_TRUE.search(text) or PRE_EMPTY.search(text):
            findings.append(
                {
                    "severity": "major",
                    "category": "thin_contract",
                    "location": str(path.relative_to(fixture)),
                    "detail": "vacuous or empty OCL pre",
                }
            )
    return findings


def static_openapi(fixture: Path) -> list[dict]:
    findings = []
    path = fixture / "openapi" / "openapi.yaml"
    if not path.is_file():
        return findings
    text = path.read_text(encoding="utf-8")
    # Very lightweight: operation blocks that list responses without 4xx
    ops = re.split(r"\n\s+(get|post|put|patch|delete):\s*\n", text)
    # Fallback: if file has paths but no 4\d\d / default under responses
    if "responses:" in text and not re.search(r"['\"]?4\d\d['\"]?:", text) and "default:" not in text:
        findings.append(
            {
                "severity": "major",
                "category": "thin_contract",
                "location": "openapi/openapi.yaml",
                "detail": "no 4xx or default error responses documented",
            }
        )
    return findings


def match_expected(findings: list[dict], expected: dict) -> list[str]:
    errors: list[str] = []
    result = "fail" if any(f["severity"] in ("blocker", "major") for f in findings) else "pass"
    if result != expected.get("result"):
        errors.append(f"result want {expected.get('result')!r} got {result!r}")
    for req in expected.get("must_include") or []:
        sev = req.get("severity")
        cat = req.get("category")
        ok = any(
            (sev is None or f.get("severity") == sev)
            and (cat is None or f.get("category") == cat)
            for f in findings
        )
        if not ok:
            errors.append(f"missing finding matching {req}")
    for forb in expected.get("forbidden") or []:
        sev = forb.get("severity")
        hit = any(f.get("severity") == sev for f in findings if sev)
        if hit and forb.get("when_result") == "pass":
            errors.append(f"forbidden severity {sev} on must-pass case")
    return errors


def run_case(case_dir: Path) -> tuple[bool, str]:
    meta = load(case_dir / "case.json")
    expected = load(case_dir / "expected.json")
    fixture = case_dir / "fixture"
    checker = meta.get("checker", "lint")
    if checker == "lint":
        report = run_lint(fixture)
        findings = report.get("findings") or []
    elif checker == "static_ocl":
        findings = static_ocl(fixture)
    elif checker == "static_openapi":
        findings = static_openapi(fixture)
    elif checker == "lint_and_static":
        findings = (run_lint(fixture).get("findings") or []) + static_ocl(fixture) + static_openapi(fixture)
    else:
        return False, f"unknown checker {checker}"
    errs = match_expected(findings, expected)
    if errs:
        return False, "; ".join(errs)
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

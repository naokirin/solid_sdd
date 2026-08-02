#!/usr/bin/env python3
"""Deterministic solid_sdd lint for critique Step 0/1.

Emits JSON findings (blocker/major/minor) and exits 0 on pass, 1 on fail.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    print("solidsdd-lint requires the jsonschema package", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
LEXICON_PATH = Path(__file__).resolve().parent / "ambiguity-lexicon.json"

GHERKIN_KEYWORDS = re.compile(
    r"^\s*(Given|When|Then|And|But)\b", re.IGNORECASE | re.MULTILINE
)
SCENARIO_HDR = re.compile(
    r"^\s*Scenario(?: Outline)?:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE
)
TAG_LINE = re.compile(r"^\s*(@[^\s]+(?:\s+@[^\s]+)*)\s*$")
SCOPE_ID = re.compile(r"^[A-Z][A-Z0-9]*[0-9]+$")
COVER_TAG = re.compile(r"^@([A-Z][A-Z0-9]*[0-9]+)$")


def finding(
    severity: str, category: str, location: str, detail: str
) -> dict[str, str]:
    return {
        "severity": severity,
        "category": category,
        "location": location,
        "detail": detail,
    }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_schema(
    instance: Any, schema_name: str, location: str, findings: list[dict[str, str]]
) -> None:
    schema = load_json(SCHEMAS / schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    for err in errors:
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        findings.append(
            finding(
                "blocker",
                "schema_violation",
                f"{location}#{path}",
                err.message,
            )
        )


def resolve_change_dir(project: Path, change_id: str | None) -> tuple[str, Path]:
    active = project / ".solidsdd" / "active-change.json"
    if change_id is None:
        if not active.is_file():
            raise SystemExit("no --change-id and no .solidsdd/active-change.json")
        change_id = load_json(active)["change_id"]
    change_dir = project / ".solidsdd" / "changes" / change_id
    if not change_dir.is_dir():
        raise SystemExit(f"change directory missing: {change_dir}")
    return change_id, change_dir


def check_change_id_match(
    change_id: str, brief: dict[str, Any] | None, findings: list[dict[str, str]]
) -> None:
    if brief and brief.get("change_id") != change_id:
        findings.append(
            finding(
                "blocker",
                "consistency",
                "change-brief.json#change_id",
                f"change_id {brief.get('change_id')!r} != directory name {change_id!r}",
            )
        )


def brief_ids(brief: dict[str, Any]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {
        "in_scope": set(),
        "out_of_scope": set(),
        "success_criteria": set(),
        "all": set(),
    }
    for key in ("in_scope", "out_of_scope", "success_criteria"):
        for item in brief.get(key) or []:
            if isinstance(item, dict) and "id" in item:
                out[key].add(item["id"])
                out["all"].add(item["id"])
    return out


def check_unique_brief_ids(
    brief: dict[str, Any], findings: list[dict[str, str]]
) -> None:
    seen: dict[str, str] = {}
    for key in ("in_scope", "out_of_scope", "success_criteria"):
        for item in brief.get(key) or []:
            if not isinstance(item, dict):
                continue
            i = item.get("id")
            if not i:
                continue
            if i in seen:
                findings.append(
                    finding(
                        "blocker",
                        "consistency",
                        f"change-brief.json#{key}",
                        f"duplicate scope id {i!r} (also in {seen[i]})",
                    )
                )
            else:
                seen[i] = key


def has_gherkin_shape(text: str) -> bool:
    if not SCENARIO_HDR.search(text):
        return False
    kinds = {m.group(1).lower() for m in GHERKIN_KEYWORDS.finditer(text)}
    return {"given", "when", "then"} <= kinds


def count_scenarios(text: str) -> int:
    return len(SCENARIO_HDR.findall(text))


def depends_on_cycles(items: list[dict[str, Any]]) -> list[list[str]]:
    graph = {it["id"]: list(it.get("depends_on") or []) for it in items}
    ids = set(graph)
    cycles: list[list[str]] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {i: WHITE for i in ids}
    stack: list[str] = []

    def dfs(u: str) -> None:
        color[u] = GRAY
        stack.append(u)
        for v in graph.get(u, []):
            if v not in ids:
                continue
            if color[v] == GRAY:
                if v in stack:
                    i = stack.index(v)
                    cycles.append(stack[i:] + [v])
            elif color[v] == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for node in ids:
        if color[node] == WHITE:
            dfs(node)
    return cycles


def parse_feature_tags(project: Path) -> dict[str, set[str]]:
    """Map scenario_name -> set of @R1-style cover tags (without @)."""
    req = project / "requirements"
    mapping: dict[str, set[str]] = defaultdict(set)
    if not req.is_dir():
        return mapping
    for path in sorted(req.rglob("*.feature")):
        lines = path.read_text(encoding="utf-8").splitlines()
        pending_tags: set[str] = set()
        for line in lines:
            tm = TAG_LINE.match(line)
            if tm:
                for tok in tm.group(1).split():
                    m = COVER_TAG.match(tok)
                    if m:
                        pending_tags.add(m.group(1))
                continue
            sm = re.match(r"^\s*Scenario(?: Outline)?:\s*(.+?)\s*$", line, re.I)
            if sm:
                name = sm.group(1).strip()
                mapping[name] |= pending_tags
                pending_tags = set()
            elif line.strip() and not line.strip().startswith("#"):
                # Non-tag, non-scenario content clears pending only after scenario
                pass
    return mapping


def ambiguity_hits(text: str, lexicon: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for _lang, phrases in (lexicon.get("languages") or {}).items():
        for phrase in phrases:
            if not phrase:
                continue
            if phrase.lower() in lower or phrase in text:
                hits.append(phrase)
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def lint_change(
    project: Path, change_id: str, change_dir: Path
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    lexicon = load_json(LEXICON_PATH)

    brief_path = change_dir / "change-brief.json"
    plan_path = change_dir / "work-plan.json"
    gate_path = change_dir / "change-context-gate.json"
    status_path = change_dir / "status.json"

    brief = None
    if brief_path.is_file():
        brief = load_json(brief_path)
        validate_schema(brief, "change-brief.schema.json", str(brief_path), findings)
        check_change_id_match(change_id, brief, findings)
        check_unique_brief_ids(brief, findings)
        for key in ("in_scope", "out_of_scope", "success_criteria"):
            for item in brief.get(key) or []:
                if isinstance(item, dict) and item.get("text"):
                    for phrase in ambiguity_hits(item["text"], lexicon):
                        findings.append(
                            finding(
                                "minor",
                                "unverifiable_acceptance",
                                f"{brief_path}#{key}/{item.get('id')}",
                                f"ambiguous phrase {phrase!r} in scope text",
                            )
                        )
    else:
        findings.append(
            finding(
                "major",
                "scope_gap",
                str(brief_path),
                "change-brief.json missing for active change",
            )
        )

    if gate_path.is_file():
        validate_schema(
            load_json(gate_path),
            "change-context-gate.schema.json",
            str(gate_path),
            findings,
        )
    if status_path.is_file():
        validate_schema(
            load_json(status_path), "change-status.schema.json", str(status_path), findings
        )

    run_state_path = change_dir / "run-state.json"
    if run_state_path.is_file():
        rs = load_json(run_state_path)
        validate_schema(rs, "run-state.schema.json", str(run_state_path), findings)
        if rs.get("change_id") and rs["change_id"] != change_id:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    "run-state.json#change_id",
                    f"change_id {rs['change_id']!r} != directory {change_id!r}",
                )
            )

    work = None
    if plan_path.is_file():
        work = load_json(plan_path)
        validate_schema(work, "work-plan.schema.json", str(plan_path), findings)
        if work.get("change_id") and work["change_id"] != change_id:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    "work-plan.json#change_id",
                    f"change_id {work['change_id']!r} != directory {change_id!r}",
                )
            )

        items = work.get("items") or []
        item_ids = {it.get("id") for it in items if isinstance(it, dict)}
        for it in items:
            if not isinstance(it, dict):
                continue
            iid = it.get("id", "?")
            for dep in it.get("depends_on") or []:
                if dep not in item_ids:
                    findings.append(
                        finding(
                            "blocker",
                            "consistency",
                            f"work-plan.json#items/{iid}/depends_on",
                            f"unknown depends_on id {dep!r}",
                        )
                    )
            ac = it.get("acceptance_criterion") or ""
            if not has_gherkin_shape(ac):
                findings.append(
                    finding(
                        "major",
                        "unverifiable_acceptance",
                        f"work-plan.json#items/{iid}/acceptance_criterion",
                        "acceptance_criterion must be one Gherkin Scenario with Given/When/Then",
                    )
                )
            elif count_scenarios(ac) > 1:
                findings.append(
                    finding(
                        "major",
                        "unverifiable_acceptance",
                        f"work-plan.json#items/{iid}/acceptance_criterion",
                        "acceptance_criterion contains more than one Scenario",
                    )
                )
            for phrase in ambiguity_hits(ac, lexicon):
                findings.append(
                    finding(
                        "minor",
                        "unverifiable_acceptance",
                        f"work-plan.json#items/{iid}/acceptance_criterion",
                        f"ambiguous phrase {phrase!r}",
                    )
                )

        for cycle in depends_on_cycles([it for it in items if isinstance(it, dict)]):
            findings.append(
                finding(
                    "major",
                    "consistency",
                    "work-plan.json#depends_on",
                    f"dependency cycle: {' -> '.join(cycle)}",
                )
            )

        if brief:
            ids = brief_ids(brief)
            covered: set[str] = set()
            for it in items:
                if not isinstance(it, dict):
                    continue
                iid = it.get("id", "?")
                for cid in it.get("covers") or []:
                    if cid not in ids["all"]:
                        findings.append(
                            finding(
                                "blocker",
                                "consistency",
                                f"work-plan.json#items/{iid}/covers",
                                f"unknown Brief id {cid!r}",
                            )
                        )
                    if cid in ids["out_of_scope"]:
                        findings.append(
                            finding(
                                "major",
                                "scope_gap",
                                f"work-plan.json#items/{iid}/covers",
                                f"covers out_of_scope id {cid!r}",
                            )
                        )
                    if cid in ids["in_scope"] or cid in ids["success_criteria"]:
                        covered.add(cid)

            must = ids["in_scope"] | ids["success_criteria"]
            missing = sorted(must - covered)
            if missing:
                findings.append(
                    finding(
                        "major",
                        "scope_gap",
                        "work-plan.json#covers",
                        f"Brief ids not covered by any item.covers: {', '.join(missing)}",
                    )
                )

            # Scenario tags vs item covers
            feature_tags = parse_feature_tags(project)
            for it in items:
                if not isinstance(it, dict):
                    continue
                name = it.get("scenario_name")
                covers = set(it.get("covers") or [])
                if not name:
                    continue
                tags = feature_tags.get(name, set())
                if not tags and covers:
                    findings.append(
                        finding(
                            "major",
                            "scope_gap",
                            it.get("feature_path") or "requirements/**/*.feature",
                            f"Scenario {name!r} has no @R*/@SC* tags but WorkPlan item {it.get('id')} covers {sorted(covers)}",
                        )
                    )
                else:
                    missing_tags = sorted(covers - tags)
                    extra = sorted(tags - covers)
                    if missing_tags:
                        findings.append(
                            finding(
                                "major",
                                "scope_gap",
                                f"{it.get('feature_path')}#{name}",
                                f"Scenario tags missing WorkPlan covers ids: {', '.join(missing_tags)}",
                            )
                        )
                    if extra:
                        findings.append(
                            finding(
                                "minor",
                                "consistency",
                                f"{it.get('feature_path')}#{name}",
                                f"Scenario tags not listed in item.covers: {', '.join(extra)}",
                            )
                        )
    elif brief_path.is_file():
        # Brief without WorkPlan is OK for early critique(subject=change_brief)
        pass

    # Optional ApplicationPlan / Verification under change dir or .solidsdd/
    for pattern, schema in (
        ("application-plan*.json", "application-plan.schema.json"),
        ("verification-report*.json", "verification-report.schema.json"),
        ("critique*.json", "critique-report.schema.json"),
    ):
        for path in list(change_dir.glob(pattern)) + list(
            (project / ".solidsdd").glob(pattern)
        ):
            if not path.is_file():
                continue
            # critique-*-eval.json in examples may not match critique schema strictly; only validate known schemas
            try:
                data = load_json(path)
            except json.JSONDecodeError as e:
                findings.append(
                    finding("blocker", "schema_violation", str(path), str(e))
                )
                continue
            if schema == "critique-report.schema.json":
                if "subject" not in data or "findings" not in data:
                    continue
            validate_schema(data, schema, str(path), findings)

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="solid_sdd deterministic lint")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Consuming project root (default: cwd)",
    )
    parser.add_argument("--change-id", default=None)
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON (default compact)",
    )
    args = parser.parse_args()
    project = args.project_root.resolve()
    change_id, change_dir = resolve_change_dir(project, args.change_id)
    findings = lint_change(project, change_id, change_dir)
    fail = any(f["severity"] in ("blocker", "major") for f in findings)
    report = {
        "version": "1",
        "change_id": change_id,
        "result": "fail" if fail else "pass",
        "findings": findings,
    }
    indent = 2 if args.pretty else None
    print(json.dumps(report, ensure_ascii=False, indent=indent))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())

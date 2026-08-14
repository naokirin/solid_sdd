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

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from solidsdd_lib.paths import (  # noqa: E402
    load_layout,
    resolve_change_dir as _resolve_change_dir,
)

_ARCH_DIR = _SCRIPTS / "solidsdd-architecture"
if str(_ARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_ARCH_DIR))
import validate as _architecture_validate  # noqa: E402

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
    return _resolve_change_dir(project, change_id)


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


def dependency_cycles(
    module_ids: set[str], edges: list[tuple[str, str]]
) -> list[list[str]]:
    graph: dict[str, list[str]] = {m: [] for m in module_ids}
    for src, dst in edges:
        if src in graph and dst in module_ids:
            graph[src].append(dst)
    cycles: list[list[str]] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {m: WHITE for m in module_ids}
    stack: list[str] = []

    def dfs(u: str) -> None:
        color[u] = GRAY
        stack.append(u)
        for v in graph.get(u, []):
            if color[v] == GRAY:
                if v in stack:
                    i = stack.index(v)
                    cycles.append(stack[i:] + [v])
            elif color[v] == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for node in module_ids:
        if color[node] == WHITE:
            dfs(node)
    return cycles


def parse_feature_tags(
    project: Path, requirements_dir: Path | None = None
) -> dict[str, set[str]]:
    """Map scenario_name -> set of @R1-style cover tags (without @)."""
    req = requirements_dir if requirements_dir is not None else project / "requirements"
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
    project: Path,
    change_id: str,
    change_dir: Path,
    layout: Any | None = None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    lexicon = load_json(LEXICON_PATH)
    lay = layout if layout is not None else load_layout(project)

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

    clar_path = change_dir / "clarifications" / "open.json"
    if clar_path.is_file():
        clar = load_json(clar_path)
        validate_schema(clar, "clarifications.schema.json", str(clar_path), findings)
        if clar.get("change_id") and clar["change_id"] != change_id:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    "clarifications/open.json#change_id",
                    f"change_id {clar['change_id']!r} != directory {change_id!r}",
                )
            )
        blocking_open = [
            it
            for it in (clar.get("items") or [])
            if isinstance(it, dict)
            and it.get("blocking")
            and it.get("status") == "open"
        ]
        if blocking_open and not (clar.get("human_gate") or {}).get("required"):
            findings.append(
                finding(
                    "major",
                    "consistency",
                    "clarifications/open.json#human_gate",
                    f"blocking open items {[it.get('id') for it in blocking_open]} but human_gate.required is not true",
                )
            )

    harvest_path = change_dir / "knowledge-harvest.json"
    if harvest_path.is_file():
        harvest = load_json(harvest_path)
        validate_schema(
            harvest, "knowledge-harvest.schema.json", str(harvest_path), findings
        )
        if harvest.get("change_id") and harvest["change_id"] != change_id:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    "knowledge-harvest.json#change_id",
                    f"change_id {harvest['change_id']!r} != directory {change_id!r}",
                )
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

    nfr_path = change_dir / "nfr.json"
    status_obj = load_json(status_path) if status_path.is_file() else {}
    if nfr_path.is_file():
        nfr = load_json(nfr_path)
        validate_schema(nfr, "nfr.schema.json", str(nfr_path), findings)
        if nfr.get("change_id") and nfr["change_id"] != change_id:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    "nfr.json#change_id",
                    f"change_id {nfr['change_id']!r} != directory {change_id!r}",
                )
            )
        required_qualities = {
            "reliability",
            "security",
            "performance",
            "operability",
            "compatibility",
            "maintainability",
        }
        seen_q = set()
        for item in nfr.get("items") or []:
            if not isinstance(item, dict):
                continue
            q = item.get("quality")
            if q:
                seen_q.add(q)
            if item.get("status") == "in_scope":
                if not item.get("threshold") or not item.get("measurement"):
                    findings.append(
                        finding(
                            "major",
                            "scope_gap",
                            f"nfr.json#{item.get('id')}",
                            "in_scope NFR requires threshold and measurement",
                        )
                    )
                if status_obj.get("status") == "done":
                    vb = item.get("verified_by") or []
                    if not vb:
                        findings.append(
                            finding(
                                "major",
                                "scope_gap",
                                f"nfr.json#{item.get('id')}/verified_by",
                                "in_scope NFR has empty verified_by while change status is done",
                            )
                        )
        missing_q = sorted(required_qualities - seen_q)
        if missing_q:
            findings.append(
                finding(
                    "major",
                    "scope_gap",
                    "nfr.json#items",
                    f"missing required qualities: {', '.join(missing_q)}",
                )
            )
    elif brief_path.is_file() or (change_dir / "change-context.md").is_file():
        findings.append(
            finding(
                "major",
                "scope_gap",
                str(nfr_path),
                "nfr.json missing (SoT for Change Context §4)",
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

        # Advisory: ready items with intersecting touches (orchestrator should serialize)
        ready_items: list[dict[str, Any]] = [
            it
            for it in items
            if isinstance(it, dict)
            and it.get("status") in (None, "ready", "pending", "running")
        ]
        ready_with_touches: list[tuple[str, set[str]]] = []
        for it in ready_items:
            touches = it.get("touches")
            if isinstance(touches, list) and touches:
                ready_with_touches.append(
                    (str(it.get("id", "?")), {str(t) for t in touches})
                )
        for i, (a_id, a_t) in enumerate(ready_with_touches):
            for b_id, b_t in ready_with_touches[i + 1 :]:
                overlap = sorted(a_t & b_t)
                if overlap:
                    findings.append(
                        finding(
                            "minor",
                            "consistency",
                            f"work-plan.json#items/{a_id},{b_id}/touches",
                            f"overlapping touches {overlap}; solidsdd-run must serialize these items",
                        )
                    )

        # Greenfield smell: ≥3 ready items, pairwise touches overlap, no depends_on edges
        ready_ids = {str(it.get("id")) for it in ready_items if it.get("id")}
        has_dep_edge = False
        for it in ready_items:
            for dep in it.get("depends_on") or []:
                if dep in ready_ids:
                    has_dep_edge = True
                    break
            if has_dep_edge:
                break
        if len(ready_with_touches) >= 3 and not has_dep_edge:
            # all pairs overlap?
            all_overlap = True
            for i, (_, a_t) in enumerate(ready_with_touches):
                for _, b_t in ready_with_touches[i + 1 :]:
                    if not (a_t & b_t):
                        all_overlap = False
                        break
                if not all_overlap:
                    break
            if all_overlap:
                findings.append(
                    finding(
                        "minor",
                        "consistency",
                        "work-plan.json#touches",
                        "≥3 items share intersecting touches with no depends_on among them; "
                        "prefer foundation→properties depends_on and narrower touches "
                        "(see work-decomposition greenfield guidance / docs/run-cost.md)",
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
            feature_tags = parse_feature_tags(project, lay.requirements_dir())
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
                            it.get("feature_path") or lay.requirements_glob,
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

    approval_path = change_dir / "gate-approval.json"
    if approval_path.is_file():
        appr = load_json(approval_path)
        validate_schema(appr, "gate-approval.schema.json", str(approval_path), findings)
        if appr.get("change_id") and appr["change_id"] != change_id:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    "gate-approval.json#change_id",
                    f"change_id {appr['change_id']!r} != directory {change_id!r}",
                )
            )
    hist_dir = change_dir / "gate-approvals"
    if hist_dir.is_dir():
        for path in sorted(hist_dir.glob("*.json")):
            data = load_json(path)
            validate_schema(data, "gate-approval.schema.json", str(path), findings)

    # Optional ArchitecturePlan under change dir
    arch_path = change_dir / "architecture-plan.json"
    if arch_path.is_file():
        arch = load_json(arch_path)
        validate_schema(
            arch, "architecture-plan.schema.json", str(arch_path), findings
        )
        if arch.get("change_id") and arch["change_id"] != change_id:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    "architecture-plan.json#change_id",
                    f"change_id {arch['change_id']!r} != directory {change_id!r}",
                )
            )
        if arch.get("status") == "changed":
            modules = arch.get("modules") or []
            module_ids = {
                m["id"] for m in modules if isinstance(m, dict) and "id" in m
            }
            dependencies = arch.get("dependencies") or []
            dep_edges: list[tuple[str, str]] = []
            for dep in dependencies:
                if not isinstance(dep, dict):
                    continue
                src, dst = dep.get("from"), dep.get("to")
                for role, mid in (("from", src), ("to", dst)):
                    if mid and mid not in module_ids:
                        findings.append(
                            finding(
                                "blocker",
                                "consistency",
                                "architecture-plan.json#dependencies",
                                f"dependency {role} references unknown module {mid!r}",
                            )
                        )
                if src and dst:
                    dep_edges.append((src, dst))

            forbidden: set[tuple[str, str]] = set()
            cycles_forbidden = False
            for constraint in arch.get("constraints") or []:
                if not isinstance(constraint, dict):
                    continue
                ctype = constraint.get("type")
                if ctype == "forbid_dependency":
                    cf, ct = constraint.get("from"), constraint.get("to")
                    for role, mid in (("from", cf), ("to", ct)):
                        if mid and mid not in module_ids:
                            findings.append(
                                finding(
                                    "blocker",
                                    "consistency",
                                    "architecture-plan.json#constraints",
                                    f"forbid_dependency {role} references unknown module {mid!r}",
                                )
                            )
                    if cf and ct:
                        forbidden.add((cf, ct))
                elif ctype == "no_cycles":
                    cycles_forbidden = True

            for src, dst in dep_edges:
                if (src, dst) in forbidden:
                    findings.append(
                        finding(
                            "blocker",
                            "consistency",
                            "architecture-plan.json#dependencies",
                            f"dependency {src} -> {dst} violates forbid_dependency constraint",
                        )
                    )

            if cycles_forbidden:
                for cycle in dependency_cycles(module_ids, dep_edges):
                    findings.append(
                        finding(
                            "major",
                            "consistency",
                            "architecture-plan.json#dependencies",
                            f"dependency cycle: {' -> '.join(cycle)}",
                        )
                    )

    # Optional ApplicationPlan / Verification under change dir or .solidsdd/
    for pattern, schema in (
        ("application-plan*.json", "application-plan.schema.json"),
        ("verification-report*.json", "verification-report.schema.json"),
        ("critique*.json", "critique-report.schema.json"),
    ):
        for path in list(change_dir.glob(pattern)) + list(
            lay.solidsdd_dir().glob(pattern)
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

    # Optional Architecture Model (.solidsdd/architecture/workspace.dsl + invariants.yaml).
    # Whole-project, persistent across changes; no-op when the directory doesn't exist.
    findings.extend(_architecture_validate.validate_project(lay))

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
    layout = load_layout(project)
    change_id, change_dir = _resolve_change_dir(project, args.change_id, layout=layout)
    findings = lint_change(project, change_id, change_dir, layout=layout)
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

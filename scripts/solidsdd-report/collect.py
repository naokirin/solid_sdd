"""Deterministic discovery/presence/coverage collector for solidsdd-report.

Reads existing change artifacts (Change Context, ChangeBrief, WorkPlan, nfr.json,
Features, ApplicationPlan(s), ArchitecturePlan, contracts) and emits a single
structured JSON blob: per-section Present/Not-performed state, a Brief-id
coverage matrix, and diagram-eligibility + node/edge data. The report-writing
agent uses this instead of re-deriving the same mechanical facts from a dozen
separate reads on every run (see change-report.md "Presence rules" /
"Diagrams").

This script never invents content — it only reports what exists. Judgment
prose (demand narrative, key judgments, natural-language contract summaries)
stays the caller's job.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from solidsdd_lib.paths import Layout, load_json, load_layout, resolve_change_dir  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

CONTEXT_HEADINGS: list[tuple[str, str]] = [
    ("1", "1. Demand and problem"),
    ("2", "2. Drivers and constraints"),
    ("3", "3. Functional intent"),
    ("4", "4. Non-functional requirements"),
    ("5", "5. Technology selection"),
    ("6", "6. Key judgments and trade-offs"),
    ("7", "7. Open questions"),
    ("8", "8. Links"),
]
_HEADING_RE = re.compile(r"^##\s+(\d+)\.\s+(.*)$", re.MULTILINE)

TAG_LINE = re.compile(r"^\s*(@[^\s]+(?:\s+@[^\s]+)*)\s*$")
COVER_TAG = re.compile(r"^@([A-Z][A-Z0-9]*[0-9]+)$")
SCENARIO_LINE = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.+?)\s*$", re.I)

STATUS_LABELS = {
    "en": {"present": "Present", "not_performed": "Not performed"},
    "ja": {"present": "実施済", "not_performed": "未実施"},
}


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _context_sections(text: str) -> dict[str, str]:
    """Split Change Context body by its fixed `## N. Title` headings."""
    matches = list(_HEADING_RE.finditer(text))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        num = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[num] = text[start:end].strip()
    return out


def _section_has_content(body: str | None) -> bool:
    if not body:
        return False
    stripped = body.strip()
    if not stripped:
        return False
    # A heading with only "N/A" / "none" / a bare dash is not real content.
    return not re.fullmatch(r"(?i)(n/?a|none|-|—)\.?", stripped)


def parse_feature_tags(requirements_dir: Path) -> dict[str, set[str]]:
    """Map scenario_name -> set of @R1-style cover tags (without @)."""
    mapping: dict[str, set[str]] = {}
    if not requirements_dir.is_dir():
        return mapping
    for path in sorted(requirements_dir.rglob("*.feature")):
        lines = path.read_text(encoding="utf-8").splitlines()
        pending: set[str] = set()
        for line in lines:
            tm = TAG_LINE.match(line)
            if tm:
                for tok in tm.group(1).split():
                    cm = COVER_TAG.match(tok)
                    if cm:
                        pending.add(cm.group(1))
                continue
            sm = SCENARIO_LINE.match(line)
            if sm:
                name = sm.group(1).strip()
                mapping.setdefault(name, set())
                mapping[name] |= pending
                pending = set()
    return mapping


def _feature_index(requirements_dir: Path) -> dict[str, str]:
    """Map scenario_name -> feature file path (project-relative-ish, first match wins)."""
    idx: dict[str, str] = {}
    if not requirements_dir.is_dir():
        return idx
    for path in sorted(requirements_dir.rglob("*.feature")):
        for line in path.read_text(encoding="utf-8").splitlines():
            sm = SCENARIO_LINE.match(line)
            if sm:
                name = sm.group(1).strip()
                idx.setdefault(name, str(path))
    return idx


def _scenario_block(feature_path: Path, scenario_name: str) -> str | None:
    """Extract the verbatim Scenario/Given-When-Then block (incl. tag lines).

    Lets render.py embed acceptance text verbatim (spec-allowed alternative
    to an LLM-authored paraphrase) instead of an agent re-typing it.
    """
    if not feature_path.is_file():
        return None
    lines = feature_path.read_text(encoding="utf-8").splitlines()
    start = None
    tag_start = None
    for i, line in enumerate(lines):
        if TAG_LINE.match(line):
            tag_start = i if tag_start is None or start is None else tag_start
            continue
        sm = SCENARIO_LINE.match(line)
        if sm and sm.group(1).strip() == scenario_name:
            start = i
            break
        if line.strip() == "" or not TAG_LINE.match(line):
            tag_start = None
    if start is None:
        return None
    block_start = tag_start if tag_start is not None else start
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].strip()
        if SCENARIO_LINE.match(lines[j]) or TAG_LINE.match(lines[j]):
            end = j
            break
        if stripped == "" and j + 1 < len(lines) and (
            SCENARIO_LINE.match(lines[j + 1]) or TAG_LINE.match(lines[j + 1])
        ):
            end = j
            break
    return "\n".join(lines[block_start:end]).rstrip()


def _application_plan_paths(layout: Layout, project_root: Path, change_id: str, change_dir: Path) -> list[Path]:
    found: list[Path] = []
    items_dir = change_dir / "items"
    if items_dir.is_dir():
        for p in sorted(items_dir.glob("*/application-plan.json")):
            found.append(p)
    if found:
        return found
    for p in sorted(change_dir.glob("application-plan*.json")):
        found.append(p)
    if found:
        return found
    solidsdd_dir = layout.solidsdd_dir()
    if solidsdd_dir.is_dir():
        for p in sorted(solidsdd_dir.glob("application-plan*.json")):
            try:
                data = load_json(p)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("change_id") == change_id:
                found.append(p)
    return found


def _ocl_paths(layout: Layout, project_root: Path) -> list[Path]:
    contracts_dir = layout.abs(layout.contracts)
    if not contracts_dir.is_dir():
        return []
    return sorted(contracts_dir.rglob("*.ocl"))


def _formal_paths(layout: Layout, project_root: Path) -> list[Path]:
    formal_dir = layout.abs(layout.formal)
    if not formal_dir.is_dir():
        return []
    return sorted(p for p in formal_dir.rglob("*") if p.is_file())


def _rel(project_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _resolve_language(project_root: Path, layout: Layout, context_sections: dict[str, str]) -> dict[str, str]:
    config_path = layout.solidsdd_dir() / "config.yaml"
    if config_path.is_file() and yaml is not None:
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        lang = data.get("working_language") if isinstance(data, dict) else None
        if isinstance(lang, str) and lang.strip():
            return {"value": lang.strip(), "source": "config.yaml"}
    judgments = context_sections.get("6", "")
    m = re.search(r"Working language:\s*([A-Za-z-]+)", judgments)
    if m:
        return {"value": m.group(1), "source": "change-context.md §6"}
    return {"value": "en", "source": "default"}


def collect(project_root_arg: Path, change_id: str | None) -> dict[str, Any]:
    layout = load_layout(project_root_arg)
    project_root = layout.project_root
    resolved_id, change_dir = resolve_change_dir(project_root, change_id, layout=layout, validate_change_id=True)
    sources: list[str] = []

    context_path = change_dir / "change-context.md"
    context_text = _read_text(context_path)
    context_sections = _context_sections(context_text) if context_text else {}
    if context_text is not None:
        sources.append(_rel(project_root, context_path))

    brief_path = change_dir / "change-brief.json"
    brief = load_json(brief_path) if brief_path.is_file() else None
    if brief is not None:
        sources.append(_rel(project_root, brief_path))

    work_plan_path = change_dir / "work-plan.json"
    work_plan = load_json(work_plan_path) if work_plan_path.is_file() else None
    if work_plan is not None:
        sources.append(_rel(project_root, work_plan_path))

    nfr_path = change_dir / "nfr.json"
    nfr = load_json(nfr_path) if nfr_path.is_file() else None
    if nfr is not None:
        sources.append(_rel(project_root, nfr_path))

    status_path = change_dir / "status.json"
    status = load_json(status_path) if status_path.is_file() else None

    run_state_path = change_dir / "run-state.json"
    run_state_exists = run_state_path.is_file()
    if run_state_exists:
        sources.append(_rel(project_root, run_state_path))

    # --- Features tied to this change -------------------------------------
    # Brief/WorkPlan ids (R1, SC1, ...) are only unique *within one Brief* —
    # a prior change's Feature file can reuse the same tag names by
    # coincidence (see change-report.md "Cross-change Feature files"). So we
    # never match ties by tag-id intersection alone; only two signals count:
    # (1) WorkPlan items' own feature_path/scenario_name (authoritative), and
    # (2) Feature paths explicitly named in Change Context §8 Links.
    requirements_dir = layout.requirements_dir()
    scenario_tags = parse_feature_tags(requirements_dir)
    scenario_file = {
        name: _rel(project_root, Path(path)) for name, path in _feature_index(requirements_dir).items()
    }

    tied_scenarios: dict[str, dict[str, Any]] = {}
    if work_plan:
        for item in work_plan.get("items") or []:
            name = item.get("scenario_name")
            if isinstance(name, str) and name:
                rel_feature_path = item.get("feature_path") or scenario_file.get(name)
                gherkin = None
                if rel_feature_path:
                    gherkin = _scenario_block(layout.abs(rel_feature_path), name)
                tied_scenarios[name] = {
                    "name": name,
                    "tags": sorted(scenario_tags.get(name, set())),
                    "feature_path": rel_feature_path,
                    "gherkin": gherkin,
                }

    links_text = context_sections.get("8", "")
    linked_feature_paths = set(re.findall(r"[\w./-]+\.feature", links_text))
    if linked_feature_paths:
        for rel_path in sorted(linked_feature_paths):
            abs_path = layout.abs(rel_path)
            if not abs_path.is_file():
                continue
            for line in abs_path.read_text(encoding="utf-8").splitlines():
                sm = SCENARIO_LINE.match(line)
                if sm:
                    name = sm.group(1).strip()
                    tied_scenarios.setdefault(
                        name,
                        {
                            "name": name,
                            "tags": sorted(scenario_tags.get(name, set())),
                            "gherkin": _scenario_block(abs_path, name),
                            "feature_path": _rel(project_root, abs_path),
                        },
                    )
    if tied_scenarios:
        for info in tied_scenarios.values():
            if info.get("feature_path"):
                sources.append(info["feature_path"])

    # --- Coverage matrix -----------------------------------------------------
    coverage_matrix: list[dict[str, Any]] = []
    if brief:
        work_items = (work_plan or {}).get("items") or []
        for key in ("in_scope", "success_criteria"):
            for item in brief.get(key) or []:
                if not isinstance(item, dict):
                    continue
                bid = item.get("id")
                text = item.get("text")
                covered_by = [
                    wi.get("id") for wi in work_items if bid in (wi.get("covers") or [])
                ]
                scenarios = [
                    {"name": wi.get("scenario_name"), "tags": sorted(scenario_tags.get(wi.get("scenario_name") or "", set()))}
                    for wi in work_items
                    if bid in (wi.get("covers") or []) and wi.get("scenario_name")
                ]
                coverage_matrix.append(
                    {
                        "id": bid,
                        "text": text,
                        "kind": "in_scope" if key == "in_scope" else "success_criteria",
                        "covered_by": covered_by,
                        "scenarios": scenarios,
                        "uncovered": not covered_by,
                    }
                )

    # --- ApplicationPlan discovery -------------------------------------------
    app_plan_paths = _application_plan_paths(layout, project_root, resolved_id, change_dir)
    application_plans: list[dict[str, Any]] = []
    for p in app_plan_paths:
        try:
            data = load_json(p)
        except (OSError, json.JSONDecodeError):
            continue
        application_plans.append({"path": _rel(project_root, p), "data": data})
        sources.append(_rel(project_root, p))

    # --- ArchitecturePlan / reasoning / physical design -----------------------
    arch_plan_path = change_dir / "architecture-plan.json"
    architecture_plan = load_json(arch_plan_path) if arch_plan_path.is_file() else None
    if architecture_plan is not None:
        sources.append(_rel(project_root, arch_plan_path))

    reasoning_path = change_dir / "architecture-reasoning.md"
    reasoning_exists = reasoning_path.is_file()
    if reasoning_exists:
        sources.append(_rel(project_root, reasoning_path))

    physical_design_path = change_dir / "physical-design.md"
    physical_design_exists = physical_design_path.is_file()
    if physical_design_exists:
        sources.append(_rel(project_root, physical_design_path))

    # --- Contracts -------------------------------------------------------------
    openapi_path = layout.openapi_path()
    openapi_exists = openapi_path.is_file()
    if openapi_exists:
        sources.append(_rel(project_root, openapi_path))

    graphql_path = layout.abs(layout.graphql)
    graphql_exists = graphql_path.is_file()
    if graphql_exists:
        sources.append(_rel(project_root, graphql_path))

    ocl_paths = _ocl_paths(layout, project_root)
    sources.extend(_rel(project_root, p) for p in ocl_paths)

    formal_paths = _formal_paths(layout, project_root)
    sources.extend(_rel(project_root, p) for p in formal_paths)

    # --- Presence rules ----------------------------------------------------
    demand_present = _section_has_content(context_sections.get("1"))
    functional_present = bool(brief) or bool(tied_scenarios)
    nfr_present = bool(nfr and nfr.get("items")) or _section_has_content(context_sections.get("4"))
    technology_present = _section_has_content(context_sections.get("5"))
    work_plan_present = bool(work_plan and work_plan.get("items"))
    architecture_present = architecture_plan is not None
    application_present = bool(application_plans)
    api_present = openapi_exists or graphql_exists
    dbc_present = bool(ocl_paths)
    formal_present = bool(formal_paths)
    judgments_present = _section_has_content(context_sections.get("6"))
    open_questions_present = _section_has_content(context_sections.get("7")) or bool(
        brief and brief.get("open_questions")
    )

    def state(flag: bool) -> str:
        return "present" if flag else "not_performed"

    sections = {
        "demand": {"state": state(demand_present), "owning_skill": "solidsdd-intake"},
        "functional_requirements": {"state": state(functional_present), "owning_skill": "solidsdd-brief / solidsdd-decompose"},
        "non_functional_requirements": {"state": state(nfr_present), "owning_skill": "solidsdd-intake"},
        "technology_selection": {"state": state(technology_present), "owning_skill": "solidsdd-intake"},
        "design": {
            "work_plan": {"state": state(work_plan_present), "owning_skill": "solidsdd-decompose"},
            "architecture_plan": {
                "state": state(architecture_present),
                "status": architecture_plan.get("status") if architecture_plan else None,
                "owning_skill": "solidsdd-architecture",
            },
            "application_plan": {"state": state(application_present), "owning_skill": "solidsdd-judge"},
            "api_contract": {"state": state(api_present), "owning_skill": "solidsdd-apply-api"},
            "dbc": {"state": state(dbc_present), "owning_skill": "solidsdd-apply-dbc"},
            "formal": {"state": state(formal_present), "owning_skill": "solidsdd-apply-formal"},
        },
        "key_judgments": {"state": state(judgments_present), "owning_skill": "solidsdd-intake"},
        "open_questions": {"state": state(open_questions_present)},
    }

    # --- Diagram eligibility -------------------------------------------------
    diagrams: dict[str, Any] = {}

    if architecture_plan and architecture_plan.get("status") == "changed":
        modules = architecture_plan.get("modules") or []
        diagrams["architecture"] = {
            "eligible": len(modules) >= 2,
            "nodes": [
                {"id": m.get("id"), "label": m.get("responsibility")} for m in modules
            ],
            "edges": [
                {"from": d.get("from"), "to": d.get("to"), "kind": d.get("kind"), "reason": d.get("reason")}
                for d in (architecture_plan.get("dependencies") or [])
            ],
            "forbidden_edges": [
                {"from": c.get("from"), "to": c.get("to"), "reason": c.get("reason")}
                for c in (architecture_plan.get("constraints") or [])
                if c.get("type") == "forbid_dependency"
            ],
            "no_cycles": any(
                c.get("type") == "no_cycles" for c in (architecture_plan.get("constraints") or [])
            ),
        }
    else:
        diagrams["architecture"] = {"eligible": False}

    if work_plan:
        items = work_plan.get("items") or []
        edges = [
            {"from": it.get("id"), "to": dep}
            for it in items
            for dep in (it.get("depends_on") or [])
        ]
        diagrams["work_plan"] = {
            "eligible": len(items) >= 2 and bool(edges),
            "nodes": [{"id": it.get("id"), "label": it.get("intent")} for it in items],
            "edges": edges,
        }
    else:
        diagrams["work_plan"] = {"eligible": False}

    if application_plans:
        targets: list[dict[str, Any]] = []
        for plan in application_plans:
            for t in plan["data"].get("targets") or []:
                targets.append(t)
        distinct_pairs = {(t.get("kind"), t.get("location")) for t in targets}
        distinct_kinds = {t.get("kind") for t in targets}
        left_ids: set[str] = set()
        edges = []
        for t in targets:
            covers = t.get("covers") or []
            if not covers and brief:
                covers = [i.get("id") for i in (brief.get("in_scope") or []) if isinstance(i, dict)]
            pair = (t.get("kind"), t.get("location"))
            for cid in covers:
                left_ids.add(cid)
                edges.append({"from": cid, "to": pair, "status": t.get("status"), "density": t.get("density")})
        diagrams["application_plan"] = {
            "eligible": len(distinct_pairs) >= 3 or len(distinct_kinds) >= 2,
            "left_nodes": sorted(left_ids),
            "right_nodes": [
                {"kind": k, "location": loc} for (k, loc) in sorted(distinct_pairs, key=lambda p: (p[0] or "", p[1] or ""))
            ],
            "edges": edges,
        }
    else:
        diagrams["application_plan"] = {"eligible": False}

    language = _resolve_language(project_root, layout, context_sections)

    return {
        "version": "1",
        "change_id": resolved_id,
        "status": status,
        "language_hint": language,
        "status_labels": STATUS_LABELS.get(language["value"], STATUS_LABELS["en"]),
        "sections": sections,
        "coverage_matrix": coverage_matrix,
        "diagrams": diagrams,
        "artifacts": {
            "change_context_path": _rel(project_root, context_path) if context_text is not None else None,
            "change_context_sections": {
                num: {"has_content": _section_has_content(body), "text": body}
                for num, body in context_sections.items()
            },
            "brief_path": _rel(project_root, brief_path) if brief is not None else None,
            "brief": brief,
            "work_plan_path": _rel(project_root, work_plan_path) if work_plan is not None else None,
            "work_plan": work_plan,
            "nfr_path": _rel(project_root, nfr_path) if nfr is not None else None,
            "nfr": nfr,
            "tied_scenarios": list(tied_scenarios.values()),
            "application_plans": application_plans,
            "architecture_plan_path": _rel(project_root, arch_plan_path) if architecture_plan is not None else None,
            "architecture_plan": architecture_plan,
            "architecture_reasoning_path": _rel(project_root, reasoning_path) if reasoning_exists else None,
            "physical_design_path": _rel(project_root, physical_design_path) if physical_design_exists else None,
            "openapi_path": _rel(project_root, openapi_path) if openapi_exists else None,
            "graphql_path": _rel(project_root, graphql_path) if graphql_exists else None,
            "ocl_paths": [_rel(project_root, p) for p in ocl_paths],
            "formal_paths": [_rel(project_root, p) for p in formal_paths],
            "run_state_path": _rel(project_root, run_state_path) if run_state_exists else None,
        },
        "source_artifacts": sorted(set(sources)),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Collect structured report data for solidsdd-report")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--change-id", default=None)
    parser.add_argument("--out", help="Write to this path instead of stdout")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    data = collect(Path(args.project_root), args.change_id)
    indent = 2 if args.pretty else None
    text = json.dumps(data, indent=indent, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + ("\n" if args.pretty else ""), encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

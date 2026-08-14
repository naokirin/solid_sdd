"""Validation for the Architecture Model (workspace.dsl + invariants.yaml).

Implements the mechanical checks from solidsdd-architecture's design spec:

  - DSL syntax (dsl.DslSyntaxError)
  - invariants.yaml schema validity
  - model consistency / referenced element existence (relationships, views)
  - relationship validity (no self-loops)
  - solid_sdd-specific: forbidden dependency actually present, no_cycles
    cycle detection, ownership conflicts, internal-component boundary
    leakage

Findings use the same shape as scripts/solidsdd-lint/lint.py's `finding()`:
{"severity", "category", "location", "detail"}, so callers can fold this
module's findings directly into an existing findings list.

Prose `invariants[]` entries in invariants.yaml are NOT mechanically
verified here (natural language) — only `constraints[]` are.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from solidsdd_lib.paths import Layout, load_layout  # noqa: E402

import dsl as dslmod  # noqa: E402

ROOT = _SCRIPTS.parent
SCHEMAS = ROOT / "schemas"


def finding(severity: str, category: str, location: str, detail: str) -> dict[str, str]:
    return {"severity": severity, "category": category, "location": location, "detail": detail}


def _load_yaml(path: Path) -> Any:
    if yaml is None:
        raise SystemExit("solidsdd-architecture requires the PyYAML package")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _top_level_ancestor(ws: dslmod.Workspace, element_id: str) -> str:
    elem = ws.elements[element_id]
    while elem.parent_id is not None:
        elem = ws.elements[elem.parent_id]
    return elem.id


def _is_ancestor(ws: dslmod.Workspace, ancestor_id: str, element_id: str) -> bool:
    elem = ws.elements.get(element_id)
    while elem is not None:
        if elem.id == ancestor_id:
            return True
        elem = ws.elements.get(elem.parent_id) if elem.parent_id else None
    return False


def _dependency_cycles(element_ids: set[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    graph: dict[str, list[str]] = {e: [] for e in element_ids}
    for src, dst in edges:
        if src in graph and dst in element_ids:
            graph[src].append(dst)
    cycles: list[list[str]] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {e: WHITE for e in element_ids}
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

    for node in element_ids:
        if color[node] == WHITE:
            dfs(node)
    return cycles


def parse_workspace(workspace_path: Path, findings: list[dict[str, str]]) -> dslmod.Workspace | None:
    try:
        return dslmod.parse_file(workspace_path)
    except dslmod.DslSyntaxError as e:
        findings.append(
            finding(
                "blocker",
                "schema_violation",
                f"{workspace_path}#L{e.line}",
                e.message,
            )
        )
        return None


def load_invariants(
    invariants_path: Path, findings: list[dict[str, str]]
) -> dict[str, Any] | None:
    if not invariants_path.is_file():
        return {"version": "1", "constraints": [], "invariants": []}
    data = _load_yaml(invariants_path)
    if data is None:
        data = {}
    if Draft202012Validator is not None:
        schema_path = SCHEMAS / "architecture-invariants.schema.json"
        if schema_path.is_file():
            import json

            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema)
            errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
            for err in errors:
                path = "/".join(str(p) for p in err.absolute_path) or "(root)"
                findings.append(
                    finding(
                        "blocker",
                        "schema_violation",
                        f"{invariants_path}#{path}",
                        err.message,
                    )
                )
            if errors:
                return None
    return data


def _check_model_consistency(
    ws: dslmod.Workspace, findings: list[dict[str, str]], location: str
) -> None:
    for rel in ws.relationships:
        if rel.source not in ws.elements:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    f"{location}#L{rel.line}",
                    f"relationship references unknown element {rel.source!r}",
                )
            )
        if rel.dest not in ws.elements:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    f"{location}#L{rel.line}",
                    f"relationship references unknown element {rel.dest!r}",
                )
            )
        if rel.source == rel.dest:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    f"{location}#L{rel.line}",
                    f"relationship {rel.source} -> {rel.dest} is a self-loop",
                )
            )

    for view in ws.views:
        if view.element_id not in ws.elements:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    f"{location}#L{view.line}",
                    f"view references unknown element {view.element_id!r}",
                )
            )
        for inc in view.include_ids:
            if inc not in ws.elements:
                findings.append(
                    finding(
                        "blocker",
                        "consistency",
                        f"{location}#L{view.line}",
                        f"view include references unknown element {inc!r}",
                    )
                )


def _check_boundary_leakage(
    ws: dslmod.Workspace, findings: list[dict[str, str]], location: str
) -> None:
    for rel in ws.relationships:
        dest = ws.elements.get(rel.dest)
        if dest is None or dest.kind != "component":
            continue
        container_id = dest.parent_id
        if container_id is None:
            continue
        is_public = any(t.lower() == "public" for t in dest.tags)
        if is_public:
            continue
        if _is_ancestor(ws, container_id, rel.source):
            continue
        findings.append(
            finding(
                "major",
                "consistency",
                f"{location}#L{rel.line}",
                f'relationship {rel.source} -> {rel.dest} depends on an internal '
                f'component outside its container; tag {rel.dest} "Public" if this '
                "is an intentional public boundary",
            )
        )


def _check_ownership_conflicts(
    ws: dslmod.Workspace, findings: list[dict[str, str]], location: str
) -> None:
    owners: dict[str, list[str]] = {}
    for elem in ws.elements.values():
        owns_raw = elem.properties.get("owns")
        if not owns_raw:
            continue
        for thing in (p.strip() for p in owns_raw.split(",")):
            if not thing:
                continue
            owners.setdefault(thing, []).append(elem.id)
    for thing, owner_ids in owners.items():
        if len(owner_ids) > 1:
            findings.append(
                finding(
                    "major",
                    "consistency",
                    f"{location}#model",
                    f"ownership conflict: {thing!r} is claimed by both "
                    f"{' and '.join(sorted(set(owner_ids)))}",
                )
            )


def _check_invariant_constraints(
    ws: dslmod.Workspace,
    invariants: dict[str, Any],
    findings: list[dict[str, str]],
    ws_location: str,
    inv_location: str,
) -> None:
    forbidden: set[tuple[str, str]] = set()
    cycles_forbidden = False
    for constraint in invariants.get("constraints") or []:
        if not isinstance(constraint, dict):
            continue
        ctype = constraint.get("type")
        if ctype == "forbid_dependency":
            cf, ct = constraint.get("from"), constraint.get("to")
            for role, eid in (("from", cf), ("to", ct)):
                if eid and eid not in ws.elements:
                    findings.append(
                        finding(
                            "blocker",
                            "consistency",
                            f"{inv_location}#constraints",
                            f"forbid_dependency {role} references unknown element {eid!r}",
                        )
                    )
            if cf and ct:
                forbidden.add((cf, ct))
        elif ctype == "no_cycles":
            cycles_forbidden = True

    for rel in ws.relationships:
        if (rel.source, rel.dest) in forbidden:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    f"{ws_location}#L{rel.line}",
                    f"dependency {rel.source} -> {rel.dest} violates forbid_dependency "
                    "constraint",
                )
            )

    if cycles_forbidden:
        edges = [(r.source, r.dest) for r in ws.relationships]
        for cycle in _dependency_cycles(set(ws.elements), edges):
            findings.append(
                finding(
                    "major",
                    "consistency",
                    f"{ws_location}#model",
                    f"dependency cycle: {' -> '.join(cycle)}",
                )
            )


def validate(workspace_path: Path, invariants_path: Path) -> list[dict[str, str]]:
    """Validate an Architecture Model. Returns a list of findings (possibly empty)."""
    findings: list[dict[str, str]] = []
    ws_location = str(workspace_path)
    inv_location = str(invariants_path)

    ws = parse_workspace(workspace_path, findings)
    invariants = load_invariants(invariants_path, findings)

    if ws is None:
        return findings

    _check_model_consistency(ws, findings, ws_location)
    _check_boundary_leakage(ws, findings, ws_location)
    _check_ownership_conflicts(ws, findings, ws_location)

    if invariants is not None:
        _check_invariant_constraints(ws, invariants, findings, ws_location, inv_location)

    return findings


def validate_project(layout: Layout) -> list[dict[str, str]]:
    """No-op (empty findings) when the project has no Architecture Model yet."""
    arch_dir = layout.architecture_dir()
    workspace_path = arch_dir / "workspace.dsl"
    if not workspace_path.is_file():
        return []
    invariants_path = arch_dir / "invariants.yaml"
    return validate(workspace_path, invariants_path)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json as jsonmod

    parser = argparse.ArgumentParser(description="Validate the Architecture Model")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    layout = load_layout(Path(args.project_root))
    findings = validate_project(layout)
    indent = 2 if args.pretty else None
    print(jsonmod.dumps({"findings": findings}, indent=indent, ensure_ascii=False))
    return 1 if any(f["severity"] in ("blocker", "major") for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

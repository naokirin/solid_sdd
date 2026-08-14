"""Project ArchitecturePlan JSON from the Architecture Model.

Structurizr DSL (workspace.dsl) + invariants.yaml are the Source of Truth
for structure. `architecture-plan.json` (schemas/architecture-plan.schema.json,
unchanged) is kept as a deterministic, generated *projection* of that model
for the change_id given — a change-level delta view for existing consumers
(scripts/solidsdd-lint/lint.py, solidsdd-critique, solidsdd-report).

Elements/relationships belonging to a change are tagged `change:<change_id>`
in workspace.dsl (existing tags are preserved, not replaced). `modules[]`
also includes any element referenced by a touched relationship or an
emitted constraint, even if not itself tagged, so `dependencies[]`/
`constraints[]` from/to always resolve within `modules[]` (required by
lint.py). `human_gate` is not computed here — the agent adds it to the
generated file per reference-src/human-gates.md when required.

Known limitation: this is additive-only. Deletions/renames of elements or
relationships are not reflected in the projection; note them in
architecture-reasoning.md instead.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from solidsdd_lib.paths import Layout, load_layout  # noqa: E402

import dsl as dslmod  # noqa: E402
from validate import load_invariants  # noqa: E402

_KIND_TAG_RE = re.compile(r"^kind:(runtime|data|event|api)$")


def _to_module_id(dsl_id: str) -> str:
    return dsl_id.replace("_", "-")


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def _change_tag(change_id: str) -> str:
    return f"change:{change_id}"


def project(
    ws: dslmod.Workspace, invariants: dict[str, Any], change_id: str
) -> dict[str, Any]:
    tag = _change_tag(change_id)
    touched_ids = {e.id for e in ws.elements.values() if tag in e.tags}
    touched_rels = [r for r in ws.relationships if tag in r.tags]

    referenced_ids: set[str] = set(touched_ids)
    for r in touched_rels:
        referenced_ids.add(r.source)
        referenced_ids.add(r.dest)

    emitted_constraints: list[dict[str, Any]] = []
    for constraint in invariants.get("constraints") or []:
        if not isinstance(constraint, dict):
            continue
        ctype = constraint.get("type")
        if ctype == "no_cycles":
            emitted_constraints.append({"type": "no_cycles"})
        elif ctype == "forbid_dependency":
            cf, ct = constraint.get("from"), constraint.get("to")
            if cf in referenced_ids or ct in referenced_ids:
                entry: dict[str, Any] = {
                    "type": "forbid_dependency",
                    "from": _to_module_id(cf) if cf else cf,
                    "to": _to_module_id(ct) if ct else ct,
                }
                if constraint.get("reason"):
                    entry["reason"] = constraint["reason"]
                emitted_constraints.append(entry)
                if cf:
                    referenced_ids.add(cf)
                if ct:
                    referenced_ids.add(ct)

    if not referenced_ids and not emitted_constraints:
        return {
            "version": "1",
            "status": "unchanged",
            "change_id": change_id,
            "summary": (
                f"No Architecture Model elements or relationships tagged "
                f"{tag!r}; structure unchanged."
            ),
        }

    modules = []
    for eid in sorted(referenced_ids):
        elem = ws.elements.get(eid)
        if elem is None:
            continue
        module: dict[str, Any] = {
            "id": _to_module_id(eid),
            "responsibility": elem.description or elem.name,
        }
        owns = _split_csv(elem.properties.get("owns"))
        if owns:
            module["owns"] = owns
        public = _split_csv(elem.properties.get("public"))
        if public:
            module["public"] = public
        modules.append(module)

    dependencies = []
    for r in touched_rels:
        dep: dict[str, Any] = {
            "from": _to_module_id(r.source),
            "to": _to_module_id(r.dest),
        }
        if r.description:
            dep["reason"] = r.description
        for t in r.tags:
            m = _KIND_TAG_RE.match(t)
            if m:
                dep["kind"] = m.group(1)
                break
        dependencies.append(dep)

    return {
        "version": "1",
        "status": "changed",
        "change_id": change_id,
        "summary": (
            f"Projected from workspace.dsl + invariants.yaml for change "
            f"{change_id!r}: {len(modules)} module(s), {len(dependencies)} "
            f"dependency edge(s), {len(emitted_constraints)} constraint(s)."
        ),
        "modules": modules,
        "dependencies": dependencies,
        "constraints": emitted_constraints,
    }


def project_project_root(project_root: Path, change_id: str) -> dict[str, Any]:
    layout: Layout = load_layout(project_root)
    arch_dir = layout.architecture_dir()
    workspace_path = arch_dir / "workspace.dsl"
    invariants_path = arch_dir / "invariants.yaml"
    if not workspace_path.is_file():
        return {
            "version": "1",
            "status": "unchanged",
            "change_id": change_id,
            "summary": "No .solidsdd/architecture/workspace.dsl; structure unchanged.",
        }
    ws = dslmod.parse_file(workspace_path)
    findings: list[dict[str, str]] = []
    invariants = load_invariants(invariants_path, findings) or {}
    return project(ws, invariants, change_id)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json as jsonmod

    parser = argparse.ArgumentParser(
        description="Project ArchitecturePlan JSON from the Architecture Model"
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--change-id", required=True)
    parser.add_argument("--out", help="Write to this path instead of stdout")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    plan = project_project_root(Path(args.project_root), args.change_id)
    indent = 2 if args.pretty else None
    text = jsonmod.dumps(plan, indent=indent, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + ("\n" if args.pretty else ""), encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Best-effort cross-checks between physical-design.md and the Architecture Model.

`physical-design.md` (see reference-src/physical-design.md) is free-form,
change-local reasoning — not a second Source of Truth, and not parsed by a
strict grammar the way `workspace.dsl` is. This module extracts only the
handful of conventions the template documents (a "## Logical Elements"
bullet list, a "## Physical Realization" table, and `A -> B` lines under
"## Physical Dependencies") and, when present, cross-checks them against the
already-validated Architecture Model. Anything that doesn't match those
conventions is silently skipped rather than treated as a syntax error —
prose stays prose; only what the agent chose to state in a checkable shape
gets checked.

Two checks:
  - Logical / Physical consistency: every Logical Element named in
    `physical-design.md` resolves to an element in `workspace.dsl` (catches
    typos / stale references after a rename).
  - Physical dependency vs. `forbid_dependency`: a declared `A -> B` Physical
    Dependency line, resolved back to Logical element ids via the Physical
    Realization table, is checked against `invariants.yaml`'s
    `forbid_dependency` constraints and against the declared Logical
    dependency direction — the same mechanism already used for Logical
    relationships in `workspace.dsl`, not a new constraint type.

Does not perform static analysis of actual source code (import graphs,
directory conventions) — only what the agent declared in
`physical-design.md` is checked. That is an intentional scope limit, not a
gap: see "Important Constraint" in the Architecture Validation design —
semantic/code-level judgment stays with critique / review.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import dsl as dslmod  # noqa: E402
from validate import finding, load_invariants, parse_workspace  # noqa: E402

_LOGICAL_ELEMENTS_HEADING = re.compile(r"^#{2,6}\s*Logical Elements\s*$", re.IGNORECASE)
_PHYSICAL_REALIZATION_HEADING = re.compile(r"^#{2,6}\s*Physical Realization\s*$", re.IGNORECASE)
_PHYSICAL_DEPENDENCIES_HEADING = re.compile(r"^#{2,6}\s*Physical Dependencies\s*$", re.IGNORECASE)
_ANY_HEADING = re.compile(r"^#{1,6}\s")
_BULLET = re.compile(r"^\s*-\s+(.+?)\s*$")
_TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
_ARROW_LINE = re.compile(r"^\s*-?\s*(\S+)\s*->\s*(\S+)\s*$")


def _section_lines(lines: list[str], heading_re: re.Pattern[str]) -> list[str]:
    out: list[str] = []
    in_section = False
    for line in lines:
        if heading_re.match(line):
            in_section = True
            continue
        if in_section:
            if _ANY_HEADING.match(line):
                break
            out.append(line)
    return out


def _parse_bullets(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        m = _BULLET.match(line)
        if m:
            out.append(m.group(1).strip("`"))
    return out


def _parse_table(lines: list[str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in lines:
        m = _TABLE_ROW.match(line)
        if not m:
            continue
        cells = [c.strip().strip("`") for c in m.group(1).split("|")]
        if len(cells) < 2:
            continue
        left, right = cells[0], cells[1]
        if not left or set(left) <= {"-", ":"}:
            continue  # header separator row
        if left.lower() in ("logical element",):
            continue  # header row
        rows.append((left, right))
    return rows


def _parse_arrows(lines: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for line in lines:
        m = _ARROW_LINE.match(line)
        if m:
            out.append((m.group(1).strip("`"), m.group(2).strip("`")))
    return out


def _resolve_element(ws: dslmod.Workspace, ref: str) -> dslmod.Element | None:
    ref_norm = ref.strip().strip("`")
    for elem in ws.elements.values():
        if elem.id == ref_norm or elem.name == ref_norm:
            return elem
    low = ref_norm.lower()
    for elem in ws.elements.values():
        if elem.id.lower() == low or elem.name.lower() == low:
            return elem
    return None


def validate_physical_design(
    physical_design_path: Path,
    ws: dslmod.Workspace | None,
    invariants: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Core check: given an already-parsed Workspace/invariants, validate one
    physical-design.md file. Returns findings (possibly empty)."""
    findings: list[dict[str, str]] = []
    if not physical_design_path.is_file():
        return findings
    location = str(physical_design_path)

    if ws is None:
        findings.append(
            finding(
                "major",
                "consistency",
                location,
                "physical-design.md exists but .solidsdd/architecture/workspace.dsl "
                "is missing or has a syntax error; Logical Elements referenced here "
                "cannot be cross-checked",
            )
        )
        return findings

    lines = physical_design_path.read_text(encoding="utf-8").splitlines()

    logical_names = set(_parse_bullets(_section_lines(lines, _LOGICAL_ELEMENTS_HEADING)))
    realization_rows = _parse_table(_section_lines(lines, _PHYSICAL_REALIZATION_HEADING))
    for name, _path in realization_rows:
        logical_names.add(name)

    for name in sorted(logical_names):
        if _resolve_element(ws, name) is None:
            findings.append(
                finding(
                    "major",
                    "consistency",
                    location,
                    f"Logical Element {name!r} referenced in physical-design.md "
                    "not found in workspace.dsl",
                )
            )

    # physical path -> Logical element, for resolving Physical Dependency lines
    path_to_logical: dict[str, dslmod.Element] = {}
    for name, path in realization_rows:
        elem = _resolve_element(ws, name)
        if elem is not None and path:
            path_to_logical[path] = elem

    forbidden: set[tuple[str, str]] = set()
    if invariants:
        for constraint in invariants.get("constraints") or []:
            if isinstance(constraint, dict) and constraint.get("type") == "forbid_dependency":
                cf, ct = constraint.get("from"), constraint.get("to")
                if cf and ct:
                    forbidden.add((cf, ct))

    logical_rel_pairs = {(r.source, r.dest) for r in ws.relationships}

    dep_lines = _section_lines(lines, _PHYSICAL_DEPENDENCIES_HEADING)
    for phys_a, phys_b in _parse_arrows(dep_lines):
        elem_a = path_to_logical.get(phys_a) or _resolve_element(ws, phys_a)
        elem_b = path_to_logical.get(phys_b) or _resolve_element(ws, phys_b)
        if elem_a is None or elem_b is None:
            continue  # not resolvable to a known Logical element; prose, not a checkable fact
        if (elem_a.id, elem_b.id) in forbidden:
            findings.append(
                finding(
                    "blocker",
                    "consistency",
                    location,
                    f"physical dependency {phys_a} -> {phys_b} resolves to Logical "
                    f"dependency {elem_a.id} -> {elem_b.id}, which violates a "
                    "forbid_dependency constraint in invariants.yaml",
                )
            )
        elif (
            (elem_b.id, elem_a.id) in logical_rel_pairs
            and (elem_a.id, elem_b.id) not in logical_rel_pairs
        ):
            findings.append(
                finding(
                    "major",
                    "consistency",
                    location,
                    f"physical dependency {phys_a} -> {phys_b} (Logical "
                    f"{elem_a.id} -> {elem_b.id}) is opposite the declared Logical "
                    f"dependency direction {elem_b.id} -> {elem_a.id} in workspace.dsl",
                )
            )

    return findings


def validate_physical_design_project(layout: Any, change_dir: Path) -> list[dict[str, str]]:
    """No-op when the change has no physical-design.md."""
    physical_design_path = change_dir / "physical-design.md"
    if not physical_design_path.is_file():
        return []
    arch_dir = layout.architecture_dir()
    ws_path = arch_dir / "workspace.dsl"
    ws = parse_workspace(ws_path, []) if ws_path.is_file() else None
    invariants = load_invariants(arch_dir / "invariants.yaml", [])
    return validate_physical_design(physical_design_path, ws, invariants)

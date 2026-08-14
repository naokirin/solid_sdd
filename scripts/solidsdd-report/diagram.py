"""Deterministic diagram rendering for solidsdd-report.

Turns the node/edge data collect.py already extracted from ArchitecturePlan /
WorkPlan / ApplicationPlan (or, for Formal specs, data the caller supplies
after reading the .tla/.als source) into:

- Mermaid source text (flowchart LR / stateDiagram-v2) — always produced.
- A hand-laid-out inline SVG — produced only while the node/edge count stays
  small enough to lay out legibly (see change-report.md "Diagrams" /
  "HTML rendering"); beyond that this returns svg: null and the caller keeps
  the Mermaid source only, exactly as the spec already allows.

This removes the need for an LLM to compute box/arrow coordinates by hand —
the geometry here is a fixed, tested formula, not a judgment call.
"""
from __future__ import annotations

import html
import json
import re
from typing import Any

_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9_]")

MAX_ROW_NODES = 8  # dependency graph / state diagram: skip SVG above this
MAX_TARGET_NODES = 8  # target mapping: skip SVG above this many total nodes
MAX_STATE_NODES = 5  # state diagram: single-row/loop layout ceiling

FORBIDDEN_COLOR = "#ff6b6b"
ACCENT_COLOR = "var(--accent, #4dabf7)"
TEXT_COLOR = "currentColor"


def _mermaid_id(raw: str) -> str:
    return _ID_SAFE_RE.sub("_", raw)


def _esc(text: Any) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


def _short(text: Any, limit: int = 40) -> str:
    s = str(text or "")
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Dependency graph (ArchitecturePlan modules, WorkPlan items)
# ---------------------------------------------------------------------------


def mermaid_dependency_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    forbidden_edges: list[dict[str, Any]] | None = None,
) -> str:
    forbidden_edges = forbidden_edges or []
    lines = ["flowchart LR"]
    for n in nodes:
        nid = _mermaid_id(str(n["id"]))
        label = str(n["id"])
        if n.get("label"):
            label += f"<br/>{_short(n['label'])}"
        lines.append(f'  {nid}["{label}"]')
    edge_lines: list[str] = []
    style_lines: list[str] = []
    idx = 0
    for e in edges:
        a, b = _mermaid_id(str(e["from"])), _mermaid_id(str(e["to"]))
        label = f"|{e['kind']}|" if e.get("kind") else ""
        edge_lines.append(f"  {a} -->{label} {b}")
        idx += 1
    for e in forbidden_edges:
        a, b = _mermaid_id(str(e["from"])), _mermaid_id(str(e["to"]))
        edge_lines.append(f"  {a} -.->|forbidden| {b}")
        style_lines.append(f"  linkStyle {idx} stroke:{FORBIDDEN_COLOR},stroke-dasharray: 4 2")
        idx += 1
    lines.extend(edge_lines)
    lines.extend(style_lines)
    if not edges and not forbidden_edges:
        lines.append("  %% no dependency edges among these modules")
    return "\n".join(lines)


def svg_dependency_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    forbidden_edges: list[dict[str, Any]] | None = None,
) -> str | None:
    forbidden_edges = forbidden_edges or []
    if len(nodes) < 1 or len(nodes) > MAX_ROW_NODES:
        return None
    box_w, box_h, gap, pad_top, pad_side = 140, 44, 60, 40, 20
    n = len(nodes)
    width = pad_side * 2 + n * box_w + max(0, n - 1) * gap
    height = pad_top * 2 + box_h + 60  # room for a curved forbidden edge above
    xs = {}
    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Module dependency diagram">'
    ]
    for i, node in enumerate(nodes):
        x = pad_side + i * (box_w + gap)
        y = pad_top + 30
        xs[str(node["id"])] = (x, y)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="none" stroke="{ACCENT_COLOR}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{x + box_w / 2}" y="{y + box_h / 2 + 4}" text-anchor="middle" '
            f'font-size="13" fill="{TEXT_COLOR}">{_esc(node["id"])}</text>'
        )
    parts.append(
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{ACCENT_COLOR}"/></marker>'
        '<marker id="arrow-forbidden" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{FORBIDDEN_COLOR}"/></marker></defs>'
    )
    for e in edges:
        a, b = xs.get(str(e["from"])), xs.get(str(e["to"]))
        if not a or not b:
            continue
        ax, ay = a[0] + box_w / 2, a[1] + box_h / 2
        bx, by = b[0] + box_w / 2, b[1] + box_h / 2
        parts.append(
            f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{ACCENT_COLOR}" '
            f'stroke-width="1.5" marker-end="url(#arrow)"/>'
        )
        if e.get("kind"):
            mx, my = (ax + bx) / 2, (ay + by) / 2 - 6
            parts.append(
                f'<text x="{mx}" y="{my}" text-anchor="middle" font-size="11" '
                f'fill="{TEXT_COLOR}">{_esc(e["kind"])}</text>'
            )
    for e in forbidden_edges:
        a, b = xs.get(str(e["from"])), xs.get(str(e["to"]))
        if not a or not b:
            continue
        ax, ay = a[0] + box_w / 2, a[1]
        bx, by = b[0] + box_w / 2, b[1]
        cx, cy = (ax + bx) / 2, min(ay, by) - 40
        parts.append(
            f'<path d="M{ax},{ay} Q{cx},{cy} {bx},{by}" fill="none" '
            f'stroke="{FORBIDDEN_COLOR}" stroke-width="1.5" stroke-dasharray="4 2" '
            f'marker-end="url(#arrow-forbidden)"/>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" font-size="11" '
            f'fill="{FORBIDDEN_COLOR}">forbidden</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Target mapping (ApplicationPlan) — bipartite
# ---------------------------------------------------------------------------


def _target_node_id(kind: Any, location: Any, seen: dict[tuple, str]) -> str:
    key = (kind, location)
    if key in seen:
        return seen[key]
    base = _mermaid_id(str(kind or "target"))
    n = sum(1 for v in seen.values() if v.startswith(base)) + 1
    node_id = f"{base}{n}"
    seen[key] = node_id
    return node_id


def mermaid_target_mapping(
    left_nodes: list[str],
    right_nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> str:
    lines = ["flowchart LR"]
    for lid in left_nodes:
        nid = _mermaid_id(str(lid))
        lines.append(f'  {nid}["{_esc(lid)}"]')
    seen: dict[tuple, str] = {}
    right_ids: dict[tuple, str] = {}
    for r in right_nodes:
        key = (r.get("kind"), r.get("location"))
        nid = _target_node_id(r.get("kind"), r.get("location"), seen)
        right_ids[key] = nid
        label = f"{r.get('kind')}: {_short(r.get('location'), 30)}"
        if r.get("density"):
            label += f"<br/>density: {r['density']}"
        if r.get("status") == "defer":
            label += " (defer)"
        lines.append(f'  {nid}["{label}"]')
    for e in edges:
        from_id = _mermaid_id(str(e["from"]))
        to_key = tuple(e["to"]) if isinstance(e["to"], list) else e["to"]
        to_id = right_ids.get(to_key)
        if to_id:
            lines.append(f"  {from_id} --> {to_id}")
    return "\n".join(lines)


def svg_target_mapping(
    left_nodes: list[str],
    right_nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> str | None:
    total = len(left_nodes) + len(right_nodes)
    if total < 2 or total > MAX_TARGET_NODES:
        return None
    box_w, box_h, row_gap, col_gap, pad = 200, 40, 16, 220, 24
    rows = max(len(left_nodes), len(right_nodes))
    height = pad * 2 + rows * box_h + max(0, rows - 1) * row_gap
    width = pad * 2 + box_w * 2 + col_gap
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Application target mapping diagram">'
    ]
    left_x = pad
    right_x = pad + box_w + col_gap
    left_pos: dict[str, tuple[float, float]] = {}
    for i, lid in enumerate(left_nodes):
        y = pad + i * (box_h + row_gap)
        left_pos[str(lid)] = (left_x, y)
        parts.append(
            f'<rect x="{left_x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="none" stroke="{ACCENT_COLOR}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{left_x + box_w / 2}" y="{y + box_h / 2 + 4}" text-anchor="middle" '
            f'font-size="13" fill="{TEXT_COLOR}">{_esc(lid)}</text>'
        )
    right_pos: dict[tuple, tuple[float, float]] = {}
    for i, r in enumerate(right_nodes):
        key = (r.get("kind"), r.get("location"))
        y = pad + i * (box_h + row_gap)
        right_pos[key] = (right_x, y)
        label = f"{r.get('kind')}: {_short(r.get('location'), 22)}"
        parts.append(
            f'<rect x="{right_x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="none" stroke="{ACCENT_COLOR}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{right_x + box_w / 2}" y="{y + box_h / 2 + 4}" text-anchor="middle" '
            f'font-size="12" fill="{TEXT_COLOR}">{_esc(label)}</text>'
        )
    parts.append(
        '<defs><marker id="arrow2" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{ACCENT_COLOR}"/></marker></defs>'
    )
    for e in edges:
        a = left_pos.get(str(e["from"]))
        to_key = tuple(e["to"]) if isinstance(e["to"], list) else e["to"]
        b = right_pos.get(to_key)
        if not a or not b:
            continue
        ax, ay = a[0] + box_w, a[1] + box_h / 2
        bx, by = b[0], b[1] + box_h / 2
        parts.append(
            f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{ACCENT_COLOR}" '
            f'stroke-width="1.5" marker-end="url(#arrow2)"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# State diagram (Formal: TLA+ / Alloy) — caller supplies the simplified
# state/transition data (deriving it requires reading prose, an LLM job).
# ---------------------------------------------------------------------------


def mermaid_state_diagram(states: list[str], transitions: list[dict[str, Any]]) -> str:
    lines = ["stateDiagram-v2", "  [*] --> " + _mermaid_id(states[0])] if states else ["stateDiagram-v2"]
    for t in transitions:
        a, b = _mermaid_id(str(t["from"])), _mermaid_id(str(t["to"]))
        label = f": {t['label']}" if t.get("label") else ""
        lines.append(f"  {a} --> {b}{label}")
    return "\n".join(lines)


def svg_state_diagram(states: list[str], transitions: list[dict[str, Any]]) -> str | None:
    if not states or len(states) > MAX_STATE_NODES:
        return None
    box_w, box_h, gap, pad = 120, 40, 70, 30
    n = len(states)
    width = pad * 2 + n * box_w + max(0, n - 1) * gap
    height = pad * 2 + box_h + 60
    pos: dict[str, tuple[float, float]] = {}
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Simplified state diagram">'
    ]
    for i, s in enumerate(states):
        x = pad + i * (box_w + gap)
        y = pad + 30
        pos[s] = (x, y)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="20" '
            f'fill="none" stroke="{ACCENT_COLOR}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{x + box_w / 2}" y="{y + box_h / 2 + 4}" text-anchor="middle" '
            f'font-size="13" fill="{TEXT_COLOR}">{_esc(s)}</text>'
        )
    parts.append(
        '<defs><marker id="arrow3" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{ACCENT_COLOR}"/></marker></defs>'
    )
    for t in transitions:
        a, b = pos.get(t["from"]), pos.get(t["to"])
        if not a or not b:
            continue
        ax, ay = a[0] + box_w, a[1] + box_h / 2
        bx, by = b[0], b[1] + box_h / 2
        parts.append(
            f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{ACCENT_COLOR}" '
            f'stroke-width="1.5" marker-end="url(#arrow3)"/>'
        )
        if t.get("label"):
            mx, my = (ax + bx) / 2, (ay + by) / 2 - 8
            parts.append(
                f'<text x="{mx}" y="{my}" text-anchor="middle" font-size="11" '
                f'fill="{TEXT_COLOR}">{_esc(t["label"])}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def render(payload: dict[str, Any]) -> dict[str, Any]:
    kind = payload.get("kind")
    if kind == "dependency_graph":
        nodes = payload.get("nodes") or []
        edges = payload.get("edges") or []
        forbidden = payload.get("forbidden_edges") or []
        return {
            "mermaid": mermaid_dependency_graph(nodes, edges, forbidden),
            "svg": svg_dependency_graph(nodes, edges, forbidden),
        }
    if kind == "target_mapping":
        left = payload.get("left_nodes") or []
        right = payload.get("right_nodes") or []
        edges = payload.get("edges") or []
        return {
            "mermaid": mermaid_target_mapping(left, right, edges),
            "svg": svg_target_mapping(left, right, edges),
        }
    if kind == "state_diagram":
        states = payload.get("states") or []
        transitions = payload.get("transitions") or []
        return {
            "mermaid": mermaid_state_diagram(states, transitions),
            "svg": svg_state_diagram(states, transitions),
        }
    raise SystemExit(f"unknown diagram kind: {kind!r} (expected dependency_graph|target_mapping|state_diagram)")


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Render a report diagram (Mermaid + optional SVG)")
    parser.add_argument("--in", dest="in_path", help="JSON payload path (default: stdin)")
    parser.add_argument("--out", help="Write result JSON here instead of stdout")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    import sys as _sys

    raw = Path(args.in_path).read_text(encoding="utf-8") if args.in_path else _sys.stdin.read()
    payload = json.loads(raw)
    result = render(payload)
    indent = 2 if args.pretty else None
    text = json.dumps(result, indent=indent, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + ("\n" if args.pretty else ""), encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

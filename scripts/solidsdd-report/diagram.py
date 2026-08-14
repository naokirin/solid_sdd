"""Diagram rendering for solidsdd-report.

Turns the node/edge data collect.py already extracted from ArchitecturePlan /
WorkPlan / ApplicationPlan (or, for Formal specs, data the caller supplies
after reading the .tla/.als source) into:

- Mermaid source text (flowchart LR / stateDiagram-v2) — always produced,
  and always correct: this is plain text templating, nothing to lay out.
- An inline SVG — rendered via the optional Mermaid CLI (`mmdc`,
  https://github.com/mermaid-js/mermaid-cli): a `mmdc` binary directly on
  `PATH` when present, else `npx --offline` (uses an already-installed
  local/cached copy only — never fetches over the network). `None` when
  neither path can invoke the tool or the render fails, in which case the
  caller keeps the Mermaid source only, exactly as change-report.md
  already allows.

Earlier versions of this module hand-computed box/arrow/label coordinates
directly. That repeatedly produced diagrams that were technically non-
overlapping but still hard to read (arrows crossing through boxes, curve
labels reading as attached to the wrong arrow, an opaque label backing that
hid the arrow underneath it) — node placement, edge routing, and label
placement without collisions is a genuinely hard layout problem that a
mature, purpose-built renderer solves far more reliably than a few hundred
lines of one-off geometry. Mermaid's own renderer (driven through `mmdc`) is
that renderer here, and it draws from the exact same Mermaid source already
used for the Markdown/no-SVG-fallback path, so the two representations of a
given diagram can't drift apart.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9_]")

FORBIDDEN_COLOR = "#ff6b6b"

MERMAID_CLI_BIN = "mmdc"
MERMAID_CLI_TIMEOUT = 20.0


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


# ---------------------------------------------------------------------------
# SVG rendering via the optional Mermaid CLI
# ---------------------------------------------------------------------------


MERMAID_CLI_NETWORK_TIMEOUT = 180.0  # generous: first-run npx install + Chromium download


def _mermaid_cli_command(*, allow_network: bool = False) -> list[str] | None:
    """Locate a way to invoke the Mermaid CLI.

    Prefers a `mmdc` binary directly on `PATH` (a global install, or an
    already-activated local `node_modules/.bin`) — never touches the
    network either way. Otherwise, when `npx` is on `PATH`:

    - by default, uses `--offline`, which only resolves an already-
      installed local project dependency or npm-cached copy of
      `@mermaid-js/mermaid-cli`; npm refuses to reach the registry at all
      in `--offline` mode, so this can never turn into a network fetch.
    - with `allow_network=True` (an explicit, caller-opted-in escape
      hatch — see change-report.md "HTML rendering"), drops `--offline`
      and adds `--yes` so npx installs the package on demand instead of
      prompting interactively (which would otherwise hang a
      non-interactive subprocess waiting for input that never arrives).

    Returns `None` when neither path can invoke the tool.
    """
    mmdc = shutil.which(MERMAID_CLI_BIN)
    if mmdc:
        return [mmdc]
    npx = shutil.which("npx")
    if not npx:
        return None
    if allow_network:
        return [npx, "--yes", "--package=@mermaid-js/mermaid-cli", "--", MERMAID_CLI_BIN]
    return [npx, "--offline", "--package=@mermaid-js/mermaid-cli", "--", MERMAID_CLI_BIN]


def mermaid_cli_available(*, allow_network: bool = False) -> bool:
    return _mermaid_cli_command(allow_network=allow_network) is not None


def _strip_to_svg_fragment(text: str) -> str:
    """mmdc writes a standalone SVG file (XML prolog + DOCTYPE); keep only
    the `<svg ...>...` fragment so it can be inlined into an HTML body."""
    start = text.find("<svg")
    return text[start:] if start != -1 else text


# One report can carry several diagrams (ArchitecturePlan, WorkPlan,
# ApplicationPlan, Formal), each calling render_svg_via_mermaid_cli. When
# the CLI can't actually produce SVG output in this environment (no browser
# runtime, tool missing), every one of those calls would otherwise pay for
# its own failed subprocess spawn (real seconds each — resolving `npx`,
# starting `mmdc`, trying and failing to launch a browser). `shutil.which`
# lookups aren't the slow part; the spawn-and-fail is. So the *outcome* of
# the first attempt per `allow_network` mode is memoized for the lifetime
# of this process (one `render`/`diagram` CLI invocation = one report), and
# every later diagram in the same run skips straight to `None` once that's
# established — a content-specific Mermaid syntax error from our own
# template functions is not a realistic failure mode, so "it failed once"
# is a safe signal that it will fail again for the same environment reason.
_svg_cli_probe_result: dict[bool, bool] = {}


def _reset_mermaid_cli_probe_cache() -> None:
    """Test hook: clear the per-process memoization from a clean slate."""
    _svg_cli_probe_result.clear()


def render_svg_via_mermaid_cli(
    mermaid_source: str, *, timeout: float | None = None, allow_network: bool = False
) -> str | None:
    """Render Mermaid source to an inline SVG fragment via the Mermaid CLI.

    Returns `None` — never raises — when the tool can't be invoked at all
    (see `_mermaid_cli_command`), or the render fails for any reason (no
    browser runtime available, timeout, malformed source). The caller keeps
    the Mermaid source only in that case; this is a best-effort enhancement,
    not a required step. See `_svg_cli_probe_result` above for why repeated
    calls after the first failure short-circuit instead of re-spawning.

    `allow_network=False` (default) never reaches the network — offline
    runs (CI, `solidsdd-run`, or any caller that hasn't explicitly asked a
    human) always get this. Pass `allow_network=True` only after a human
    has actually agreed to a one-time install (see change-report.md);
    that also raises the default timeout, since a first-run npx install
    plus a Chromium/Puppeteer download can take much longer than a cached
    render.
    """
    if not mermaid_source.strip():
        return None
    if _svg_cli_probe_result.get(allow_network) is False:
        return None
    command = _mermaid_cli_command(allow_network=allow_network)
    if not command:
        _svg_cli_probe_result[allow_network] = False
        return None
    if timeout is None:
        timeout = MERMAID_CLI_NETWORK_TIMEOUT if allow_network else MERMAID_CLI_TIMEOUT
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = Path(tmpdir) / "diagram.mmd"
            out_path = Path(tmpdir) / "diagram.svg"
            in_path.write_text(mermaid_source, encoding="utf-8")
            subprocess.run(
                [*command, "-i", str(in_path), "-o", str(out_path), "-b", "transparent", "-t", "dark"],
                capture_output=True,
                timeout=timeout,
                check=True,
            )
            if not out_path.is_file():
                _svg_cli_probe_result[allow_network] = False
                return None
            svg = _strip_to_svg_fragment(out_path.read_text(encoding="utf-8"))
            _svg_cli_probe_result[allow_network] = True
            return svg
    except (subprocess.SubprocessError, OSError):
        _svg_cli_probe_result[allow_network] = False
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def render(payload: dict[str, Any], *, allow_network: bool = False) -> dict[str, Any]:
    kind = payload.get("kind")
    if kind == "dependency_graph":
        nodes = payload.get("nodes") or []
        edges = payload.get("edges") or []
        forbidden = payload.get("forbidden_edges") or []
        mermaid = mermaid_dependency_graph(nodes, edges, forbidden)
    elif kind == "target_mapping":
        left = payload.get("left_nodes") or []
        right = payload.get("right_nodes") or []
        edges = payload.get("edges") or []
        mermaid = mermaid_target_mapping(left, right, edges)
    elif kind == "state_diagram":
        states = payload.get("states") or []
        transitions = payload.get("transitions") or []
        mermaid = mermaid_state_diagram(states, transitions)
    else:
        raise SystemExit(
            f"unknown diagram kind: {kind!r} (expected dependency_graph|target_mapping|state_diagram)"
        )
    return {"mermaid": mermaid, "svg": render_svg_via_mermaid_cli(mermaid, allow_network=allow_network)}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Render a report diagram (Mermaid + optional SVG via mmdc)")
    parser.add_argument("--in", dest="in_path", help="JSON payload path (default: stdin)")
    parser.add_argument("--out", help="Write result JSON here instead of stdout")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Let npx install @mermaid-js/mermaid-cli on demand if not already cached "
        "(only pass this after a human has agreed to it — see change-report.md)",
    )
    args = parser.parse_args(argv)

    import sys as _sys

    raw = Path(args.in_path).read_text(encoding="utf-8") if args.in_path else _sys.stdin.read()
    payload = json.loads(raw)
    result = render(payload, allow_network=args.allow_network)
    indent = 2 if args.pretty else None
    text = json.dumps(result, indent=indent, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + ("\n" if args.pretty else ""), encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

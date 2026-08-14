#!/usr/bin/env python3
"""Unit tests for solidsdd-report diagram.py."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import diagram  # noqa: E402


class DependencyGraphMermaidTests(unittest.TestCase):
    NODES = [{"id": "inventory", "label": "own stock"}, {"id": "reservation", "label": "own holds"}]
    EDGES = [{"from": "reservation", "to": "inventory", "kind": "runtime"}]
    FORBIDDEN = [{"from": "inventory", "to": "reservation", "reason": "keep independent"}]

    def test_mermaid_has_nodes_edge_and_forbidden_style(self) -> None:
        text = diagram.mermaid_dependency_graph(self.NODES, self.EDGES, self.FORBIDDEN)
        self.assertIn('flowchart LR', text)
        self.assertIn('inventory["inventory<br/>own stock"]', text)
        self.assertIn('reservation -->|runtime| inventory', text)
        self.assertIn('inventory -.->|forbidden| reservation', text)
        # The forbidden edge is the 2nd emitted edge (index 1).
        self.assertIn('linkStyle 1 stroke:#ff6b6b,stroke-dasharray: 4 2', text)

    def test_mermaid_sanitizes_hyphenated_ids(self) -> None:
        nodes = [{"id": "order-service", "label": None}]
        text = diagram.mermaid_dependency_graph(nodes, [], [])
        self.assertIn("order_service", text)
        self.assertIn('order-service', text)  # original id kept in the label

    def test_mermaid_notes_when_no_edges(self) -> None:
        text = diagram.mermaid_dependency_graph(self.NODES, [], [])
        self.assertIn("no dependency edges", text)


class TargetMappingMermaidTests(unittest.TestCase):
    LEFT = ["W1", "W2"]
    RIGHT = [
        {"kind": "api", "location": "openapi/openapi.yaml#/paths/~1things/post", "density": "standard"},
        {"kind": "dbc", "location": "contracts/Thing.ocl#do", "density": "standard", "status": "defer"},
    ]
    EDGES = [
        {"from": "W1", "to": ("api", "openapi/openapi.yaml#/paths/~1things/post")},
        {"from": "W1", "to": ("dbc", "contracts/Thing.ocl#do")},
        {"from": "W2", "to": ("dbc", "contracts/Thing.ocl#do")},
    ]

    def test_mermaid_bipartite_shape(self) -> None:
        text = diagram.mermaid_target_mapping(self.LEFT, self.RIGHT, self.EDGES)
        self.assertIn('W1["W1"]', text)
        self.assertIn("(defer)", text)
        self.assertIn("W1 --> api1", text)
        self.assertIn("W2 --> dbc1", text)

    def test_right_node_ids_are_unique_per_kind(self) -> None:
        right = [
            {"kind": "api", "location": "a"},
            {"kind": "api", "location": "b"},
        ]
        edges = [{"from": "W1", "to": ("api", "a")}, {"from": "W1", "to": ("api", "b")}]
        text = diagram.mermaid_target_mapping(["W1"], right, edges)
        self.assertIn("api1", text)
        self.assertIn("api2", text)
        self.assertIn("W1 --> api1", text)
        self.assertIn("W1 --> api2", text)


class StateDiagramMermaidTests(unittest.TestCase):
    STATES = ["Idle", "Owned"]
    TRANSITIONS = [{"from": "Idle", "to": "Owned", "label": "Acquire"}, {"from": "Owned", "to": "Idle", "label": "Add"}]

    def test_mermaid_shape(self) -> None:
        text = diagram.mermaid_state_diagram(self.STATES, self.TRANSITIONS)
        self.assertIn("stateDiagram-v2", text)
        self.assertIn("[*] --> Idle", text)
        self.assertIn("Idle --> Owned: Acquire", text)


class MermaidCliSvgTests(unittest.TestCase):
    """render_svg_via_mermaid_cli must never raise — mmdc is optional, and
    every failure mode (not installed, no browser runtime, timeout, bad
    input) has to fall back to `svg: None` so the caller keeps the Mermaid
    source only."""

    def setUp(self) -> None:
        diagram._reset_mermaid_cli_probe_cache()

    def test_returns_none_for_empty_source_without_touching_the_tool(self) -> None:
        with patch("diagram.shutil.which") as which:
            self.assertIsNone(diagram.render_svg_via_mermaid_cli(""))
            which.assert_not_called()

    def test_returns_none_when_cli_not_on_path(self) -> None:
        with patch("diagram.shutil.which", return_value=None):
            self.assertIsNone(diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b"))

    def test_returns_none_when_cli_invocation_fails(self) -> None:
        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"), patch(
            "diagram.subprocess.run", side_effect=subprocess.CalledProcessError(1, ["mmdc"])
        ):
            self.assertIsNone(diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b"))

    def test_returns_none_on_timeout(self) -> None:
        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"), patch(
            "diagram.subprocess.run", side_effect=subprocess.TimeoutExpired(["mmdc"], 20)
        ):
            self.assertIsNone(diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b"))

    def test_returns_svg_fragment_stripped_of_xml_prolog_on_success(self) -> None:
        def fake_run(cmd, **kwargs):
            out_path = Path(cmd[cmd.index("-o") + 1])
            out_path.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<!DOCTYPE svg PUBLIC>\n"
                '<svg xmlns="http://www.w3.org/2000/svg"><g>ok</g></svg>',
                encoding="utf-8",
            )

        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"), patch(
            "diagram.subprocess.run", side_effect=fake_run
        ):
            svg = diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b")
        self.assertIsNotNone(svg)
        self.assertTrue(svg.startswith("<svg"))
        self.assertNotIn("<?xml", svg)
        self.assertNotIn("<!DOCTYPE", svg)

    def test_falls_back_to_npx_offline_when_mmdc_not_on_path(self) -> None:
        # No global/local `mmdc` on PATH, but `npx` is — must invoke it with
        # `--offline` so it only ever uses an already-installed local
        # project dependency or npm cache, never a network fetch.
        def which(name):
            return {"npx": "/usr/bin/npx"}.get(name)

        captured_cmd = {}

        def fake_run(cmd, **kwargs):
            captured_cmd["cmd"] = cmd
            out_path = Path(cmd[cmd.index("-o") + 1])
            out_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")

        with patch("diagram.shutil.which", side_effect=which), patch(
            "diagram.subprocess.run", side_effect=fake_run
        ):
            svg = diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b")
        self.assertIsNotNone(svg)
        cmd = captured_cmd["cmd"]
        self.assertEqual(cmd[0], "/usr/bin/npx")
        self.assertIn("--offline", cmd)
        self.assertIn("--package=@mermaid-js/mermaid-cli", cmd)

    def test_returns_none_when_neither_mmdc_nor_npx_on_path(self) -> None:
        with patch("diagram.shutil.which", return_value=None):
            self.assertIsNone(diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b"))
            self.assertFalse(diagram.mermaid_cli_available())

    def test_second_diagram_in_same_run_skips_subprocess_after_first_failure(self) -> None:
        # A report can carry several diagrams; once the first spawn fails
        # (no browser runtime, etc.), every later diagram in the same
        # process must return None immediately rather than paying for its
        # own failed subprocess spawn again.
        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"), patch(
            "diagram.subprocess.run", side_effect=subprocess.CalledProcessError(1, ["mmdc"])
        ) as run:
            self.assertIsNone(diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b"))
            self.assertEqual(run.call_count, 1)
            self.assertIsNone(diagram.render_svg_via_mermaid_cli("stateDiagram-v2\n  [*] --> Idle"))
            self.assertEqual(run.call_count, 1, "second diagram must not spawn a new subprocess")

    def test_probe_cache_is_scoped_per_allow_network_value(self) -> None:
        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"), patch(
            "diagram.subprocess.run", side_effect=subprocess.CalledProcessError(1, ["mmdc"])
        ) as run:
            diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b", allow_network=False)
            diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b", allow_network=True)
        self.assertEqual(run.call_count, 2, "offline and allow_network failures are cached independently")

    def test_probe_cache_does_not_short_circuit_after_a_success(self) -> None:
        def fake_run(cmd, **kwargs):
            out_path = Path(cmd[cmd.index("-o") + 1])
            out_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")

        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"), patch(
            "diagram.subprocess.run", side_effect=fake_run
        ) as run:
            diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b")
            diagram.render_svg_via_mermaid_cli("stateDiagram-v2\n  [*] --> Idle")
        self.assertEqual(run.call_count, 2, "a working tool still renders every diagram, not just the first")

    def test_prefers_direct_mmdc_over_npx_when_both_available(self) -> None:
        def which(name):
            return {"mmdc": "/usr/bin/mmdc", "npx": "/usr/bin/npx"}.get(name)

        with patch("diagram.shutil.which", side_effect=which):
            self.assertEqual(diagram._mermaid_cli_command(), ["/usr/bin/mmdc"])

    def test_allow_network_drops_offline_and_adds_yes(self) -> None:
        # Only after a human has explicitly agreed (see change-report.md) —
        # `--yes` avoids an interactive npx install prompt hanging a
        # subprocess with no TTY attached.
        def which(name):
            return {"npx": "/usr/bin/npx"}.get(name)

        with patch("diagram.shutil.which", side_effect=which):
            cmd = diagram._mermaid_cli_command(allow_network=True)
        self.assertNotIn("--offline", cmd)
        self.assertIn("--yes", cmd)

    def test_allow_network_does_not_change_direct_mmdc_invocation(self) -> None:
        # A local/global mmdc binary never touches the network either way.
        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"):
            self.assertEqual(diagram._mermaid_cli_command(allow_network=True), ["/usr/bin/mmdc"])

    def test_allow_network_uses_a_longer_default_timeout(self) -> None:
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["timeout"] = kwargs.get("timeout")
            out_path = Path(cmd[cmd.index("-o") + 1])
            out_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")

        with patch("diagram.shutil.which", return_value="/usr/bin/mmdc"), patch(
            "diagram.subprocess.run", side_effect=fake_run
        ):
            diagram.render_svg_via_mermaid_cli("flowchart LR\n  a --> b", allow_network=True)
        self.assertEqual(captured["timeout"], diagram.MERMAID_CLI_NETWORK_TIMEOUT)
        self.assertGreater(diagram.MERMAID_CLI_NETWORK_TIMEOUT, diagram.MERMAID_CLI_TIMEOUT)


class RenderDispatchTests(unittest.TestCase):
    def test_render_dependency_graph_shape(self) -> None:
        with patch("diagram.render_svg_via_mermaid_cli", return_value=None):
            result = diagram.render(
                {
                    "kind": "dependency_graph",
                    "nodes": [{"id": "a", "label": "A"}],
                    "edges": [],
                    "forbidden_edges": [],
                }
            )
        self.assertIn("mermaid", result)
        self.assertIn("svg", result)
        self.assertIsNone(result["svg"])

    def test_render_passes_mermaid_source_to_svg_renderer(self) -> None:
        with patch("diagram.render_svg_via_mermaid_cli", return_value="<svg>stub</svg>") as renderer:
            result = diagram.render({"kind": "state_diagram", "states": ["Idle"], "transitions": []})
        renderer.assert_called_once_with(result["mermaid"], allow_network=False)
        self.assertEqual(result["svg"], "<svg>stub</svg>")

    def test_render_forwards_allow_network(self) -> None:
        with patch("diagram.render_svg_via_mermaid_cli", return_value=None) as renderer:
            result = diagram.render(
                {"kind": "state_diagram", "states": ["Idle"], "transitions": []}, allow_network=True
            )
        renderer.assert_called_once_with(result["mermaid"], allow_network=True)

    def test_render_unknown_kind_raises(self) -> None:
        with self.assertRaises(SystemExit):
            diagram.render({"kind": "bogus"})


class CliAllowNetworkFlagTests(unittest.TestCase):
    def test_allow_network_flag_reaches_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "payload.json"
            payload_path.write_text(
                json.dumps({"kind": "state_diagram", "states": ["Idle"], "transitions": []}), encoding="utf-8"
            )
            with patch("diagram.render_svg_via_mermaid_cli", return_value=None) as renderer:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    diagram.main(["--in", str(payload_path), "--allow-network"])
            self.assertTrue(renderer.call_args.kwargs.get("allow_network"))


if __name__ == "__main__":
    unittest.main()

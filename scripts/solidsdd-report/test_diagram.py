#!/usr/bin/env python3
"""Unit tests for solidsdd-report diagram.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import diagram  # noqa: E402


class DependencyGraphTests(unittest.TestCase):
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

    def test_svg_produced_for_small_graph(self) -> None:
        svg = diagram.svg_dependency_graph(self.NODES, self.EDGES, self.FORBIDDEN)
        self.assertIsNotNone(svg)
        self.assertIn("<svg", svg)
        self.assertIn("forbidden", svg)

    def test_svg_skipped_above_node_threshold(self) -> None:
        many_nodes = [{"id": f"m{i}", "label": ""} for i in range(diagram.MAX_ROW_NODES + 1)]
        self.assertIsNone(diagram.svg_dependency_graph(many_nodes, [], []))

    def test_svg_none_for_empty_nodes(self) -> None:
        self.assertIsNone(diagram.svg_dependency_graph([], [], []))


class TargetMappingTests(unittest.TestCase):
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

    def test_svg_skipped_above_threshold(self) -> None:
        left = [f"W{i}" for i in range(diagram.MAX_TARGET_NODES)]
        right = [{"kind": "api", "location": f"a{i}"} for i in range(diagram.MAX_TARGET_NODES)]
        self.assertIsNone(diagram.svg_target_mapping(left, right, []))

    def test_svg_produced_for_small_mapping(self) -> None:
        svg = diagram.svg_target_mapping(self.LEFT, self.RIGHT, self.EDGES)
        self.assertIsNotNone(svg)
        self.assertIn("<svg", svg)


class StateDiagramTests(unittest.TestCase):
    STATES = ["Idle", "Owned"]
    TRANSITIONS = [{"from": "Idle", "to": "Owned", "label": "Acquire"}, {"from": "Owned", "to": "Idle", "label": "Add"}]

    def test_mermaid_shape(self) -> None:
        text = diagram.mermaid_state_diagram(self.STATES, self.TRANSITIONS)
        self.assertIn("stateDiagram-v2", text)
        self.assertIn("[*] --> Idle", text)
        self.assertIn("Idle --> Owned: Acquire", text)

    def test_svg_skipped_above_threshold(self) -> None:
        states = [f"S{i}" for i in range(diagram.MAX_STATE_NODES + 1)]
        self.assertIsNone(diagram.svg_state_diagram(states, []))

    def test_svg_produced_for_small_diagram(self) -> None:
        svg = diagram.svg_state_diagram(self.STATES, self.TRANSITIONS)
        self.assertIsNotNone(svg)
        self.assertIn("<svg", svg)


class RenderDispatchTests(unittest.TestCase):
    def test_render_dependency_graph(self) -> None:
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

    def test_render_unknown_kind_raises(self) -> None:
        with self.assertRaises(SystemExit):
            diagram.render({"kind": "bogus"})


if __name__ == "__main__":
    unittest.main()

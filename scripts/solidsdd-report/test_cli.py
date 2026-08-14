#!/usr/bin/env python3
"""Unit tests for the solidsdd-report CLI dispatcher (cli.py)."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import cli  # noqa: E402


class CliDispatchTests(unittest.TestCase):
    def _empty_project(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        change_dir = root / ".solidsdd" / "changes" / "demo"
        change_dir.mkdir(parents=True)
        (root / ".solidsdd" / "active-change.json").write_text(
            json.dumps({"version": "1", "change_id": "demo"}), encoding="utf-8"
        )
        return root

    def test_no_args_prints_usage_and_errors(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main([])
        self.assertEqual(rc, 2)

    def test_unknown_subcommand_errors(self) -> None:
        rc = cli.main(["bogus"])
        self.assertEqual(rc, 2)

    def test_collect_dispatch(self) -> None:
        root = self._empty_project()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["collect", "--project-root", str(root), "--change-id", "demo"])
        self.assertEqual(rc, 0)
        self.assertIn('"change_id": "demo"', buf.getvalue())

    def test_highlight_dispatch(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["highlight", "--css-only"])
        self.assertEqual(rc, 0)
        self.assertIn(".tok-key", buf.getvalue())

    def test_diagram_dispatch(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        payload_path = Path(tmp.name) / "payload.json"
        payload_path.write_text(
            json.dumps({"kind": "dependency_graph", "nodes": [{"id": "a", "label": "A"}], "edges": [], "forbidden_edges": []}),
            encoding="utf-8",
        )
        buf = io.StringIO()
        # Don't let this hit a real npx/mmdc spawn — the SVG path itself is
        # covered by diagram.py's own tests; here we only need to check
        # dispatch, and a real subprocess attempt would make this test slow
        # and environment-dependent (fast/instant with mmdc installed,
        # ~1-2s of failed spawns without it).
        with patch("diagram.render_svg_via_mermaid_cli", return_value=None), redirect_stdout(buf):
            rc = cli.main(["diagram", "--in", str(payload_path)])
        self.assertEqual(rc, 0)
        self.assertIn('"mermaid"', buf.getvalue())

    def test_render_dispatch(self) -> None:
        root = self._empty_project()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["render", "--project-root", str(root), "--change-id", "demo", "--format", "markdown"])
        self.assertEqual(rc, 0)
        self.assertIn('"markdown"', buf.getvalue())
        self.assertTrue((root / ".solidsdd" / "changes" / "demo" / "report.md").is_file())


if __name__ == "__main__":
    unittest.main()

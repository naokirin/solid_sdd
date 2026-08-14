#!/usr/bin/env python3
"""Unit tests for the solidsdd-architecture CLI dispatcher (cli.py)."""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import cli  # noqa: E402


class CliDispatchTests(unittest.TestCase):
    def _project_with_workspace(self, tag: str = "change:demo") -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        arch_dir = root / ".solidsdd" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "workspace.dsl").write_text(
            f'workspace "W" {{ model {{ a = softwareSystem "A" {{ tags "{tag}" }} }} }}',
            encoding="utf-8",
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

    def test_validate_dispatch(self) -> None:
        root = self._project_with_workspace()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["validate", "--project-root", str(root)])
        self.assertEqual(rc, 0)
        self.assertIn('"findings": []', buf.getvalue())

    def test_project_dispatch(self) -> None:
        root = self._project_with_workspace()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(
                ["project", "--project-root", str(root), "--change-id", "demo"]
            )
        self.assertEqual(rc, 0)
        self.assertIn('"status": "changed"', buf.getvalue())


if __name__ == "__main__":
    unittest.main()

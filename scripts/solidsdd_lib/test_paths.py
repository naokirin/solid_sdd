#!/usr/bin/env python3
"""Unit tests for solidsdd_lib.paths."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from solidsdd_lib.paths import load_layout, resolve_change_dir  # noqa: E402


class PathsTests(unittest.TestCase):
    def test_defaults_without_config(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".solidsdd").mkdir()
        layout = load_layout(root)
        self.assertEqual(layout.changes, ".solidsdd/changes")
        self.assertEqual(layout.openapi, "openapi/openapi.yaml")
        self.assertEqual(layout.knowledge, ("knowledge",))
        self.assertIsNone(layout.config_path)

    def test_config_override_changes(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        sdd = root / ".solidsdd"
        sdd.mkdir()
        (sdd / "config.yaml").write_text(
            'version: "1"\npaths:\n  changes: docs/changes\n  openapi: api/openapi.yaml\n',
            encoding="utf-8",
        )
        layout = load_layout(root)
        self.assertEqual(layout.changes, "docs/changes")
        self.assertEqual(layout.openapi, "api/openapi.yaml")
        self.assertEqual(layout.active_change, ".solidsdd/active-change.json")
        self.assertEqual(layout.config_path, sdd / "config.yaml")

        cid = "alt-change"
        cdir = root / "docs" / "changes" / cid
        cdir.mkdir(parents=True)
        (sdd / "active-change.json").write_text(
            json.dumps({"version": "1", "change_id": cid}),
            encoding="utf-8",
        )
        got_id, got_dir = resolve_change_dir(root, None)
        self.assertEqual(got_id, cid)
        self.assertEqual(got_dir, cdir)

    def test_solidsdd_mismatch_errors(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        sdd = root / ".solidsdd"
        sdd.mkdir()
        (sdd / "config.yaml").write_text(
            'version: "1"\npaths:\n  solidsdd: other-meta\n',
            encoding="utf-8",
        )
        with self.assertRaises(SystemExit) as ctx:
            load_layout(root)
        self.assertIn("does not match discovery", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

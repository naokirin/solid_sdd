#!/usr/bin/env python3
"""Unit tests for solidsdd-next (no project write)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import next as nxt


class NextTests(unittest.TestCase):
    def _change(self, files: dict[str, object]) -> tuple[str, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        cid = "sample-change"
        cdir = root / ".solidsdd" / "changes" / cid
        cdir.mkdir(parents=True)
        (root / ".solidsdd" / "active-change.json").write_text(
            json.dumps({"version": "1", "change_id": cid}), encoding="utf-8"
        )
        for rel, body in files.items():
            path = cdir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(body, (dict, list)):
                path.write_text(json.dumps(body), encoding="utf-8")
            else:
                path.write_text(str(body), encoding="utf-8")
        return cid, cdir

    def test_brief_phase_needs_critique(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "brief",
                    "run_retry": {"remaining": 3, "max": 3},
                },
                "change-brief.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "summary": "s",
                    "goal": "g",
                    "in_scope": [{"id": "R1", "text": "t"}],
                    "out_of_scope": [],
                    "success_criteria": [{"id": "SC1", "text": "t"}],
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "critique_change_brief")
        self.assertIn("critique_change_brief", h["legal_actions"])

    def test_validate_rejects_illegal(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "brief",
                    "run_retry": {"remaining": 3, "max": 3},
                },
                "change-brief.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "summary": "s",
                    "goal": "g",
                    "in_scope": [{"id": "R1", "text": "t"}],
                    "out_of_scope": [],
                    "success_criteria": [{"id": "SC1", "text": "t"}],
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        legal = set(h.get("legal_actions") or [h["action"]])
        self.assertNotIn("waves", legal)

    def test_blocking_clarifications(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "grill",
                    "run_retry": {"remaining": 3, "max": 3},
                },
                "clarifications/open.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "items": [
                        {
                            "id": "Q1",
                            "question": "AuthZ model?",
                            "status": "open",
                            "blocking": True,
                        }
                    ],
                    "human_gate": {"required": True},
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "human_gate")


if __name__ == "__main__":
    unittest.main()

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

    def _single_item_waves(self, item_report: dict[str, object] | None) -> tuple[str, Path]:
        files: dict[str, object] = {
            "run-state.json": {
                "version": "1",
                "change_id": "sample-change",
                "phase": "waves",
                "run_retry": {"remaining": 3, "max": 3},
                "items": {"W1": {"status": "done", "artifact_dir": "items/W1"}},
            },
            "work-plan.json": {
                "version": "1",
                "change_id": "sample-change",
                "items": [{"id": "W1", "intent": "i", "acceptance_criterion": "s", "covers": ["R1"]}],
            },
        }
        if item_report is not None:
            files["items/W1/verification-report.json"] = item_report
        return self._change(files)

    def test_b4_skip_when_sole_item_covers_acceptance_of_whole(self) -> None:
        cid, cdir = self._single_item_waves(
            {
                "version": "1",
                "change_id": "sample-change",
                "result": "pass",
                "checks": [{"name": "n", "kind": "other", "result": "pass", "covers": ["acceptance_of_whole", "W1"]}],
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "knowledge_harvest")
        self.assertIn("cost_skip:B4", h["reason"])
        self.assertIn("integration_verify", h["legal_actions"])

    def test_no_b4_skip_without_acceptance_of_whole_tag(self) -> None:
        cid, cdir = self._single_item_waves(
            {
                "version": "1",
                "change_id": "sample-change",
                "result": "pass",
                "checks": [{"name": "n", "kind": "other", "result": "pass", "covers": ["W1"]}],
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "integration_verify")

    def test_no_b4_skip_when_item_report_missing(self) -> None:
        cid, cdir = self._single_item_waves(None)
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "integration_verify")


if __name__ == "__main__":
    unittest.main()

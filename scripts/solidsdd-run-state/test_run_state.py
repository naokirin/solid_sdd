#!/usr/bin/env python3
"""Unit tests for solidsdd-run-state."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import run_state as rs


class RunStateCliTests(unittest.TestCase):
    def _project(self, with_work_plan: bool = True) -> tuple[Path, str, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        cid = "sample-change"
        cdir = root / ".solidsdd" / "changes" / cid
        cdir.mkdir(parents=True)
        (root / ".solidsdd" / "active-change.json").write_text(
            json.dumps({"version": "1", "change_id": cid}),
            encoding="utf-8",
        )
        (cdir / "status.json").write_text(
            json.dumps({"version": "1", "status": "active"}),
            encoding="utf-8",
        )
        if with_work_plan:
            (cdir / "work-plan.json").write_text(
                json.dumps(
                    {
                        "version": "1",
                        "change_id": cid,
                        "summary": "s",
                        "acceptance_of_whole": "Scenario: whole\n  Given x\n  When y\n  Then z",
                        "items": [
                            {
                                "id": "W1",
                                "intent": "do W1",
                                "acceptance_criterion": (
                                    "Scenario: W1\n  Given a\n  When b\n  Then c"
                                ),
                                "covers": ["R1"],
                                "depends_on": [],
                                "status": "ready",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
        return root, cid, cdir

    def test_happy_path(self) -> None:
        root, cid, cdir = self._project()
        self.assertEqual(rs.main(["--project-root", str(root), "init"]), 0)
        self.assertTrue((cdir / "run-state.json").is_file())

        self.assertEqual(
            rs.main(["--project-root", str(root), "set-phase", "--phase", "waves"]),
            0,
        )
        self.assertEqual(
            rs.main(["--project-root", str(root), "set-wave", "--index", "1"]),
            0,
        )
        self.assertEqual(rs.main(["--project-root", str(root), "sync-items"]), 0)

        data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(data["phase"], "waves")
        self.assertEqual(data["wave_index"], 1)
        self.assertEqual(data["items"]["W1"]["status"], "ready")
        self.assertEqual(data["items"]["W1"]["artifact_dir"], "items/W1")

        self.assertEqual(
            rs.main(
                [
                    "--project-root",
                    str(root),
                    "set-item",
                    "--id",
                    "W1",
                    "--status",
                    "done",
                    "--loop-phase",
                    "done",
                    "--sync-work-plan",
                ]
            ),
            0,
        )
        wp = json.loads((cdir / "work-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(wp["items"][0]["status"], "done")

        self.assertEqual(
            rs.main(
                [
                    "--project-root",
                    str(root),
                    "note",
                    "--append",
                    "cost_skip:B4",
                ]
            ),
            0,
        )
        data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
        self.assertIn("cost_skip:B4", data["isolation_notes"])

        # dedupe
        self.assertEqual(
            rs.main(
                [
                    "--project-root",
                    str(root),
                    "note",
                    "--append",
                    "cost_skip:B4",
                ]
            ),
            0,
        )
        data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(data["isolation_notes"].count("cost_skip:B4"), 1)

        self.assertEqual(
            rs.main(["--project-root", str(root), "mark-change-done"]),
            0,
        )
        data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
        status = json.loads((cdir / "status.json").read_text(encoding="utf-8"))
        self.assertEqual(data["phase"], "done")
        self.assertEqual(status["status"], "done")
        rs.validate_run_state(data)

    def test_init_refuses_existing(self) -> None:
        root, _, cdir = self._project(with_work_plan=False)
        self.assertEqual(rs.main(["--project-root", str(root), "init"]), 0)
        with self.assertRaises(SystemExit):
            rs.main(["--project-root", str(root), "init"])
        self.assertEqual(
            rs.main(["--project-root", str(root), "init", "--force"]),
            0,
        )

    def test_architecture_phases_accepted(self) -> None:
        root, _, cdir = self._project(with_work_plan=False)
        rs.main(["--project-root", str(root), "init"])
        for phase in ("architecture", "critique_architecture"):
            self.assertEqual(
                rs.main(["--project-root", str(root), "set-phase", "--phase", phase]),
                0,
            )
            data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(data["phase"], phase)
            rs.validate_run_state(data)

    def test_invalid_phase(self) -> None:
        root, _, _ = self._project(with_work_plan=False)
        rs.main(["--project-root", str(root), "init"])
        with self.assertRaises(SystemExit):
            rs.main(
                [
                    "--project-root",
                    str(root),
                    "set-phase",
                    "--phase",
                    "not-a-phase",
                ]
            )

    def test_unknown_item(self) -> None:
        root, _, _ = self._project()
        rs.main(["--project-root", str(root), "init"])
        rs.main(["--project-root", str(root), "sync-items"])
        with self.assertRaises(SystemExit):
            rs.main(
                [
                    "--project-root",
                    str(root),
                    "set-item",
                    "--id",
                    "W99",
                    "--status",
                    "done",
                ]
            )

    def test_set_host_toolchain(self) -> None:
        root, _, cdir = self._project(with_work_plan=False)
        rs.main(["--project-root", str(root), "init"])
        (root / ".solidsdd" / "host-toolchain.json").write_text(
            json.dumps(
                {
                    "version": "1",
                    "ready": True,
                    "missing": [],
                    "resolved_at": "2026-08-05T00:00:00Z",
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            rs.main(["--project-root", str(root), "set-host-toolchain"]),
            0,
        )
        data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
        self.assertTrue(data["host_toolchain"]["ready"])
        self.assertEqual(
            data["host_toolchain"]["source"], ".solidsdd/host-toolchain.json"
        )

    def test_record_metrics(self) -> None:
        root, _, cdir = self._project(with_work_plan=False)
        rs.main(["--project-root", str(root), "init"])
        self.assertEqual(
            rs.main(
                [
                    "--project-root",
                    str(root),
                    "record-metrics",
                    "--inc-task-launches",
                    "2",
                    "--inc-critiques",
                    "1",
                    "--set-slices",
                    "3",
                ]
            ),
            0,
        )
        data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(data["metrics"]["task_launch_count"], 2)
        self.assertEqual(data["metrics"]["critique_count"], 1)
        self.assertEqual(data["metrics"]["slice_count"], 3)
        self.assertIn("started_at", data["metrics"])

        # Second increment
        self.assertEqual(
            rs.main(
                [
                    "--project-root",
                    str(root),
                    "record-metrics",
                    "--inc-task-launches",
                    "1",
                    "--inc-critiques",
                    "2",
                ]
            ),
            0,
        )
        data = json.loads((cdir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(data["metrics"]["task_launch_count"], 3)
        self.assertEqual(data["metrics"]["critique_count"], 3)
        rs.validate_run_state(data)

    def test_changes_path_override(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        cid = "relocated-change"
        cdir = root / "alt-changes" / cid
        cdir.mkdir(parents=True)
        sdd = root / ".solidsdd"
        sdd.mkdir()
        (sdd / "config.yaml").write_text(
            'version: "1"\npaths:\n  changes: alt-changes\n',
            encoding="utf-8",
        )
        (sdd / "active-change.json").write_text(
            json.dumps({"version": "1", "change_id": cid}),
            encoding="utf-8",
        )
        (cdir / "status.json").write_text(
            json.dumps({"version": "1", "status": "active"}),
            encoding="utf-8",
        )
        self.assertEqual(rs.main(["--project-root", str(root), "init"]), 0)
        self.assertTrue((cdir / "run-state.json").is_file())
        self.assertFalse(
            (root / ".solidsdd" / "changes" / cid / "run-state.json").exists()
        )


if __name__ == "__main__":
    unittest.main()

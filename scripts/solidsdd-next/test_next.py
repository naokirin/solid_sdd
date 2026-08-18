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

    def test_critique_work_plan_runs_architecture_when_no_plan_yet(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "critique_work_plan",
                    "run_retry": {"remaining": 3, "max": 3},
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "architecture")
        self.assertEqual(h["skill"], "solidsdd-architecture")

    def test_architecture_unchanged_skips_critique_and_enters_waves(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "architecture",
                    "run_retry": {"remaining": 3, "max": 3},
                },
                "architecture-plan.json": {
                    "version": "1",
                    "status": "unchanged",
                    "change_id": "sample-change",
                    "summary": "no structural change",
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "waves")
        self.assertEqual(h["phase"], "critique_architecture")

    def test_architecture_changed_needs_critique(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "architecture",
                    "run_retry": {"remaining": 3, "max": 3},
                },
                "architecture-plan.json": {
                    "version": "1",
                    "status": "changed",
                    "change_id": "sample-change",
                    "modules": [{"id": "a", "responsibility": "r"}],
                    "dependencies": [],
                    "constraints": [],
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "critique_architecture")
        self.assertEqual(h["subject"], "architecture_plan")

    def test_architecture_gate_required_blocks_waves(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "architecture",
                    "run_retry": {"remaining": 3, "max": 3},
                },
                "architecture-plan.json": {
                    "version": "1",
                    "status": "changed",
                    "change_id": "sample-change",
                    "modules": [{"id": "a", "responsibility": "r"}],
                    "dependencies": [],
                    "constraints": [],
                    "human_gate": {"required": True, "reason": "external boundary change"},
                },
                "critique-architecture-plan.json": {
                    "version": "1",
                    "subject": "architecture_plan",
                    "result": "pass",
                    "findings": [],
                    "summary": "ok",
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "human_gate")

    def test_direct_profile_recommends_direct_implementation_no_run_state(self) -> None:
        cid, cdir = self._change(
            {
                "triage-result.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "requested_profile": "auto",
                    "effective_profile": "direct",
                    "required_minimum_profile": "direct",
                    "change_type": "local",
                    "risk": "low",
                    "complexity": "low",
                    "contract_impact": False,
                    "architecture_impact": False,
                    "uncertain": False,
                    "reasons": ["typo fix; no contract/architecture impact"],
                    "decided_at": "2026-08-18T00:00:00Z",
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "direct_implementation")
        legal = set(h["legal_actions"])
        for heavy in ("intake", "brief", "decompose", "architecture", "waves"):
            self.assertNotIn(heavy, legal)

    def test_thin_profile_recommends_thin_implementation_no_run_state(self) -> None:
        cid, cdir = self._change(
            {
                "triage-result.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "requested_profile": "auto",
                    "effective_profile": "thin",
                    "required_minimum_profile": "thin",
                    "change_type": "local",
                    "risk": "low",
                    "complexity": "low",
                    "contract_impact": False,
                    "architecture_impact": False,
                    "uncertain": False,
                    "reasons": ["small additive change"],
                    "decided_at": "2026-08-18T00:00:00Z",
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "thin_implementation")
        self.assertEqual(h["skill"], "solidsdd-implement")
        legal = set(h["legal_actions"])
        for heavy in ("intake", "brief", "decompose", "architecture", "waves"):
            self.assertNotIn(heavy, legal)

    def test_thin_implementation_phase_recommends_thin_verification(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "thin_implementation",
                    "run_retry": {"remaining": 3, "max": 3},
                    "execution_profile": {
                        "requested": "auto",
                        "effective": "thin",
                        "required_minimum": "thin",
                    },
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "thin_verification")
        self.assertEqual(h["skill"], "solidsdd-verify")

    def test_thin_verification_pass_recommends_done(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "thin_verification",
                    "run_retry": {"remaining": 3, "max": 3},
                    "execution_profile": {
                        "requested": "auto",
                        "effective": "thin",
                        "required_minimum": "thin",
                    },
                },
                "verification-report.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "result": "pass",
                    "checks": [],
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "done")

    def test_thin_verification_fail_recommends_critique_not_downgrade(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "thin_verification",
                    "run_retry": {"remaining": 3, "max": 3},
                    "execution_profile": {
                        "requested": "auto",
                        "effective": "thin",
                        "required_minimum": "thin",
                    },
                },
                "verification-report.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "result": "fail",
                    "checks": [],
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "critique_verification_report")
        self.assertEqual(h["subject"], "verification_report")

    def test_standard_profile_triage_phase_falls_through_to_knowledge_consult(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "triage",
                    "run_retry": {"remaining": 3, "max": 3},
                    "execution_profile": {
                        "requested": "auto",
                        "effective": "standard",
                        "required_minimum": "standard",
                    },
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "knowledge_consult")

    def test_parse_profile_dash_flag(self) -> None:
        r = nxt.parse_explicit_profile("please run --profile thin: fix the typo")
        self.assertEqual(r["requested_profile"], "thin")
        self.assertTrue(r["explicit"])
        self.assertEqual(r["matched_text"], "--profile thin")

    def test_parse_profile_colon_form(self) -> None:
        r = nxt.parse_explicit_profile("profile: full - handle auth change")
        self.assertEqual(r["requested_profile"], "full")
        self.assertTrue(r["explicit"])

    def test_parse_profile_equals_and_case_insensitive(self) -> None:
        r = nxt.parse_explicit_profile("--profile=STANDARD add the field")
        self.assertEqual(r["requested_profile"], "standard")
        self.assertTrue(r["explicit"])

    def test_parse_profile_no_token_defaults_auto(self) -> None:
        r = nxt.parse_explicit_profile("no explicit profile mentioned here")
        self.assertEqual(r["requested_profile"], "auto")
        self.assertFalse(r["explicit"])
        self.assertNotIn("warning", r)

    def test_parse_profile_invalid_value_warns_and_defaults_auto(self) -> None:
        r = nxt.parse_explicit_profile("--profile fast please")
        self.assertEqual(r["requested_profile"], "auto")
        self.assertFalse(r["explicit"])
        self.assertIn("fast", r["warning"])

    def test_parse_profile_empty_text(self) -> None:
        r = nxt.parse_explicit_profile("")
        self.assertEqual(r["requested_profile"], "auto")
        self.assertFalse(r["explicit"])

    def test_parse_profile_cli_command(self) -> None:
        argv = ["parse-profile", "--text", "--profile direct: bump a comment"]
        # main() prints JSON and returns 0; capture via monkeypatching stdout is
        # unnecessary here — just assert the exit code and that the underlying
        # function (already tested above) is what backs the command.
        self.assertEqual(nxt.main(argv), 0)

    def test_critique_architecture_enters_waves_with_ready_items(self) -> None:
        cid, cdir = self._change(
            {
                "run-state.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "phase": "critique_architecture",
                    "run_retry": {"remaining": 3, "max": 3},
                    "items": {"W1": {"status": "ready"}},
                },
                "work-plan.json": {
                    "version": "1",
                    "change_id": "sample-change",
                    "items": [{"id": "W1", "intent": "i", "acceptance_criterion": "s", "covers": ["R1"]}],
                },
            }
        )
        h = nxt.compute_next(cid, cdir)
        self.assertEqual(h["action"], "waves")
        self.assertEqual(h["item_ids"], ["W1"])


if __name__ == "__main__":
    unittest.main()

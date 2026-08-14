#!/usr/bin/env python3
"""Unit tests for solidsdd-report collect.py."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import collect  # noqa: E402

CONTEXT_MD = """# Change context: demo

## 1. Demand and problem
Users need a thing.

## 2. Drivers and constraints
None.

## 3. Functional intent
Do the thing.

## 4. Non-functional requirements
N/A

## 5. Technology selection
Use the existing stack.

## 6. Key judgments and trade-offs
Working language: en (from config.yaml)
Server is authority.

## 7. Open questions
None.

## 8. Links
- requirements/demo.feature
"""

FEATURE = """Feature: Demo

  @R1 @SC1
  Scenario: Do thing
    Given a precondition
    When an action
    Then a result
"""

COLLIDING_FEATURE = """Feature: Unrelated prior change

  @R1 @SC1
  Scenario: Unrelated scenario from another change
    Given something else
    When it happens
    Then nothing to do with this change follows
"""


class CollectTests(unittest.TestCase):
    def _build_project(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        change_dir = root / ".solidsdd" / "changes" / "demo"
        change_dir.mkdir(parents=True)
        (root / ".solidsdd" / "active-change.json").write_text(
            json.dumps({"version": "1", "change_id": "demo"}), encoding="utf-8"
        )
        (change_dir / "change-context.md").write_text(CONTEXT_MD, encoding="utf-8")
        (change_dir / "change-brief.json").write_text(
            json.dumps(
                {
                    "version": "1",
                    "change_id": "demo",
                    "summary": "s",
                    "goal": "g",
                    "in_scope": [{"id": "R1", "text": "Do the thing"}, {"id": "R2", "text": "Not covered"}],
                    "out_of_scope": [{"id": "X1", "text": "Not this"}],
                    "success_criteria": [{"id": "SC1", "text": "It works"}],
                }
            ),
            encoding="utf-8",
        )
        (change_dir / "work-plan.json").write_text(
            json.dumps(
                {
                    "version": "1",
                    "items": [
                        {
                            "id": "W1",
                            "intent": "do it",
                            "acceptance_criterion": "Scenario: Do thing",
                            "covers": ["R1", "SC1"],
                            "depends_on": [],
                            "status": "done",
                            "feature_path": "requirements/demo.feature",
                            "scenario_name": "Do thing",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (change_dir / "nfr.json").write_text(
            json.dumps(
                {
                    "version": "1",
                    "change_id": "demo",
                    "items": [
                        {"id": f"NFR{i}", "quality": q, "status": "out_of_scope", "requirement": "N/A", "rationale": "n/a"}
                        for i, q in enumerate(
                            ["reliability", "security", "performance", "operability", "compatibility", "maintainability"],
                            start=1,
                        )
                    ],
                }
            ),
            encoding="utf-8",
        )
        (change_dir / "architecture-plan.json").write_text(
            json.dumps(
                {
                    "version": "1",
                    "status": "changed",
                    "change_id": "demo",
                    "modules": [
                        {"id": "a", "responsibility": "owns a"},
                        {"id": "b", "responsibility": "owns b"},
                    ],
                    "dependencies": [{"from": "a", "to": "b", "kind": "runtime"}],
                    "constraints": [{"type": "forbid_dependency", "from": "b", "to": "a", "reason": "keep a reusable"}],
                }
            ),
            encoding="utf-8",
        )
        items_dir = change_dir / "items" / "W1"
        items_dir.mkdir(parents=True)
        (items_dir / "application-plan.json").write_text(
            json.dumps(
                {
                    "version": "1",
                    "targets": [
                        {
                            "kind": "api",
                            "location": "openapi/openapi.yaml#/paths/~1thing/post",
                            "density": "standard",
                            "rationale": "r",
                            "adapter_hint": "openapi",
                            "status": "apply",
                            "covers": ["W1"],
                        },
                        {
                            "kind": "dbc",
                            "location": "contracts/Thing.ocl#do",
                            "density": "standard",
                            "rationale": "r",
                            "adapter_hint": "ocl",
                            "status": "apply",
                            "covers": ["W1"],
                        },
                        {
                            "kind": "formal",
                            "location": "formal/",
                            "density": "thin",
                            "rationale": "r",
                            "adapter_hint": "defer-formal",
                            "status": "defer",
                            "covers": ["W1"],
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        req_dir = root / "requirements"
        req_dir.mkdir()
        (req_dir / "demo.feature").write_text(FEATURE, encoding="utf-8")
        # A prior, unrelated change's Feature file reusing the same @R1/@SC1
        # tag names by coincidence (ids are only unique within one Brief).
        (req_dir / "unrelated.feature").write_text(COLLIDING_FEATURE, encoding="utf-8")

        (root / "openapi").mkdir()
        (root / "openapi" / "openapi.yaml").write_text("openapi: 3.0.3\n", encoding="utf-8")
        (root / "contracts").mkdir()
        (root / "contracts" / "Thing.ocl").write_text("-- contract\ncontext Thing\n", encoding="utf-8")
        (root / "formal").mkdir()
        (root / "formal" / "Thing.tla").write_text("---- MODULE Thing ----\n====\n", encoding="utf-8")
        return root

    def test_presence_and_coverage(self) -> None:
        root = self._build_project()
        data = collect.collect(root, "demo")
        self.assertEqual(data["change_id"], "demo")
        s = data["sections"]
        self.assertEqual(s["demand"]["state"], "present")
        self.assertEqual(s["functional_requirements"]["state"], "present")
        self.assertEqual(s["non_functional_requirements"]["state"], "present")
        self.assertEqual(s["technology_selection"]["state"], "present")
        self.assertEqual(s["design"]["work_plan"]["state"], "present")
        self.assertEqual(s["design"]["architecture_plan"]["state"], "present")
        self.assertEqual(s["design"]["architecture_plan"]["status"], "changed")
        self.assertEqual(s["design"]["application_plan"]["state"], "present")
        self.assertEqual(s["design"]["api_contract"]["state"], "present")
        self.assertEqual(s["design"]["dbc"]["state"], "present")
        self.assertEqual(s["design"]["formal"]["state"], "present")
        self.assertEqual(s["key_judgments"]["state"], "present")

        by_id = {row["id"]: row for row in data["coverage_matrix"]}
        self.assertEqual(by_id["R1"]["covered_by"], ["W1"])
        self.assertFalse(by_id["R1"]["uncovered"])
        self.assertTrue(by_id["R2"]["uncovered"])
        self.assertEqual(by_id["R2"]["covered_by"], [])

    def test_cross_change_tag_collision_is_not_pulled_in(self) -> None:
        root = self._build_project()
        data = collect.collect(root, "demo")
        tied_names = {s["name"] for s in data["artifacts"]["tied_scenarios"]}
        self.assertIn("Do thing", tied_names)
        self.assertNotIn("Unrelated scenario from another change", tied_names)
        self.assertNotIn("requirements/unrelated.feature", data["source_artifacts"])

    def test_diagram_eligibility(self) -> None:
        root = self._build_project()
        data = collect.collect(root, "demo")
        diagrams = data["diagrams"]
        self.assertTrue(diagrams["architecture"]["eligible"])
        self.assertEqual(len(diagrams["architecture"]["forbidden_edges"]), 1)
        # Only one WorkPlan item and no depends_on edges -> not eligible.
        self.assertFalse(diagrams["work_plan"]["eligible"])
        # 3 distinct (kind, location) targets -> eligible.
        self.assertTrue(diagrams["application_plan"]["eligible"])
        self.assertEqual(len(diagrams["application_plan"]["right_nodes"]), 3)

    def test_missing_change_falls_back_to_not_performed(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        change_dir = root / ".solidsdd" / "changes" / "empty"
        change_dir.mkdir(parents=True)
        (root / ".solidsdd" / "active-change.json").write_text(
            json.dumps({"version": "1", "change_id": "empty"}), encoding="utf-8"
        )
        data = collect.collect(root, None)
        s = data["sections"]
        self.assertEqual(s["demand"]["state"], "not_performed")
        self.assertEqual(s["design"]["work_plan"]["state"], "not_performed")
        self.assertEqual(s["design"]["architecture_plan"]["state"], "not_performed")
        self.assertEqual(data["coverage_matrix"], [])

    def test_language_hint_from_config(self) -> None:
        root = self._build_project()
        (root / ".solidsdd" / "config.yaml").write_text('working_language: "ja"\n', encoding="utf-8")
        data = collect.collect(root, "demo")
        self.assertEqual(data["language_hint"], {"value": "ja", "source": "config.yaml"})
        self.assertEqual(data["status_labels"]["present"], "実施済")


if __name__ == "__main__":
    unittest.main()

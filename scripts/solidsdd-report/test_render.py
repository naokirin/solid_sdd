#!/usr/bin/env python3
"""Unit tests for solidsdd-report render.py."""
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
import render  # noqa: E402

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


class RenderTests(unittest.TestCase):
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
                    "in_scope": [{"id": "R1", "text": "Do the thing"}],
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
        req_dir = root / "requirements"
        req_dir.mkdir()
        (req_dir / "demo.feature").write_text(FEATURE, encoding="utf-8")
        (root / "openapi").mkdir()
        (root / "openapi" / "openapi.yaml").write_text("openapi: 3.0.3\ninfo:\n  title: Demo\n", encoding="utf-8")
        return root

    def test_markdown_is_mechanical_and_embeds_verbatim_scenario(self) -> None:
        root = self._build_project()
        data = collect.collect(root, "demo")
        md = render.render_markdown(data, {}, root)
        self.assertIn("# Change report: demo", md)
        self.assertIn("Users need a thing.", md)  # verbatim §1 copy, no LLM authorship
        self.assertIn("Given a precondition", md)  # verbatim Gherkin block
        self.assertIn("| R1 | Do the thing |", md)
        self.assertIn("Not performed", md)  # ArchitecturePlan/ApplicationPlan absent

    def test_narrative_summaries_are_used_when_supplied(self) -> None:
        root = self._build_project()
        data = collect.collect(root, "demo")
        md = render.render_markdown(data, {"api_contract_summary": "Custom summary text."}, root)
        self.assertIn("Custom summary text.", md)

    def test_links_are_relative_to_report_location_not_project_root(self) -> None:
        # report.md/report.html live under .solidsdd/changes/<id>/, so a
        # project-root-relative path like "requirements/demo.feature" must
        # be emitted as "../../../requirements/demo.feature", not bare.
        root = self._build_project()
        data = collect.collect(root, "demo")
        md = render.render_markdown(data, {}, root)
        self.assertIn("](../../../requirements/demo.feature)", md)
        self.assertNotIn("](requirements/demo.feature)", md)
        out = render.render_html(data, {}, root)
        self.assertIn('href="../../../requirements/demo.feature"', out)

    def test_html_is_self_contained_and_dark_themed(self) -> None:
        root = self._build_project()
        data = collect.collect(root, "demo")
        out = render.render_html(data, {}, root)
        self.assertTrue(out.startswith("<!doctype html>"))
        self.assertIn("color-scheme: dark", out)
        self.assertIn("tok-key", out)  # TOKEN_CSS inlined
        self.assertNotIn("cdn.", out)  # no external CDN reference

    def test_write_report_writes_both_formats_to_change_dir(self) -> None:
        root = self._build_project()
        written = render.write_report(root, "demo", {}, {"markdown", "html"})
        self.assertTrue(Path(written["markdown"]).is_file())
        self.assertTrue(Path(written["html"]).is_file())
        self.assertTrue(written["markdown"].endswith(".solidsdd/changes/demo/report.md"))


if __name__ == "__main__":
    unittest.main()

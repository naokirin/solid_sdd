#!/usr/bin/env python3
"""Unit tests for solidsdd-architecture physical.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import dsl  # noqa: E402
import physical  # noqa: E402

WS_TEXT = """
workspace "W" {
  model {
    inventory = softwareSystem "Inventory" "Owns available stock" {
      properties { "owns" "Stock" }
    }
    reservation = softwareSystem "Reservation" "Owns hold lifecycle" {
      properties { "owns" "Hold" }
    }
    reservation -> inventory "Reads and adjusts available stock" "runtime"
  }
}
"""

INVARIANTS = {
    "version": "1",
    "constraints": [
        {
            "type": "forbid_dependency",
            "from": "inventory",
            "to": "reservation",
            "reason": "keep inventory reusable",
        },
    ],
}


class ValidatePhysicalDesignTests(unittest.TestCase):
    def _root(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def _write(self, root: Path, text: str) -> Path:
        path = root / "physical-design.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_file_is_noop(self) -> None:
        root = self._root()
        ws = dsl.parse(WS_TEXT)
        findings = physical.validate_physical_design(
            root / "physical-design.md", ws, INVARIANTS
        )
        self.assertEqual(findings, [])

    def test_workspace_missing_flags_major(self) -> None:
        root = self._root()
        path = self._write(
            root,
            "# Physical Design\n\n## Logical Elements\n\n- Inventory\n",
        )
        findings = physical.validate_physical_design(path, None, None)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "major")

    def test_known_logical_elements_have_no_findings(self) -> None:
        root = self._root()
        text = """# Physical Design

## Logical Elements

- Inventory
- Reservation

## Physical Realization

| Logical Element | Physical Realization |
|---|---|
| Inventory | `src/domain/inventory/` |
| Reservation | `src/domain/inventory/reservation/` |
"""
        path = self._write(root, text)
        ws = dsl.parse(WS_TEXT)
        findings = physical.validate_physical_design(path, ws, INVARIANTS)
        self.assertEqual(findings, [])

    def test_unknown_logical_element_is_flagged(self) -> None:
        root = self._root()
        text = """# Physical Design

## Logical Elements

- Payment
"""
        path = self._write(root, text)
        ws = dsl.parse(WS_TEXT)
        findings = physical.validate_physical_design(path, ws, INVARIANTS)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "major")
        self.assertIn("Payment", findings[0]["detail"])

    def test_physical_dependency_violating_forbid_dependency_is_blocker(self) -> None:
        root = self._root()
        text = """# Physical Design

## Physical Realization

| Logical Element | Physical Realization |
|---|---|
| Inventory | `src/inventory/` |
| Reservation | `src/reservation/` |

## Physical Dependencies

- `src/inventory/` -> `src/reservation/`
"""
        path = self._write(root, text)
        ws = dsl.parse(WS_TEXT)
        findings = physical.validate_physical_design(path, ws, INVARIANTS)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "blocker")
        self.assertIn("forbid_dependency", findings[0]["detail"])

    def test_physical_dependency_reversed_from_logical_is_major(self) -> None:
        root = self._root()
        text = """# Physical Design

## Physical Realization

| Logical Element | Physical Realization |
|---|---|
| Inventory | `src/inventory/` |
| Reservation | `src/reservation/` |

## Physical Dependencies

- `src/inventory/` -> `src/reservation/`
"""
        path = self._write(root, text)
        # Logical relationship is reservation -> inventory; forbid the opposite
        # pair so only the "reversed direction" check (not forbid_dependency)
        # fires for inventory -> reservation.
        ws = dsl.parse(WS_TEXT)
        invariants = {"version": "1", "constraints": []}
        findings = physical.validate_physical_design(path, ws, invariants)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "major")
        self.assertIn("opposite", findings[0]["detail"])

    def test_physical_dependency_matching_logical_direction_has_no_findings(self) -> None:
        root = self._root()
        text = """# Physical Design

## Physical Realization

| Logical Element | Physical Realization |
|---|---|
| Inventory | `src/inventory/` |
| Reservation | `src/reservation/` |

## Physical Dependencies

- `src/reservation/` -> `src/inventory/`
"""
        path = self._write(root, text)
        ws = dsl.parse(WS_TEXT)
        invariants = {"version": "1", "constraints": []}
        findings = physical.validate_physical_design(path, ws, invariants)
        self.assertEqual(findings, [])

    def test_unresolvable_dependency_line_is_skipped(self) -> None:
        root = self._root()
        text = """# Physical Design

## Physical Dependencies

- `src/unknown-a/` -> `src/unknown-b/`
"""
        path = self._write(root, text)
        ws = dsl.parse(WS_TEXT)
        findings = physical.validate_physical_design(path, ws, INVARIANTS)
        self.assertEqual(findings, [])

    def test_free_prose_without_sections_is_ignored(self) -> None:
        root = self._root()
        path = self._write(root, "# Physical Design\n\nJust some prose, no headings.\n")
        ws = dsl.parse(WS_TEXT)
        findings = physical.validate_physical_design(path, ws, INVARIANTS)
        self.assertEqual(findings, [])


class ValidatePhysicalDesignProjectTests(unittest.TestCase):
    def test_no_physical_design_file_is_noop(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".solidsdd").mkdir()
        change_dir = root / ".solidsdd" / "changes" / "demo"
        change_dir.mkdir(parents=True)

        from solidsdd_lib.paths import load_layout

        layout = load_layout(root)
        findings = physical.validate_physical_design_project(layout, change_dir)
        self.assertEqual(findings, [])

    def test_project_root_wrapper_cross_checks(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        arch_dir = root / ".solidsdd" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "workspace.dsl").write_text(WS_TEXT, encoding="utf-8")
        change_dir = root / ".solidsdd" / "changes" / "demo"
        change_dir.mkdir(parents=True)
        (change_dir / "physical-design.md").write_text(
            "# Physical Design\n\n## Logical Elements\n\n- Payment\n",
            encoding="utf-8",
        )

        from solidsdd_lib.paths import load_layout

        layout = load_layout(root)
        findings = physical.validate_physical_design_project(layout, change_dir)
        self.assertEqual(len(findings), 1)
        self.assertIn("Payment", findings[0]["detail"])


if __name__ == "__main__":
    unittest.main()

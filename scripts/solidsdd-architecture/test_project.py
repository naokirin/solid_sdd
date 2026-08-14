#!/usr/bin/env python3
"""Unit tests for solidsdd-architecture project.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import dsl  # noqa: E402
import project  # noqa: E402

WS_TEXT = """
workspace "W" {
  model {
    inventory = softwareSystem "Inventory" "Owns available stock" {
      tags "change:split1"
      properties { "owns" "Stock" ; "public" "InventoryService" }
    }
    reservation = softwareSystem "Reservation" "Owns hold lifecycle" {
      tags "change:split1"
      properties { "owns" "Hold" ; "public" "ReservationService" }
    }
    reservation -> inventory "Reads and adjusts available stock" "runtime" {
      tags "change:split1, kind:runtime"
    }
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
    "invariants": ["Inventory owns stock state."],
}


class ProjectTests(unittest.TestCase):
    def test_changed_projection_shape(self) -> None:
        ws = dsl.parse(WS_TEXT)
        plan = project.project(ws, INVARIANTS, "split1")
        self.assertEqual(plan["version"], "1")
        self.assertEqual(plan["status"], "changed")
        self.assertEqual(plan["change_id"], "split1")

        module_ids = {m["id"] for m in plan["modules"]}
        self.assertEqual(module_ids, {"inventory", "reservation"})

        inv_module = next(m for m in plan["modules"] if m["id"] == "inventory")
        self.assertEqual(inv_module["responsibility"], "Owns available stock")
        self.assertEqual(inv_module["owns"], ["Stock"])
        self.assertEqual(inv_module["public"], ["InventoryService"])

        self.assertEqual(len(plan["dependencies"]), 1)
        dep = plan["dependencies"][0]
        self.assertEqual(dep["from"], "reservation")
        self.assertEqual(dep["to"], "inventory")
        self.assertEqual(dep["kind"], "runtime")

        constraint_types = {c["type"] for c in plan["constraints"]}
        self.assertIn("forbid_dependency", constraint_types)
        fd = next(c for c in plan["constraints"] if c["type"] == "forbid_dependency")
        self.assertEqual(fd["from"], "inventory")
        self.assertEqual(fd["to"], "reservation")

    def test_unchanged_when_nothing_tagged(self) -> None:
        ws = dsl.parse(WS_TEXT.replace('tags "change:split1"', 'tags "unrelated"'))
        plan = project.project(ws, INVARIANTS, "other-change")
        self.assertEqual(plan["status"], "unchanged")
        self.assertNotIn("modules", plan)
        self.assertNotIn("dependencies", plan)
        self.assertNotIn("constraints", plan)

    def test_project_project_root_no_architecture_dir(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".solidsdd").mkdir()
        plan = project.project_project_root(root, "some-change")
        self.assertEqual(plan["status"], "unchanged")
        self.assertNotIn("modules", plan)

    def test_project_project_root_workspace_without_invariants_file(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        arch_dir = root / ".solidsdd" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "workspace.dsl").write_text(
            'workspace "W" { model { a = softwareSystem "A" { tags "change:demo" } } }',
            encoding="utf-8",
        )
        plan = project.project_project_root(root, "demo")
        self.assertEqual(plan["status"], "changed")
        self.assertEqual(plan["modules"][0]["id"], "a")
        self.assertEqual(plan["constraints"], [])

    def test_underscore_ids_become_hyphenated_module_ids(self) -> None:
        text = """
        workspace "W" {
          model {
            my_module = softwareSystem "My Module" "Desc" {
              tags "change:demo"
            }
          }
        }
        """
        ws = dsl.parse(text)
        plan = project.project(ws, {"version": "1"}, "demo")
        self.assertEqual(plan["modules"][0]["id"], "my-module")


if __name__ == "__main__":
    unittest.main()

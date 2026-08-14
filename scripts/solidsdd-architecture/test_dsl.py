#!/usr/bin/env python3
"""Unit tests for the solidsdd-architecture DSL parser."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import dsl  # noqa: E402

SAMPLE = """
// sample workspace
workspace "Inventory" "Sample" {
  model {
    inventory = softwareSystem "Inventory" "Owns stock" {
      tags "Domain"
      properties {
        "owns" "Stock"
      }
      inventory_service = container "InventoryService" "Facade" "TypeScript" {
        tags "Public"
        internal_repo = component "Repo" "Internal storage"
      }
    }
    reservation = softwareSystem "Reservation" "Owns holds" {
      properties { "owns" "Hold" }
    }
    reservation -> inventory "Reserves stock" "runtime" {
      tags "change:demo"
    }
  }
  views {
    systemContext inventory {
      include *
      autoLayout
    }
  }
}
"""


class DslParserTests(unittest.TestCase):
    def test_parses_elements_relationships_views(self) -> None:
        ws = dsl.parse(SAMPLE)
        self.assertEqual(ws.name, "Inventory")
        self.assertIn("inventory", ws.elements)
        self.assertIn("inventory_service", ws.elements)
        self.assertIn("internal_repo", ws.elements)
        self.assertIn("reservation", ws.elements)

        inv = ws.elements["inventory"]
        self.assertEqual(inv.kind, "softwareSystem")
        self.assertEqual(inv.tags, ["Domain"])
        self.assertEqual(inv.properties.get("owns"), "Stock")

        svc = ws.elements["inventory_service"]
        self.assertEqual(svc.kind, "container")
        self.assertEqual(svc.parent_id, "inventory")
        self.assertEqual(svc.tags, ["Public"])

        repo = ws.elements["internal_repo"]
        self.assertEqual(repo.kind, "component")
        self.assertEqual(repo.parent_id, "inventory_service")

        self.assertEqual(len(ws.relationships), 1)
        rel = ws.relationships[0]
        self.assertEqual(rel.source, "reservation")
        self.assertEqual(rel.dest, "inventory")
        self.assertEqual(rel.description, "Reserves stock")
        self.assertEqual(rel.technology, "runtime")
        self.assertEqual(rel.tags, ["change:demo"])

        self.assertEqual(len(ws.views), 1)
        view = ws.views[0]
        self.assertEqual(view.kind, "systemContext")
        self.assertEqual(view.element_id, "inventory")
        self.assertTrue(view.include_all)

    def test_unsupported_construct_raises(self) -> None:
        text = """
        workspace "W" {
          model {
            u = person "User"
          }
        }
        """
        with self.assertRaises(dsl.DslSyntaxError):
            dsl.parse(text)

    def test_duplicate_identifier_raises(self) -> None:
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A"
            a = softwareSystem "B"
          }
        }
        """
        with self.assertRaises(dsl.DslSyntaxError):
            dsl.parse(text)

    def test_bad_identifier_pattern_raises(self) -> None:
        text = """
        workspace "W" {
          model {
            MyThing = softwareSystem "A"
          }
        }
        """
        with self.assertRaises(dsl.DslSyntaxError):
            dsl.parse(text)

    def test_unclosed_brace_raises(self) -> None:
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A"
        }
        """
        with self.assertRaises(dsl.DslSyntaxError):
            dsl.parse(text)

    def test_relationship_to_unknown_kind_at_wrong_depth_raises(self) -> None:
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A" {
              b = softwareSystem "B"
            }
          }
        }
        """
        with self.assertRaises(dsl.DslSyntaxError):
            dsl.parse(text)


if __name__ == "__main__":
    unittest.main()

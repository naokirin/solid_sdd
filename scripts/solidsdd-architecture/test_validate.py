#!/usr/bin/env python3
"""Unit tests for solidsdd-architecture validate.py."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import validate  # noqa: E402


def _write(root: Path, workspace_dsl: str, invariants_yaml: str | None = None) -> tuple[Path, Path]:
    ws_path = root / "workspace.dsl"
    ws_path.write_text(workspace_dsl, encoding="utf-8")
    inv_path = root / "invariants.yaml"
    if invariants_yaml is not None:
        inv_path.write_text(invariants_yaml, encoding="utf-8")
    return ws_path, inv_path


CLEAN_WS = """
workspace "W" {
  model {
    inventory = softwareSystem "Inventory" "Owns stock" {
      properties { "owns" "Stock" }
    }
    reservation = softwareSystem "Reservation" "Owns holds" {
      properties { "owns" "Hold" }
    }
    reservation -> inventory "Reserves stock" "runtime" {
      tags "change:demo"
    }
  }
}
"""

CLEAN_INVARIANTS = """
version: "1"
constraints:
  - type: forbid_dependency
    from: inventory
    to: reservation
    reason: keep inventory reusable
invariants:
  - "Inventory owns stock state."
"""


class ValidateTests(unittest.TestCase):
    def _root(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_clean_model_has_no_findings(self) -> None:
        root = self._root()
        ws, inv = _write(root, CLEAN_WS, CLEAN_INVARIANTS)
        findings = validate.validate(ws, inv)
        self.assertEqual(findings, [])

    def test_unknown_element_in_relationship(self) -> None:
        root = self._root()
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A"
            a -> ghost "uses"
          }
        }
        """
        ws, inv = _write(root, text)
        findings = validate.validate(ws, inv)
        self.assertTrue(
            any("ghost" in f["detail"] and f["severity"] == "blocker" for f in findings)
        )

    def test_forbid_dependency_violation(self) -> None:
        root = self._root()
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A"
            b = softwareSystem "B"
            a -> b "uses" { tags "change:demo" }
          }
        }
        """
        inv_text = """
        version: "1"
        constraints:
          - type: forbid_dependency
            from: a
            to: b
        """
        ws, inv = _write(root, text, inv_text)
        findings = validate.validate(ws, inv)
        self.assertTrue(
            any(
                "violates forbid_dependency" in f["detail"] and f["severity"] == "blocker"
                for f in findings
            )
        )

    def test_no_cycles_detects_cycle(self) -> None:
        root = self._root()
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A"
            b = softwareSystem "B"
            a -> b "uses"
            b -> a "uses back"
          }
        }
        """
        inv_text = """
        version: "1"
        constraints:
          - type: no_cycles
            scope: all
        """
        ws, inv = _write(root, text, inv_text)
        findings = validate.validate(ws, inv)
        self.assertTrue(
            any("dependency cycle" in f["detail"] and f["severity"] == "major" for f in findings)
        )

    def test_ownership_conflict(self) -> None:
        root = self._root()
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A" { properties { "owns" "Stock" } }
            b = softwareSystem "B" { properties { "owns" "Stock" } }
          }
        }
        """
        ws, inv = _write(root, text)
        findings = validate.validate(ws, inv)
        self.assertTrue(
            any("ownership conflict" in f["detail"] and f["severity"] == "major" for f in findings)
        )

    def test_boundary_leakage_on_internal_component(self) -> None:
        root = self._root()
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A"
            b = softwareSystem "B" {
              b_container = container "Container" {
                b_internal = component "Internal"
              }
            }
            a -> b_internal "reaches into B"
          }
        }
        """
        ws, inv = _write(root, text)
        findings = validate.validate(ws, inv)
        self.assertTrue(
            any("internal component" in f["detail"] and f["severity"] == "major" for f in findings)
        )

    def test_public_component_allows_cross_boundary_access(self) -> None:
        root = self._root()
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A"
            b = softwareSystem "B" {
              b_container = container "Container" {
                b_service = component "Service" "" "" { tags "Public" }
              }
            }
            a -> b_service "calls"
          }
        }
        """
        ws, inv = _write(root, text)
        findings = validate.validate(ws, inv)
        self.assertEqual(
            [f for f in findings if "internal component" in f["detail"]], []
        )

    def test_parent_child_relationship_is_rejected(self) -> None:
        root = self._root()
        text = """
        workspace "W" {
          model {
            a = softwareSystem "A" {
              a_container = container "AContainer"
            }
            a -> a_container "reaches into its own child"
          }
        }
        """
        ws, inv = _write(root, text)
        findings = validate.validate(ws, inv)
        self.assertTrue(
            any(
                "parent and its own child" in f["detail"] and f["severity"] == "blocker"
                for f in findings
            )
        )

    def test_dsl_syntax_error_becomes_blocker_finding(self) -> None:
        root = self._root()
        text = 'workspace "W" { model { a = person "User" } }'
        ws, inv = _write(root, text)
        findings = validate.validate(ws, inv)
        self.assertTrue(any(f["severity"] == "blocker" for f in findings))


class StructurizrCliTests(unittest.TestCase):
    def test_find_structurizr_cli_prefers_env_override(self) -> None:
        with mock.patch.dict(os.environ, {"STRUCTURIZR_CLI": "/opt/structurizr.sh"}):
            self.assertEqual(validate.find_structurizr_cli(), "/opt/structurizr.sh")

    def test_find_structurizr_cli_none_when_absent(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "STRUCTURIZR_CLI"}
        env["PATH"] = ""
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertIsNone(validate.find_structurizr_cli())

    def test_run_structurizr_cli_ok_on_zero_exit(self) -> None:
        fake = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch("subprocess.run", return_value=fake):
            ok, output = validate.run_structurizr_cli("structurizr.sh", Path("workspace.dsl"))
        self.assertTrue(ok)

    def test_run_structurizr_cli_reports_failure_output(self) -> None:
        fake = mock.Mock(returncode=1, stdout="", stderr="boom")
        with mock.patch("subprocess.run", return_value=fake):
            ok, output = validate.run_structurizr_cli("structurizr.sh", Path("workspace.dsl"))
        self.assertFalse(ok)
        self.assertIn("boom", output)

    def test_main_with_structurizr_cli_flag_errors_when_not_found(self) -> None:
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        arch_dir = Path(root.name) / ".solidsdd" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "workspace.dsl").write_text(
            'workspace "W" { model { a = softwareSystem "A" } }', encoding="utf-8"
        )
        env = {k: v for k, v in os.environ.items() if k != "STRUCTURIZR_CLI"}
        env["PATH"] = ""
        with mock.patch.dict(os.environ, env, clear=True):
            rc = validate.main(["--project-root", root.name, "--with-structurizr-cli"])
        self.assertEqual(rc, 2)

    def test_main_without_flag_never_looks_for_cli(self) -> None:
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        arch_dir = Path(root.name) / ".solidsdd" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "workspace.dsl").write_text(
            'workspace "W" { model { a = softwareSystem "A" } }', encoding="utf-8"
        )
        with mock.patch.object(validate, "find_structurizr_cli") as m:
            rc = validate.main(["--project-root", root.name])
        m.assert_not_called()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

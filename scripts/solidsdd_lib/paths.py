"""Project path layout from .solidsdd/config.yaml (or SOLIDSDD_DIR)."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

CHANGE_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

DEFAULT_PATHS: dict[str, Any] = {
    "solidsdd": ".solidsdd",
    "active_change": ".solidsdd/active-change.json",
    "changes": ".solidsdd/changes",
    "host_toolchain": ".solidsdd/host-toolchain.json",
    "kg": ".solidsdd/kg",
    "architecture": ".solidsdd/architecture",
    "cache": ".solidsdd-cache",
    "knowledge": ["knowledge"],
    "requirements": "requirements",
    "requirements_glob": "requirements/**/*.feature",
    "openapi": "openapi/openapi.yaml",
    "graphql": "graphql/schema.graphql",
    "contracts": "contracts",
    "formal": "formal",
    "contract_tests_ts": "tests/contracts",
    "contract_tests_ruby": "spec/contracts",
}


@dataclass(frozen=True)
class Layout:
    """Resolved project-relative path layout."""

    project_root: Path
    solidsdd: str = ".solidsdd"
    active_change: str = ".solidsdd/active-change.json"
    changes: str = ".solidsdd/changes"
    host_toolchain: str = ".solidsdd/host-toolchain.json"
    kg: str = ".solidsdd/kg"
    architecture: str = ".solidsdd/architecture"
    cache: str = ".solidsdd-cache"
    knowledge: tuple[str, ...] = ("knowledge",)
    requirements: str = "requirements"
    requirements_glob: str = "requirements/**/*.feature"
    openapi: str = "openapi/openapi.yaml"
    graphql: str = "graphql/schema.graphql"
    contracts: str = "contracts"
    formal: str = "formal"
    contract_tests_ts: str = "tests/contracts"
    contract_tests_ruby: str = "spec/contracts"
    config_path: Path | None = None

    def abs(self, rel: str) -> Path:
        p = Path(rel)
        if p.is_absolute():
            return p
        return self.project_root / p

    def solidsdd_dir(self) -> Path:
        return self.abs(self.solidsdd)

    def active_change_path(self) -> Path:
        return self.abs(self.active_change)

    def changes_dir(self) -> Path:
        return self.abs(self.changes)

    def host_toolchain_path(self) -> Path:
        return self.abs(self.host_toolchain)

    def kg_dir(self) -> Path:
        return self.abs(self.kg)

    def architecture_dir(self) -> Path:
        return self.abs(self.architecture)

    def cache_dir(self) -> Path:
        return self.abs(self.cache)

    def openapi_path(self) -> Path:
        return self.abs(self.openapi)

    def requirements_dir(self) -> Path:
        return self.abs(self.requirements)

    def knowledge_dirs(self) -> list[Path]:
        return [self.abs(d) for d in self.knowledge]

    def brief_glob(self) -> str:
        return f"{self.changes.rstrip('/') }/*/change-brief.json"

    def change_dir(self, change_id: str) -> Path:
        return self.changes_dir() / change_id


def discover_solidsdd_rel(project_root: Path, env: dict[str, str] | None = None) -> str:
    """Return project-relative meta root (SOLIDSDD_DIR or .solidsdd)."""
    environ = env if env is not None else os.environ
    raw = (environ.get("SOLIDSDD_DIR") or "").strip()
    if not raw:
        return ".solidsdd"
    p = Path(raw)
    if p.is_absolute():
        try:
            return str(p.relative_to(project_root.resolve()))
        except ValueError as e:
            raise SystemExit(
                f"SOLIDSDD_DIR {raw!r} must be under project root {project_root}"
            ) from e
    return raw.replace("\\", "/")


def _require_yaml() -> Any:
    if yaml is None:
        raise SystemExit(
            "solidsdd path config requires the PyYAML package "
            "(pip install PyYAML)"
        )
    return yaml


def _apply_path_overrides(merged: dict[str, Any], overrides: dict[str, Any] | None) -> None:
    if not overrides:
        return
    for key, value in overrides.items():
        if key not in DEFAULT_PATHS:
            raise SystemExit(f"unknown paths key in config.yaml: {key!r}")
        if value is None:
            continue
        if key == "knowledge":
            if not isinstance(value, list) or not value:
                raise SystemExit("paths.knowledge must be a non-empty list of strings")
            if not all(isinstance(x, str) and x for x in value):
                raise SystemExit("paths.knowledge entries must be non-empty strings")
            merged[key] = list(value)
        else:
            if not isinstance(value, str) or not value:
                raise SystemExit(f"paths.{key} must be a non-empty string")
            merged[key] = value


def _layout_from_merged(
    project_root: Path, merged: dict[str, Any], config_path: Path | None
) -> Layout:
    knowledge = merged["knowledge"]
    if isinstance(knowledge, list):
        knowledge_t = tuple(knowledge)
    else:
        knowledge_t = (str(knowledge),)
    return Layout(
        project_root=project_root,
        solidsdd=merged["solidsdd"],
        active_change=merged["active_change"],
        changes=merged["changes"],
        host_toolchain=merged["host_toolchain"],
        kg=merged["kg"],
        architecture=merged["architecture"],
        cache=merged["cache"],
        knowledge=knowledge_t,
        requirements=merged["requirements"],
        requirements_glob=merged["requirements_glob"],
        openapi=merged["openapi"],
        graphql=merged["graphql"],
        contracts=merged["contracts"],
        formal=merged["formal"],
        contract_tests_ts=merged["contract_tests_ts"],
        contract_tests_ruby=merged["contract_tests_ruby"],
        config_path=config_path,
    )


def load_layout(
    project_root: Path | str,
    *,
    env: dict[str, str] | None = None,
) -> Layout:
    """Load layout for a consuming project. Missing config.yaml → defaults."""
    root = Path(project_root).resolve()
    discovered = discover_solidsdd_rel(root, env=env)
    config_path = root / discovered / "config.yaml"
    merged = dict(DEFAULT_PATHS)
    # Bootstrap: defaults use .solidsdd; if SOLIDSDD_DIR relocates meta root,
    # rewrite default meta paths that still point at .solidsdd.
    if discovered != ".solidsdd":
        merged["solidsdd"] = discovered
        for key in ("active_change", "changes", "host_toolchain", "kg", "architecture"):
            val = merged[key]
            if isinstance(val, str) and val.startswith(".solidsdd"):
                merged[key] = discovered + val[len(".solidsdd") :]

    loaded_path: Path | None = None
    if config_path.is_file():
        y = _require_yaml()
        with config_path.open(encoding="utf-8") as f:
            data = y.safe_load(f)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise SystemExit(f"config.yaml must be a mapping: {config_path}")
        version = data.get("version")
        if version is not None and version != "1" and version != 1:
            raise SystemExit(
                f"unsupported config.yaml version {version!r} in {config_path}"
            )
        paths = data.get("paths")
        if paths is not None and not isinstance(paths, dict):
            raise SystemExit(f"paths must be a mapping in {config_path}")
        _apply_path_overrides(merged, paths if isinstance(paths, dict) else None)
        loaded_path = config_path

    layout = _layout_from_merged(root, merged, loaded_path)
    if layout.solidsdd.replace("\\", "/") != discovered.replace("\\", "/"):
        raise SystemExit(
            f"paths.solidsdd {layout.solidsdd!r} does not match discovery "
            f"{discovered!r} (SOLIDSDD_DIR or .solidsdd)"
        )
    return layout


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def resolve_change_dir(
    project: Path | str,
    change_id: str | None,
    *,
    layout: Layout | None = None,
    validate_change_id: bool = False,
) -> tuple[str, Path]:
    """Resolve change_id and change directory from active-change or argv."""
    root = Path(project).resolve()
    lay = layout or load_layout(root)
    active = lay.active_change_path()
    if change_id is None:
        if not active.is_file():
            raise SystemExit(f"no --change-id and no {lay.active_change}")
        change_id = load_json(active)["change_id"]
    if not isinstance(change_id, str):
        raise SystemExit(f"invalid change_id: {change_id!r}")
    if validate_change_id and not CHANGE_ID_RE.match(change_id):
        raise SystemExit(f"invalid change_id: {change_id!r}")
    change_dir = lay.change_dir(change_id)
    if not change_dir.is_dir():
        raise SystemExit(f"change directory missing: {change_dir}")
    return change_id, change_dir


def host_toolchain_source(layout: Layout) -> str:
    """Relative source string for run-state host_toolchain snapshot."""
    return layout.host_toolchain.replace("\\", "/")

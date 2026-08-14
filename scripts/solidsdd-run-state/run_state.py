#!/usr/bin/env python3
"""Constrained mutations for solidsdd-run / solidsdd-loop run-state.json.

Writes only under .solidsdd/changes/<change_id>/ (run-state.json; optionally
work-plan.json item status and status.json). No arbitrary code paths — argv
is enum / id / short note only. Validates against schemas/run-state.schema.json
after each write.

Commands:
  init                 create run-state.json with defaults (fail if exists unless --force)
  set-phase            set phase (schema enum)
  set-wave             set wave_index
  note --append TEXT   append isolation_notes (deduped)
  sync-items           populate/refresh items from work-plan.json
  set-item             update one item status / loop_phase; optional --sync-work-plan
  set-host-toolchain   snapshot .solidsdd/host-toolchain.json into run-state
  mark-change-done     status.json done + phase done
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    print("solidsdd-run-state requires the jsonschema package", file=sys.stderr)
    sys.exit(2)

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from solidsdd_lib.paths import (  # noqa: E402
    host_toolchain_source,
    load_layout,
    resolve_change_dir as _resolve_change_dir,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
CHANGE_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ITEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")
NOTE_MAX = 512

PHASES = [
    "context",
    "grill",
    "knowledge_consult",
    "intake",
    "critique_change_context",
    "brief",
    "critique_change_brief",
    "decompose",
    "critique_work_plan",
    "architecture",
    "critique_architecture",
    "waves",
    "integration_verify",
    "critique_integration",
    "knowledge_harvest",
    "critique_knowledge_harvest",
    "done",
    "stopped",
]

ITEM_STATUSES = ["pending", "ready", "running", "done", "blocked"]

LOOP_PHASES = [
    "context",
    "judge",
    "critique_application_plan",
    "apply",
    "derive_tests",
    "implement",
    "verify",
    "done",
    "stopped",
]

WORK_PLAN_ITEM_STATUSES = ["pending", "ready", "running", "done", "blocked"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def emit(ok: bool, path: Path, changed: list[str], **extra: Any) -> None:
    out: dict[str, Any] = {
        "ok": ok,
        "path": str(path),
        "changed": changed,
    }
    out.update(extra)
    print(json.dumps(out, ensure_ascii=False))


def resolve_change_dir(project: Path, change_id: str | None) -> tuple[str, Path]:
    return _resolve_change_dir(project, change_id, validate_change_id=True)


def run_state_path(change_dir: Path) -> Path:
    return change_dir / "run-state.json"


def load_schema() -> dict[str, Any]:
    return load_json(SCHEMAS / "run-state.schema.json")


def validate_run_state(data: dict[str, Any]) -> None:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)


def default_retry() -> dict[str, Any]:
    return {"remaining": 3, "max": 3, "last_suggested_skills": []}


def default_run_state(change_id: str) -> dict[str, Any]:
    return {
        "version": "1",
        "change_id": change_id,
        "phase": "intake",
        "wave_index": 0,
        "run_retry": default_retry(),
        "items": {},
        "isolation_notes": [],
        "updated_at": utc_now(),
    }


def require_run_state(change_dir: Path) -> dict[str, Any]:
    path = run_state_path(change_dir)
    if not path.is_file():
        raise SystemExit(f"run-state.json missing: {path} (run init first)")
    data = load_json(path)
    if not isinstance(data, dict):
        raise SystemExit("run-state.json must be an object")
    return data


def write_run_state(change_dir: Path, data: dict[str, Any], changed: list[str]) -> None:
    data["updated_at"] = utc_now()
    validate_run_state(data)
    path = run_state_path(change_dir)
    dump_json(path, data)
    emit(True, path, changed)


def cmd_init(project: Path, change_id: str | None, force: bool) -> None:
    cid, change_dir = resolve_change_dir(project, change_id)
    path = run_state_path(change_dir)
    if path.is_file() and not force:
        raise SystemExit(f"run-state.json already exists: {path} (use --force to overwrite)")
    data = default_run_state(cid)
    validate_run_state(data)
    dump_json(path, data)
    emit(True, path, ["created"] if not force else ["overwritten"])


def cmd_set_phase(project: Path, change_id: str | None, phase: str) -> None:
    if phase not in PHASES:
        raise SystemExit(f"invalid phase {phase!r}; want one of {PHASES}")
    _, change_dir = resolve_change_dir(project, change_id)
    data = require_run_state(change_dir)
    data["phase"] = phase
    write_run_state(change_dir, data, ["phase"])


def cmd_set_wave(project: Path, change_id: str | None, index: int) -> None:
    if index < 0:
        raise SystemExit("wave index must be >= 0")
    _, change_dir = resolve_change_dir(project, change_id)
    data = require_run_state(change_dir)
    data["wave_index"] = index
    write_run_state(change_dir, data, ["wave_index"])


def cmd_note(project: Path, change_id: str | None, text: str) -> None:
    text = text.strip()
    if not text:
        raise SystemExit("note text must be non-empty")
    if len(text) > NOTE_MAX:
        raise SystemExit(f"note text exceeds {NOTE_MAX} characters")
    if "\n" in text or "\r" in text:
        raise SystemExit("note text must be a single line")
    _, change_dir = resolve_change_dir(project, change_id)
    data = require_run_state(change_dir)
    notes = list(data.get("isolation_notes") or [])
    path = run_state_path(change_dir)
    if text in notes:
        emit(True, path, [], note="already_present")
        return
    notes.append(text)
    data["isolation_notes"] = notes
    write_run_state(change_dir, data, ["isolation_notes"])


def work_plan_item_status(wp: dict[str, Any], item_id: str) -> str | None:
    for it in wp.get("items") or []:
        if isinstance(it, dict) and it.get("id") == item_id:
            st = it.get("status")
            return st if isinstance(st, str) else None
    return None


def cmd_sync_items(project: Path, change_id: str | None) -> None:
    _, change_dir = resolve_change_dir(project, change_id)
    wp_path = change_dir / "work-plan.json"
    if not wp_path.is_file():
        raise SystemExit(f"work-plan.json missing: {wp_path}")
    wp = load_json(wp_path)
    if not isinstance(wp, dict):
        raise SystemExit("work-plan.json must be an object")
    data = require_run_state(change_dir)
    items = dict(data.get("items") or {})
    changed_keys: list[str] = []
    for it in wp.get("items") or []:
        if not isinstance(it, dict):
            continue
        iid = it.get("id")
        if not isinstance(iid, str) or not ITEM_ID_RE.match(iid):
            raise SystemExit(f"invalid work-plan item id: {iid!r}")
        status = it.get("status")
        if status not in ITEM_STATUSES:
            # WorkPlan may use pending/ready; map unknown to pending
            status = "pending" if status is None else status
        if status not in ITEM_STATUSES:
            raise SystemExit(f"invalid item status for {iid}: {status!r}")
        existing = items.get(iid) if isinstance(items.get(iid), dict) else {}
        entry = {
            "status": status,
            "loop_retry": existing.get("loop_retry") or default_retry(),
            "artifact_dir": existing.get("artifact_dir") or f"items/{iid}",
        }
        if "loop_phase" in existing:
            entry["loop_phase"] = existing["loop_phase"]
        if "blocked_reason" in existing:
            entry["blocked_reason"] = existing["blocked_reason"]
        if "last_loop_action" in existing:
            entry["last_loop_action"] = existing["last_loop_action"]
        if items.get(iid) != entry:
            changed_keys.append(f"items.{iid}")
        items[iid] = entry
    data["items"] = items
    write_run_state(change_dir, data, changed_keys or ["items"])


def cmd_set_item(
    project: Path,
    change_id: str | None,
    item_id: str,
    status: str | None,
    loop_phase: str | None,
    sync_work_plan: bool,
) -> None:
    if not ITEM_ID_RE.match(item_id):
        raise SystemExit(f"invalid item id: {item_id!r}")
    if status is None and loop_phase is None:
        raise SystemExit("set-item requires --status and/or --loop-phase")
    if status is not None and status not in ITEM_STATUSES:
        raise SystemExit(f"invalid status {status!r}; want one of {ITEM_STATUSES}")
    if loop_phase is not None and loop_phase not in LOOP_PHASES:
        raise SystemExit(f"invalid loop_phase {loop_phase!r}; want one of {LOOP_PHASES}")

    _, change_dir = resolve_change_dir(project, change_id)
    data = require_run_state(change_dir)
    items = dict(data.get("items") or {})
    if item_id not in items:
        raise SystemExit(f"unknown item id {item_id!r}; run sync-items first")
    entry = dict(items[item_id])
    changed: list[str] = []
    if status is not None:
        entry["status"] = status
        changed.append(f"items.{item_id}.status")
    if loop_phase is not None:
        entry["loop_phase"] = loop_phase
        changed.append(f"items.{item_id}.loop_phase")
    if "loop_retry" not in entry:
        entry["loop_retry"] = default_retry()
    if "artifact_dir" not in entry:
        entry["artifact_dir"] = f"items/{item_id}"
    items[item_id] = entry
    data["items"] = items

    wp_changed = False
    if sync_work_plan:
        if status is None:
            raise SystemExit("--sync-work-plan requires --status")
        if status not in WORK_PLAN_ITEM_STATUSES:
            raise SystemExit(f"status {status!r} not syncable to work-plan")
        wp_path = change_dir / "work-plan.json"
        if not wp_path.is_file():
            raise SystemExit(f"work-plan.json missing: {wp_path}")
        wp = load_json(wp_path)
        found = False
        for it in wp.get("items") or []:
            if isinstance(it, dict) and it.get("id") == item_id:
                it["status"] = status
                found = True
                break
        if not found:
            raise SystemExit(f"item {item_id!r} not found in work-plan.json")
        dump_json(wp_path, wp)
        wp_changed = True
        changed.append("work-plan.json")

    data["updated_at"] = utc_now()
    validate_run_state(data)
    path = run_state_path(change_dir)
    dump_json(path, data)
    extra: dict[str, Any] = {}
    if wp_changed:
        extra["work_plan"] = str(change_dir / "work-plan.json")
    emit(True, path, changed, **extra)


def cmd_set_host_toolchain(project: Path, change_id: str | None) -> None:
    layout = load_layout(project)
    _, change_dir = resolve_change_dir(project, change_id)
    ht_path = layout.host_toolchain_path()
    if not ht_path.is_file():
        raise SystemExit(f"host-toolchain.json missing: {ht_path}")
    ht = load_json(ht_path)
    if not isinstance(ht, dict):
        raise SystemExit("host-toolchain.json must be an object")
    snap: dict[str, Any] = {
        "ready": bool(ht.get("ready")),
        "source": host_toolchain_source(layout),
        "missing": list(ht.get("missing") or []),
    }
    if isinstance(ht.get("resolved_at"), str):
        snap["resolved_at"] = ht["resolved_at"]
    else:
        snap["resolved_at"] = utc_now()
    data = require_run_state(change_dir)
    data["host_toolchain"] = snap
    write_run_state(change_dir, data, ["host_toolchain"])


def cmd_record_metrics(
    project: Path,
    change_id: str | None,
    inc_task_launches: int = 0,
    inc_critiques: int = 0,
    set_slices: int | None = None,
    set_scenarios: int | None = None,
) -> None:
    _, change_dir = resolve_change_dir(project, change_id)
    data = require_run_state(change_dir)
    metrics = dict(data.get("metrics") or {})
    if "started_at" not in metrics:
        metrics["started_at"] = utc_now()
    if inc_task_launches > 0:
        metrics["task_launch_count"] = metrics.get("task_launch_count", 0) + inc_task_launches
    if inc_critiques > 0:
        metrics["critique_count"] = metrics.get("critique_count", 0) + inc_critiques
    if set_slices is not None:
        metrics["slice_count"] = set_slices
    if set_scenarios is not None:
        metrics["scenario_count"] = set_scenarios
    data["metrics"] = metrics
    write_run_state(change_dir, data, ["metrics"])


def cmd_mark_change_done(project: Path, change_id: str | None) -> None:
    cid, change_dir = resolve_change_dir(project, change_id)
    data = require_run_state(change_dir)
    data["phase"] = "done"
    if "metrics" in data and isinstance(data["metrics"], dict):
        data["metrics"]["completed_at"] = utc_now()
    data["updated_at"] = utc_now()
    validate_run_state(data)
    rs_path = run_state_path(change_dir)
    dump_json(rs_path, data)

    status_path = change_dir / "status.json"
    status_body = {"version": "1", "status": "done"}
    if status_path.is_file():
        existing = load_json(status_path)
        if isinstance(existing, dict):
            status_body = {**existing, "status": "done"}
            if "version" not in status_body:
                status_body["version"] = "1"
    dump_json(status_path, status_body)
    emit(
        True,
        rs_path,
        ["phase", "status.json"],
        change_id=cid,
        status_path=str(status_path),
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="solidsdd-run-state",
        description="Constrained mutations for solidsdd run-state.json",
    )
    p.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="consuming project root (default: .)",
    )
    p.add_argument(
        "--change-id",
        default=None,
        help="change id (default: .solidsdd/active-change.json)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="create run-state.json defaults")
    init_p.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing run-state.json",
    )

    sp = sub.add_parser("set-phase", help="set run-state phase")
    sp.add_argument("--phase", required=True, choices=PHASES)

    sw = sub.add_parser("set-wave", help="set wave_index")
    sw.add_argument("--index", type=int, required=True)

    note_p = sub.add_parser("note", help="append isolation_notes")
    note_p.add_argument("--append", required=True, help="single-line note text")

    sub.add_parser("sync-items", help="sync items map from work-plan.json")

    si = sub.add_parser("set-item", help="update one item")
    si.add_argument("--id", required=True, dest="item_id")
    si.add_argument("--status", choices=ITEM_STATUSES, default=None)
    si.add_argument("--loop-phase", choices=LOOP_PHASES, default=None)
    si.add_argument(
        "--sync-work-plan",
        action="store_true",
        help="also set matching work-plan.json item status",
    )

    sub.add_parser(
        "set-host-toolchain",
        help="copy readiness from .solidsdd/host-toolchain.json",
    )
    rm_p = sub.add_parser("record-metrics", help="record or increment run metrics")
    rm_p.add_argument("--inc-task-launches", type=int, default=0, help="increment task launch count")
    rm_p.add_argument("--inc-critiques", type=int, default=0, help="increment critique count")
    rm_p.add_argument("--set-slices", type=int, default=None, help="set slice count")
    rm_p.add_argument("--set-scenarios", type=int, default=None, help="set scenario count")

    sub.add_parser(
        "mark-change-done",
        help="set status.json and phase to done",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project = args.project_root.resolve()
    if args.command == "init":
        cmd_init(project, args.change_id, args.force)
    elif args.command == "set-phase":
        cmd_set_phase(project, args.change_id, args.phase)
    elif args.command == "set-wave":
        cmd_set_wave(project, args.change_id, args.index)
    elif args.command == "note":
        cmd_note(project, args.change_id, args.append)
    elif args.command == "sync-items":
        cmd_sync_items(project, args.change_id)
    elif args.command == "set-item":
        cmd_set_item(
            project,
            args.change_id,
            args.item_id,
            args.status,
            args.loop_phase,
            args.sync_work_plan,
        )
    elif args.command == "set-host-toolchain":
        cmd_set_host_toolchain(project, args.change_id)
    elif args.command == "record-metrics":
        cmd_record_metrics(
            project,
            args.change_id,
            args.inc_task_launches,
            args.inc_critiques,
            args.set_slices,
            args.set_scenarios,
        )
    elif args.command == "mark-change-done":
        cmd_mark_change_done(project, args.change_id)
    else:  # pragma: no cover
        parser.error(f"unknown command {args.command}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            raise SystemExit(1) from None
        raise

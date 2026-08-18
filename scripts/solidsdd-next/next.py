#!/usr/bin/env python3
"""Deterministic next-action for solidsdd-run (read-only; no run-state writes).

Commands:
  next          — emit RunNext JSON for the active or --change-id change
  validate      — check --declared ACTION against the legal set for current state
  parse-profile — extract an explicit --profile / profile: token from raw text
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    print("solidsdd-next requires the jsonschema package", file=sys.stderr)
    sys.exit(2)

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from solidsdd_lib.paths import (  # noqa: E402
    Layout,
    load_layout,
    resolve_change_dir as _resolve_change_dir,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"

REQUESTED_PROFILES = ("auto", "direct", "thin", "standard", "full")

# `--profile thin`, `--profile=thin`, `profile: thin`, `profile:thin` (case-insensitive).
_PROFILE_TOKEN_RE = re.compile(
    r"--profile[=\s]+(auto|direct|thin|standard|full)\b"
    r"|\bprofile\s*:\s*(auto|direct|thin|standard|full)\b",
    re.IGNORECASE,
)
# Same shapes, but capturing whatever word follows even if it's not a valid
# profile — lets us warn on a near-miss (e.g. `--profile fast`) instead of
# silently treating it as "no explicit profile requested".
_PROFILE_ATTEMPT_RE = re.compile(
    r"--profile[=\s]+(\S+)|\bprofile\s*:\s*(\S+)", re.IGNORECASE
)


def parse_explicit_profile(text: str) -> dict[str, Any]:
    """Extract an explicit Execution Profile token from raw instruction text.

    Mechanical helper for the Triage step in skills/solidsdd-run/SKILL.md —
    prefer this over ad hoc prose parsing so `--profile thin` is recognized
    the same way regardless of who reads the instruction. Never writes
    anything and never itself applies the safety-override floor (that's
    Triage's job, using this only as the `requested_profile` input) — see
    reference-src/triage.md.
    """
    text = text or ""
    match = _PROFILE_TOKEN_RE.search(text)
    if match:
        value = (match.group(1) or match.group(2)).lower()
        return {
            "version": "1",
            "requested_profile": value,
            "explicit": True,
            "matched_text": match.group(0).strip(),
        }
    attempt = _PROFILE_ATTEMPT_RE.search(text)
    if attempt:
        raw = attempt.group(1) or attempt.group(2)
        return {
            "version": "1",
            "requested_profile": "auto",
            "explicit": False,
            "matched_text": None,
            "warning": (
                f"found a profile-like token {raw!r} that is not one of "
                f"{REQUESTED_PROFILES}; ignoring and defaulting to auto"
            ),
        }
    return {
        "version": "1",
        "requested_profile": "auto",
        "explicit": False,
        "matched_text": None,
    }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def resolve_change_dir(project: Path, change_id: str | None) -> tuple[str, Path]:
    return _resolve_change_dir(project, change_id)


def exists(change_dir: Path, rel: str) -> bool:
    return (change_dir / rel).is_file()


def load_optional(change_dir: Path, rel: str) -> Any | None:
    p = change_dir / rel
    if not p.is_file():
        return None
    return load_json(p)


def blocking_clarifications(change_dir: Path) -> list[str]:
    clar = load_optional(change_dir, "clarifications/open.json")
    if not clar:
        return []
    out = []
    for it in clar.get("items") or []:
        if isinstance(it, dict) and it.get("blocking") and it.get("status") == "open":
            out.append(str(it.get("id")))
    return out


def gate_required(obj: Any | None) -> bool:
    if not isinstance(obj, dict):
        return False
    hg = obj.get("human_gate") or {}
    return bool(hg.get("required"))


def approval_covers(change_dir: Path, scope: str) -> bool:
    for name in ("gate-approval.json",):
        ap = load_optional(change_dir, name)
        if (
            isinstance(ap, dict)
            and ap.get("scope") == scope
            and ap.get("decision") in ("approve", "approve_partial")
        ):
            return True
    hist = change_dir / "gate-approvals"
    if hist.is_dir():
        for path in hist.glob("*.json"):
            try:
                ap = load_json(path)
            except json.JSONDecodeError:
                continue
            if ap.get("scope") == scope and ap.get("decision") in (
                "approve",
                "approve_partial",
            ):
                return True
    return False


def critique_pass(change_dir: Path, name: str) -> bool:
    data = load_optional(change_dir, name)
    return isinstance(data, dict) and data.get("result") == "pass"


def ready_item_ids(rs: dict[str, Any], work: dict[str, Any] | None) -> list[str]:
    items = rs.get("items") or {}
    ready = [i for i, st in items.items() if isinstance(st, dict) and st.get("status") == "ready"]
    if ready:
        return sorted(ready)
    if work:
        out = []
        for it in work.get("items") or []:
            if not isinstance(it, dict):
                continue
            iid = it.get("id")
            if not iid:
                continue
            st = (items.get(iid) or {}).get("status") if items else None
            if st in (None, "ready", "pending"):
                deps = it.get("depends_on") or []
                if all(
                    (items.get(d) or {}).get("status") == "done"
                    or (not items and False)
                    for d in deps
                ) or not deps:
                    if st != "done" and st != "blocked" and st != "running":
                        out.append(iid)
        # Prefer run-state; if empty items map, use work plan ready heuristic
        if not items:
            for it in work.get("items") or []:
                if isinstance(it, dict) and it.get("id") and not (it.get("depends_on") or []):
                    out.append(it["id"])
        return sorted(set(out))
    return []


def all_items_done(rs: dict[str, Any], work: dict[str, Any] | None) -> bool:
    items = rs.get("items") or {}
    if items:
        return items and all(
            isinstance(st, dict) and st.get("status") == "done" for st in items.values()
        )
    if work and work.get("items"):
        return False
    return False


def b4_skip(change_dir: Path, rs: dict[str, Any], work: dict[str, Any] | None) -> tuple[str, str] | None:
    """Return (sole_item_id, report_path) when B4 (run-cost.md) is mechanically detectable.

    B4: WorkPlan has exactly one item, and that item's own verification-report.json
    already has result=pass with "acceptance_of_whole" tagged in some check's covers.
    """
    work_items = (work or {}).get("items") or []
    if len(work_items) != 1:
        return None
    item = work_items[0]
    item_id = item.get("id") if isinstance(item, dict) else None
    if not item_id:
        return None
    state = (rs.get("items") or {}).get(item_id) or {}
    artifact_dir = state.get("artifact_dir") or f"items/{item_id}"
    report_rel = f"{artifact_dir}/verification-report.json"
    report = load_optional(change_dir, report_rel)
    if not isinstance(report, dict) or report.get("result") != "pass":
        return None
    checks = report.get("checks") or []
    covers_whole = any(
        isinstance(c, dict) and "acceptance_of_whole" in (c.get("covers") or [])
        for c in checks
    )
    if not covers_whole:
        return None
    return item_id, report_rel


def hint(
    *,
    change_id: str,
    phase: str | None,
    action: str,
    reason: str,
    skill: str | None = None,
    subject: str | None = None,
    item_ids: list[str] | None = None,
    inputs: list[str] | None = None,
    legal: list[str] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "version": "1",
        "change_id": change_id,
        "action": action,
        "reason": reason,
        "inputs": inputs or [],
        "legal_actions": legal or [action],
    }
    if phase:
        out["phase"] = phase
    if skill:
        out["skill"] = skill
    if subject:
        out["subject"] = subject
    if item_ids:
        out["item_ids"] = item_ids
    return out


def effective_profile(rs: dict[str, Any], triage: dict[str, Any] | None) -> str | None:
    """Read Triage's effective_profile, preferring the persisted run-state copy."""
    prof = rs.get("execution_profile")
    if isinstance(prof, dict) and prof.get("effective"):
        return prof["effective"]
    if isinstance(triage, dict):
        return triage.get("effective_profile")
    return None


def compute_next(
    change_id: str, change_dir: Path, layout: Layout | None = None
) -> dict[str, Any]:
    rs = load_optional(change_dir, "run-state.json") or {}
    phase = rs.get("phase")
    work = load_optional(change_dir, "work-plan.json")
    status = load_optional(change_dir, "status.json") or {}
    triage = load_optional(change_dir, "triage-result.json")

    if status.get("status") == "done" or phase == "done":
        return hint(
            change_id=change_id,
            phase=phase or "done",
            action="done",
            reason="change status or phase is done",
        )

    if triage is not None and not phase:
        profile = effective_profile(rs, triage)
        if profile == "direct":
            return hint(
                change_id=change_id,
                phase=None,
                action="direct_implementation",
                reason=(
                    "Triage selected direct (L0): implement inline and run project "
                    "verification; no orchestration phases apply — see triage-result.json"
                ),
                inputs=["triage-result.json"],
                legal=["direct_implementation", "done"],
            )
        if profile == "thin":
            return hint(
                change_id=change_id,
                phase="triage",
                action="thin_implementation",
                skill="solidsdd-implement",
                reason=(
                    "Triage selected thin (L1): implement then verify; "
                    "brief/decompose/architecture do not apply"
                ),
                inputs=["triage-result.json"],
                legal=["thin_implementation"],
            )
        # standard/full: fall through to the phase-based logic below, unchanged.

    if phase == "triage":
        profile = effective_profile(rs, triage)
        if profile == "thin":
            return hint(
                change_id=change_id,
                phase=phase,
                action="thin_implementation",
                skill="solidsdd-implement",
                reason="thin (L1): run implementation",
                legal=["thin_implementation"],
            )
        if profile == "direct":
            return hint(
                change_id=change_id,
                phase=phase,
                action="direct_implementation",
                reason="direct (L0) should not have a run-state.json; implement inline",
                legal=["direct_implementation"],
            )
        return hint(
            change_id=change_id,
            phase=phase,
            action="knowledge_consult",
            skill="solidsdd-knowledge",
            reason="triage complete; profile standard/full — advance outer framing",
            legal=["knowledge_consult", "grill", "intake"],
        )

    if phase == "thin_implementation":
        if not exists(change_dir, "verification-report.json"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="thin_verification",
                skill="solidsdd-verify",
                reason="thin (L1): run verification after implementation",
                legal=["thin_verification"],
            )
        phase = "thin_verification"

    if phase == "thin_verification":
        report = load_optional(change_dir, "verification-report.json")
        if report is None:
            return hint(
                change_id=change_id,
                phase=phase,
                action="thin_verification",
                skill="solidsdd-verify",
                reason="thin (L1): verification-report.json missing",
                legal=["thin_verification"],
            )
        if report.get("result") == "pass":
            return hint(
                change_id=change_id,
                phase=phase,
                action="done",
                reason="thin (L1) verification passed",
                legal=["done"],
            )
        return hint(
            change_id=change_id,
            phase=phase,
            action="critique_verification_report",
            skill="solidsdd-critique",
            subject="verification_report",
            reason="thin (L1) verification failed; critique then re-triage/escalate",
            legal=["critique_verification_report", "re_triage"],
        )

    opens = blocking_clarifications(change_dir)
    if opens:
        return hint(
            change_id=change_id,
            phase=phase or "grill",
            action="human_gate",
            reason=f"blocking clarifications still open: {', '.join(opens)}",
            inputs=["clarifications/open.json"],
            legal=["human_gate", "grill", "resolve_clarifications"],
        )

    # No run-state yet → start path
    if not phase:
        if not exists(change_dir, "change-context.md"):
            knowledge_present = False
            if layout is not None:
                knowledge_present = any(d.is_dir() for d in layout.knowledge_dirs())
            if exists(change_dir, "knowledge-consult.md") or knowledge_present:
                # Prefer grill only when clarifications already started; else intake or consult
                if exists(change_dir, "clarifications/open.json"):
                    return hint(
                        change_id=change_id,
                        phase=None,
                        action="grill",
                        skill="solidsdd-grill",
                        reason="clarifications present; continue grill or finish before intake",
                        inputs=["clarifications/open.json"],
                        legal=["grill", "intake", "knowledge_consult"],
                    )
                return hint(
                    change_id=change_id,
                    phase=None,
                    action="intake",
                    skill="solidsdd-intake",
                    reason="no Change Context yet",
                    legal=["intake", "grill", "knowledge_consult", "context"],
                )
            return hint(
                change_id=change_id,
                phase=None,
                action="context",
                skill="solidsdd-context",
                reason="no run-state; start with solidsdd-context, then triage",
                legal=["context", "triage", "knowledge_consult", "grill", "intake"],
            )
        # Context exists without phase → critique or brief path
        phase = "intake"

    if phase in ("context", "knowledge_consult"):
        return hint(
            change_id=change_id,
            phase=phase,
            action="intake" if phase == "knowledge_consult" else "knowledge_consult",
            skill="solidsdd-intake" if phase == "knowledge_consult" else "solidsdd-knowledge",
            reason=f"phase={phase}; advance outer framing",
            legal=["knowledge_consult", "grill", "intake"],
        )

    if phase == "grill":
        return hint(
            change_id=change_id,
            phase=phase,
            action="intake",
            skill="solidsdd-intake",
            reason="grill complete or skip; run intake",
            inputs=["clarifications/open.json"]
            if exists(change_dir, "clarifications/open.json")
            else [],
            legal=["intake", "grill"],
        )

    if phase == "intake":
        if not exists(change_dir, "change-context.md"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="intake",
                skill="solidsdd-intake",
                reason="phase=intake but change-context.md missing",
                legal=["intake"],
            )
        if not critique_pass(change_dir, "critique-change-context.json"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="critique_change_context",
                skill="solidsdd-critique",
                subject="change_context",
                reason="need critique(change_context)",
                inputs=["change-context.md", "change-context-gate.json"],
                legal=["critique_change_context", "intake"],
            )
        gate = load_optional(change_dir, "change-context-gate.json")
        if gate_required(gate) and not approval_covers(change_dir, "change_context"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="human_gate",
                reason="change-context-gate requires human approval",
                inputs=["change-context-gate.json"],
                legal=["human_gate"],
            )
        return hint(
            change_id=change_id,
            phase="critique_change_context",
            action="brief",
            skill="solidsdd-brief",
            reason="context critiqued; proceed to brief",
            inputs=["change-context.md"],
            legal=["brief"],
        )

    if phase == "critique_change_context":
        gate = load_optional(change_dir, "change-context-gate.json")
        if gate_required(gate) and not approval_covers(change_dir, "change_context"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="human_gate",
                reason="awaiting change_context gate approval",
                legal=["human_gate"],
            )
        return hint(
            change_id=change_id,
            phase=phase,
            action="brief",
            skill="solidsdd-brief",
            reason="ready for brief",
            legal=["brief"],
        )

    if phase == "brief":
        if not exists(change_dir, "change-brief.json"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="brief",
                skill="solidsdd-brief",
                reason="phase=brief but change-brief.json missing",
                legal=["brief"],
            )
        if not critique_pass(change_dir, "critique-change-brief.json"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="critique_change_brief",
                skill="solidsdd-critique",
                subject="change_brief",
                reason="need critique(change_brief)",
                inputs=["change-brief.json"],
                legal=["critique_change_brief", "brief"],
            )
        brief = load_optional(change_dir, "change-brief.json")
        if gate_required(brief) and not approval_covers(change_dir, "change_brief"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="human_gate",
                reason="ChangeBrief human_gate required",
                legal=["human_gate"],
            )
        return hint(
            change_id=change_id,
            phase="critique_change_brief",
            action="decompose",
            skill="solidsdd-decompose",
            reason="brief critiqued; proceed to decompose",
            legal=["decompose"],
        )

    if phase == "critique_change_brief":
        return hint(
            change_id=change_id,
            phase=phase,
            action="decompose",
            skill="solidsdd-decompose",
            reason="ready for decompose",
            legal=["decompose"],
        )

    if phase == "decompose":
        if not exists(change_dir, "work-plan.json"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="decompose",
                skill="solidsdd-decompose",
                reason="phase=decompose but work-plan.json missing",
                legal=["decompose"],
            )
        if not critique_pass(change_dir, "critique-work-plan.json"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="critique_work_plan",
                skill="solidsdd-critique",
                subject="work_plan",
                reason="need critique(work_plan)",
                inputs=["work-plan.json"],
                legal=["critique_work_plan", "decompose"],
            )
        if gate_required(work) and not approval_covers(change_dir, "work_plan"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="human_gate",
                reason="WorkPlan human_gate required",
                legal=["human_gate"],
            )
        return hint(
            change_id=change_id,
            phase="critique_work_plan",
            action="architecture",
            skill="solidsdd-architecture",
            reason="work plan ready; run architecture judgment",
            legal=["architecture"],
        )

    if phase in ("critique_work_plan", "architecture"):
        arch = load_optional(change_dir, "architecture-plan.json")
        if not isinstance(arch, dict):
            return hint(
                change_id=change_id,
                phase=phase,
                action="architecture",
                skill="solidsdd-architecture",
                reason="architecture-plan.json missing; run architecture judgment",
                legal=["architecture"],
            )
        if arch.get("status") == "changed":
            if not critique_pass(change_dir, "critique-architecture-plan.json"):
                return hint(
                    change_id=change_id,
                    phase=phase,
                    action="critique_architecture",
                    skill="solidsdd-critique",
                    subject="architecture_plan",
                    reason="ArchitecturePlan status=changed; need critique(architecture_plan)",
                    inputs=["architecture-plan.json"],
                    legal=["critique_architecture", "architecture"],
                )
            if gate_required(arch) and not approval_covers(change_dir, "architecture_plan"):
                return hint(
                    change_id=change_id,
                    phase=phase,
                    action="human_gate",
                    reason="ArchitecturePlan human_gate required",
                    inputs=["architecture-plan.json"],
                    legal=["human_gate"],
                )
        return hint(
            change_id=change_id,
            phase="critique_architecture",
            action="waves",
            skill="solidsdd-loop",
            reason="architecture judgment resolved; start waves",
            item_ids=ready_item_ids(rs, work),
            legal=["waves", "loop_wave", "critique_cross_change_consistency", "critique_knowledge_consistency"],
        )

    if phase == "critique_architecture":
        ready = ready_item_ids(rs, work)
        if ready or not all_items_done(rs, work):
            return hint(
                change_id=change_id,
                phase="waves",
                action="waves",
                skill="solidsdd-loop",
                reason="enter slice waves",
                item_ids=ready,
                legal=["waves", "loop_wave"],
            )
        skip = b4_skip(change_dir, rs, work)
        if skip:
            item_id, report_rel = skip
            return hint(
                change_id=change_id,
                phase=phase,
                action="knowledge_harvest",
                skill="solidsdd-knowledge",
                reason=(
                    f"cost_skip:B4 — sole item {item_id!r}'s {report_rel} already covers "
                    "acceptance_of_whole with pass; skipping duplicate integration verify"
                ),
                inputs=[report_rel],
                legal=["knowledge_harvest", "integration_verify"],
            )
        return hint(
            change_id=change_id,
            phase=phase,
            action="integration_verify",
            skill="solidsdd-verify",
            reason="no pending items; integration verify",
            legal=["integration_verify"],
        )

    if phase == "waves":
        if all_items_done(rs, work):
            skip = b4_skip(change_dir, rs, work)
            if skip:
                item_id, report_rel = skip
                return hint(
                    change_id=change_id,
                    phase=phase,
                    action="knowledge_harvest",
                    skill="solidsdd-knowledge",
                    reason=(
                        f"cost_skip:B4 — sole item {item_id!r}'s {report_rel} already covers "
                        "acceptance_of_whole with pass; skipping duplicate integration verify"
                    ),
                    inputs=[report_rel],
                    legal=["knowledge_harvest", "integration_verify"],
                )
            return hint(
                change_id=change_id,
                phase=phase,
                action="integration_verify",
                skill="solidsdd-verify",
                reason="all items done; integration verify",
                legal=["integration_verify"],
            )
        ready = ready_item_ids(rs, work)
        return hint(
            change_id=change_id,
            phase=phase,
            action="loop_wave",
            skill="solidsdd-loop",
            reason="run solidsdd-loop for ready items",
            item_ids=ready,
            legal=["loop_wave", "waves"],
        )

    if phase == "integration_verify":
        if not exists(change_dir, "integration-verification-report.json"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="integration_verify",
                skill="solidsdd-verify",
                reason="need integration verification report",
                legal=["integration_verify"],
            )
        if not critique_pass(change_dir, "critique-integration-verification.json") and not critique_pass(
            change_dir, "critique-verification-report.json"
        ):
            return hint(
                change_id=change_id,
                phase=phase,
                action="critique_integration",
                skill="solidsdd-critique",
                subject="verification_report",
                reason="need critique(verification_report) for integration",
                legal=["critique_integration"],
            )
        return hint(
            change_id=change_id,
            phase="critique_integration",
            action="knowledge_harvest",
            skill="solidsdd-knowledge",
            reason="integration green; harvest knowledge",
            legal=["knowledge_harvest"],
        )

    if phase == "critique_integration":
        return hint(
            change_id=change_id,
            phase=phase,
            action="knowledge_harvest",
            skill="solidsdd-knowledge",
            reason="ready for knowledge harvest",
            legal=["knowledge_harvest"],
        )

    if phase == "knowledge_harvest":
        harvest = load_optional(change_dir, "knowledge-harvest.json")
        if harvest is None:
            return hint(
                change_id=change_id,
                phase=phase,
                action="knowledge_harvest",
                skill="solidsdd-knowledge",
                reason="emit knowledge-harvest.json",
                legal=["knowledge_harvest"],
            )
        if gate_required(harvest) and not approval_covers(change_dir, "knowledge_harvest"):
            if not critique_pass(change_dir, "critique-knowledge-harvest.json") and (
                harvest.get("candidates") or []
            ):
                return hint(
                    change_id=change_id,
                    phase=phase,
                    action="critique_knowledge_harvest",
                    skill="solidsdd-critique",
                    subject="knowledge_harvest",
                    reason="critique harvest before gate",
                    legal=["critique_knowledge_harvest", "human_gate"],
                )
            return hint(
                change_id=change_id,
                phase=phase,
                action="human_gate",
                reason="knowledge harvest gate required",
                legal=["human_gate", "knowledge_apply"],
            )
        return hint(
            change_id=change_id,
            phase=phase,
            action="done",
            reason="harvest complete or empty; mark change done",
            legal=["done", "knowledge_apply"],
        )

    if phase == "critique_knowledge_harvest":
        harvest = load_optional(change_dir, "knowledge-harvest.json")
        if gate_required(harvest) and not approval_covers(change_dir, "knowledge_harvest"):
            return hint(
                change_id=change_id,
                phase=phase,
                action="human_gate",
                reason="awaiting knowledge_harvest approval",
                legal=["human_gate", "knowledge_apply"],
            )
        return hint(
            change_id=change_id,
            phase=phase,
            action="done",
            reason="knowledge gate cleared; mark done",
            legal=["done", "knowledge_apply"],
        )

    if phase == "stopped":
        return hint(
            change_id=change_id,
            phase=phase,
            action="human_gate",
            reason=rs.get("stopped_reason") or "run-state phase is stopped",
            legal=["human_gate", "resume"],
        )

    return hint(
        change_id=change_id,
        phase=phase,
        action="unknown",
        reason=f"unhandled phase {phase!r}; read solidsdd-run Sequence",
        legal=[],
    )


def validate_hint(hint_obj: dict[str, Any]) -> None:
    schema = load_json(SCHEMAS / "run-next.schema.json")
    Draft202012Validator(schema).validate(hint_obj)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="solid_sdd deterministic next / validate")
    parser.add_argument(
        "command",
        choices=["next", "validate", "parse-profile"],
        help="next = emit action; validate = check --declared; parse-profile = extract --profile token from --text",
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--change-id", default=None)
    parser.add_argument(
        "--declared",
        default=None,
        help="Action the parent intends to run (validate command)",
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Raw instruction text to scan for an explicit profile token (parse-profile command)",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "parse-profile":
        if args.text is None:
            print("parse-profile requires --text", file=sys.stderr)
            return 2
        result = parse_explicit_profile(args.text)
        print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
        return 0

    project = args.project_root.resolve()
    layout = load_layout(project)
    change_id, change_dir = _resolve_change_dir(project, args.change_id, layout=layout)
    nxt = compute_next(change_id, change_dir, layout=layout)
    try:
        validate_hint(nxt)
    except jsonschema.ValidationError as e:
        print(json.dumps({"error": "run-next schema", "detail": e.message}), file=sys.stderr)
        return 2

    if args.command == "next":
        print(json.dumps(nxt, indent=2 if args.pretty else None))
        return 0

    declared = args.declared
    if not declared:
        print("validate requires --declared ACTION", file=sys.stderr)
        return 2
    legal = set(nxt.get("legal_actions") or [nxt["action"]])
    ok = declared == nxt["action"] or declared in legal
    result = {
        "version": "1",
        "change_id": change_id,
        "declared": declared,
        "expected_action": nxt["action"],
        "legal_actions": sorted(legal),
        "ok": ok,
        "reason": nxt["reason"] if ok else f"declared {declared!r} not in legal {sorted(legal)}",
        "next": nxt,
    }
    print(json.dumps(result, indent=2 if args.pretty else None))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic host toolchain probe for solid_sdd (no LLM search)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from solidsdd_lib.paths import load_layout  # noqa: E402


TOOL_IDS = ("node", "npm", "npx", "bundle", "ruby", "go", "redocly", "mise")


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = (p.stdout or "").strip() or (p.stderr or "").strip()
        return p.returncode, out
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def find_mise() -> str | None:
    path = shutil.which("mise")
    if path:
        # Prefer real binary over shim if both exist
        real = Path(path).resolve()
        if real.name == "mise" or "shims" not in str(real):
            return path
    home = Path.home()
    for candidate in (
        home / ".local" / "bin" / "mise",
        home / ".local" / "share" / "mise" / "bin" / "mise",
        home / ".cargo" / "bin" / "mise",
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    # Some installs only expose shims; still try `mise` via shims dir
    shim_mise = home / ".local" / "share" / "mise" / "shims" / "mise"
    if shim_mise.is_file() and os.access(shim_mise, os.X_OK):
        return str(shim_mise)
    if path:
        return path
    return None


def resolve_tool(name: str, mise_bin: str | None = None) -> dict:
    path = shutil.which(name)
    if path:
        return {"found": True, "path": path, "via": "path"}

    mise = mise_bin or find_mise()
    if mise:
        code, out = _run([mise, "which", name])
        if code == 0 and out and Path(out.splitlines()[0]).exists():
            return {
                "found": True,
                "path": out.splitlines()[0],
                "via": "mise_which",
            }
        code, out = _run([mise, "exec", "--", "which", name])
        if code == 0 and out:
            candidate = out.splitlines()[0].strip()
            if candidate and Path(candidate).exists():
                return {
                    "found": True,
                    "path": candidate,
                    "via": "mise_exec_which",
                }

    return {"found": False, "path": None, "via": "missing"}


def detect_stack(root: Path) -> dict:
    return {
        "node": (root / "package.json").is_file(),
        "ruby": (root / "Gemfile").is_file(),
        "go": (root / "go.mod").is_file()
        or (root / "tools" / "solidsdd-kg" / "go.mod").is_file(),
        "verify_sh": (root / "verify.sh").is_file(),
        "package_json": (root / "package.json").is_file(),
    }


def preferred_commands(
    root: Path,
    stack: dict,
    tools: dict,
    mise_bin: str | None,
    openapi_rel: str = "openapi/openapi.yaml",
) -> dict[str, str]:
    cmds: dict[str, str] = {}
    mise_found = bool(mise_bin) or tools.get("mise", {}).get("found")
    mise_cmd = mise_bin or "mise"
    npm_via = tools.get("npm", {}).get("via")
    node_path = tools.get("node", {}).get("path")
    npm_path = tools.get("npm", {}).get("path")
    npx_via = tools.get("npx", {}).get("via")
    openapi_arg = openapi_rel.replace("\\", "/")

    if stack["verify_sh"]:
        cmds["verify"] = "./verify.sh"

    if stack["node"] or stack["package_json"]:
        # Prefer mise exec when mise binary exists (best for Task shells).
        # Else prefer absolute paths when tools live under mise installs/shims
        # so non-interactive shells without shims still work.
        if mise_found:
            cmds["npm_test"] = f"{mise_cmd} exec -- npm test"
            cmds["npm_install"] = f"{mise_cmd} exec -- npm install"
        elif npm_path:
            cmds["npm_test"] = f'"{npm_path}" test'
            cmds["npm_install"] = f'"{npm_path}" install'
        elif npm_via == "path":
            cmds["npm_test"] = "npm test"
            cmds["npm_install"] = "npm install"

        vitest = root / "node_modules" / "vitest" / "vitest.mjs"
        if vitest.is_file() and mise_found:
            cmds["vitest_run"] = f'{mise_cmd} exec -- node "{vitest}" run'
        elif vitest.is_file() and node_path:
            cmds["vitest_run"] = f'"{node_path}" "{vitest}" run'

        if tools.get("redocly", {}).get("found") and tools["redocly"].get("via") == "path" and not mise_found:
            redocly_path = tools["redocly"].get("path")
            if redocly_path:
                cmds["openapi_lint"] = (
                    f'"{redocly_path}" lint {openapi_arg} --extends=spec'
                )
            else:
                cmds["openapi_lint"] = (
                    f"redocly lint {openapi_arg} --extends=spec"
                )
        elif stack.get("package_json") or stack.get("node"):
            if mise_found:
                prefix = f"{mise_cmd} exec -- npx --yes"
            elif tools.get("npx", {}).get("path"):
                prefix = f'"{tools["npx"]["path"]}" --yes'
            elif npx_via == "path":
                prefix = "npx --yes"
            else:
                prefix = None
            if prefix:
                cmds["openapi_lint"] = (
                    f"{prefix} @redocly/cli@latest lint "
                    f"{openapi_arg} --extends=spec"
                )

    if stack["ruby"]:
        if tools.get("bundle", {}).get("found"):
            if tools["bundle"].get("via") == "path":
                cmds["rspec"] = "bundle exec rspec"
            elif mise_found:
                cmds["rspec"] = f"{mise_cmd} exec -- bundle exec rspec"
            elif tools["bundle"].get("path"):
                cmds["rspec"] = f'"{tools["bundle"]["path"]}" exec rspec'

    if stack["go"] and tools.get("go", {}).get("found"):
        if tools["go"].get("via") == "path":
            cmds["go_test"] = "go test ./..."
        else:
            cmds["go_test"] = f'"{tools["go"]["path"]}" test ./...'

    if (root / "tools" / "tla" / "tlc.sh").is_file():
        cmds["tlc"] = "./tools/tla/tlc.sh"

    return cmds


def npm_usable(tools: dict, mise_bin: str | None) -> bool:
    if tools.get("npm", {}).get("found"):
        return True
    if mise_bin:
        code, _ = _run([mise_bin, "exec", "--", "npm", "--version"])
        return code == 0
    return False


def required_missing(stack: dict, tools: dict, mise_bin: str | None) -> list[str]:
    missing: list[str] = []
    if stack["node"] or stack["package_json"]:
        if not tools.get("node", {}).get("found"):
            if not (
                mise_bin
                and _run([mise_bin, "exec", "--", "node", "--version"])[0] == 0
            ):
                missing.append("node")
        if not npm_usable(tools, mise_bin):
            missing.append("npm")
    if stack["ruby"]:
        if not tools.get("ruby", {}).get("found"):
            if not (
                mise_bin
                and _run([mise_bin, "exec", "--", "ruby", "--version"])[0] == 0
            ):
                missing.append("ruby")
        if not tools.get("bundle", {}).get("found"):
            if not (
                mise_bin
                and _run([mise_bin, "exec", "--", "bundle", "--version"])[0] == 0
            ):
                missing.append("bundle")
    return missing


def hints_for(missing: list[str], tools: dict, stack: dict) -> list[str]:
    hints: list[str] = []
    if not missing:
        hints.append(
            "Toolchain ready: copy commands from this file into Task prompts; "
            "do not find/search for npm/node in Subagents."
        )
        return hints

    hints.append(
        "ready=false: fix host PATH / mise before solidsdd-run. "
        "Do not spend Subagent turns on find/which rediscovery."
    )
    if "node" in missing or "npm" in missing:
        if tools.get("mise", {}).get("found"):
            hints.append(
                "mise is available: ensure node/npm are installed "
                "(`mise install` / `mise use node@…`) and prefer "
                "`mise exec -- npm test` in Task prompts."
            )
        else:
            hints.append(
                "Install Node/npm on PATH, or install mise and use "
                "`mise exec -- npm test`."
            )
    if "ruby" in missing or "bundle" in missing:
        hints.append(
            "Install Ruby + Bundler on PATH (or via mise) for RSpec projects."
        )
    if stack.get("verify_sh"):
        hints.append("Project has ./verify.sh — prefer that once its deps resolve.")
    return hints


def build_report(root: Path) -> dict:
    root = root.resolve()
    layout = load_layout(root)
    stack = detect_stack(root)
    mise_bin = find_mise()
    tools = {tid: resolve_tool(tid, mise_bin) for tid in TOOL_IDS}
    if mise_bin and not tools["mise"]["found"]:
        tools["mise"] = {"found": True, "path": mise_bin, "via": "path"}

    if not (
        stack["node"]
        or stack["package_json"]
        or stack["ruby"]
        or stack["go"]
        or stack["verify_sh"]
    ):
        missing: list[str] = []
        ready = True
    else:
        missing = required_missing(stack, tools, mise_bin)
        ready = len(missing) == 0

    commands = preferred_commands(
        root, stack, tools, mise_bin, openapi_rel=layout.openapi
    )

    return {
        "version": "1",
        "project_root": str(root),
        "resolved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ready": ready,
        "missing": missing,
        "stack": stack,
        "tools": tools,
        "commands": commands,
        "hints": hints_for(missing, tools, stack),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe host toolchain for solid_sdd (deterministic)."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Consuming project root (default: .)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when ready is false (after writing JSON).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print JSON to stdout (still writes the file).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"project root not found: {root}", file=sys.stderr)
        return 2

    layout = load_layout(root)
    report = build_report(root)
    out_path = layout.host_toolchain_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2 if args.pretty else None) + "\n"
    if not args.pretty:
        text = json.dumps(report, indent=2) + "\n"
    out_path.write_text(text, encoding="utf-8")

    if report["ready"]:
        print(f"host-toolchain ready → {out_path}", file=sys.stderr)
    else:
        print(
            f"host-toolchain NOT ready (missing={report['missing']}) → {out_path}",
            file=sys.stderr,
        )
        for h in report["hints"]:
            print(f"  hint: {h}", file=sys.stderr)

    if args.stdout:
        sys.stdout.write(text)

    if args.check and not report["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

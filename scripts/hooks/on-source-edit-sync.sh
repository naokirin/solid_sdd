#!/usr/bin/env bash
# Run after an AI file edit (Cursor afterFileEdit / Claude Code PostToolUse).
# If the edited path is a skill-reference source, sync skills/*/references/.
#
# stdin: hook JSON (Cursor: file_path; Claude: tool_input.file_path)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Prefer python3 for portable JSON parsing (no jq required).
edited_path="$(
  python3 - <<'PY'
import json, sys

raw = sys.stdin.read()
if not raw.strip():
    sys.exit(0)
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)

path = data.get("file_path") or ""
if not path:
    tool_input = data.get("tool_input") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {}
    if isinstance(tool_input, dict):
        path = (
            tool_input.get("file_path")
            or tool_input.get("path")
            or ""
        )
        # MultiEdit-style payloads may nest files
        if not path and isinstance(tool_input.get("edits"), list):
            for edit in tool_input["edits"]:
                if isinstance(edit, dict) and edit.get("file_path"):
                    path = edit["file_path"]
                    break

print(path)
PY
)"

if [[ -z "${edited_path}" ]]; then
  exit 0
fi

# Normalize to path relative to repo root when possible
rel="$edited_path"
if [[ "$edited_path" == "$ROOT"/* ]]; then
  rel="${edited_path#"$ROOT"/}"
fi

should_sync=0
case "$rel" in
  adapters/*|schemas/*|reference-src/*)
    should_sync=1
    ;;
  docs/execution-model.md|rules/solidsdd.mdc)
    should_sync=1
    ;;
esac

if [[ "$should_sync" -ne 1 ]]; then
  exit 0
fi

echo "[solid_sdd] source edit detected ($rel) → syncing skill references" >&2
exec "$ROOT/scripts/sync-skill-references.sh"

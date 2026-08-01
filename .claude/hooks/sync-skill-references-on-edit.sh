#!/usr/bin/env bash
# Claude Code PostToolUse (Edit|Write|MultiEdit) → sync skill references.
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
exec "$ROOT/scripts/hooks/on-source-edit-sync.sh"

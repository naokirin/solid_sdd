#!/usr/bin/env bash
# Deterministic solid_sdd lint (critique Step 0/1).
# Usage:
#   scripts/solidsdd-lint.sh [--project-root DIR] [--change-id ID] [--pretty]
# Exit: 0 pass, 1 fail (blocker/major), 2 tooling error
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/solidsdd-lint/lint.py" "$@"

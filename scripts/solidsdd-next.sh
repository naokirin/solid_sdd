#!/usr/bin/env bash
# Deterministic next-action hint for solidsdd-run (read-only).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/solidsdd-next/next.py" "$@"

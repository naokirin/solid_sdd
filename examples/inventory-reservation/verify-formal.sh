#!/usr/bin/env bash
# Run TLC on the concurrent last-unit reserve model.
# Usage: ./verify-formal.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
SPEC="$ROOT/formal/ConcurrentReserve.tla"
CFG="$ROOT/formal/ConcurrentReserve.cfg"

"$REPO/tools/tla/tlc.sh" "$SPEC" -config "$CFG"

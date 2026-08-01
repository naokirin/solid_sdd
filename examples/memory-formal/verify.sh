#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
SPEC="$ROOT/formal/ExclusiveMemory.tla"
CFG="$ROOT/formal/ExclusiveMemory.cfg"

"$REPO/tools/tla/tlc.sh" "$SPEC" -config "$CFG"

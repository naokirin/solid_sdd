#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
SPEC="$ROOT/formal/ClaimCoordinator.tla"
CFG="$ROOT/formal/ClaimCoordinator.cfg"

"$REPO/tools/tla/tlc.sh" "$SPEC" -config "$CFG"

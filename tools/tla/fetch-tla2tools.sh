#!/usr/bin/env bash
# Fetch official TLC (tla2tools.jar). Do not commit the jar.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="${TLA2TOOLS_VERSION:-v1.8.0}"
URL="https://github.com/tlaplus/tlaplus/releases/download/${VERSION}/tla2tools.jar"
OUT="${ROOT}/tla2tools.jar"

if [[ -f "$OUT" ]]; then
  echo "Already present: $OUT"
  exit 0
fi

echo "Downloading ${URL} ..."
curl -fsSL -o "$OUT" "$URL"
echo "Saved $OUT ($(wc -c <"$OUT") bytes)"

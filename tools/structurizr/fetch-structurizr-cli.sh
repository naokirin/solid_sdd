#!/usr/bin/env bash
# Fetch the official Structurizr CLI (optional toolchain; not required by
# solid_sdd — see reference-src/structurizr-dsl.md). Do not commit the download.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="${STRUCTURIZR_CLI_VERSION:-v2025.11.09}"
URL="https://github.com/structurizr/cli/releases/download/${VERSION}/structurizr-cli.zip"
OUT_DIR="${ROOT}/cli"
ZIP="${ROOT}/structurizr-cli.zip"

if [[ -x "${OUT_DIR}/structurizr.sh" ]]; then
  echo "Already present: ${OUT_DIR}/structurizr.sh"
  exit 0
fi

echo "Downloading ${URL} ..."
curl -fsSL -o "$ZIP" "$URL"
mkdir -p "$OUT_DIR"
unzip -oq "$ZIP" -d "$OUT_DIR"
rm -f "$ZIP"
chmod +x "${OUT_DIR}/structurizr.sh"
echo "Installed ${OUT_DIR}/structurizr.sh"

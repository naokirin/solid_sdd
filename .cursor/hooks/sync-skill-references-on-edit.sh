#!/usr/bin/env bash
# Cursor afterFileEdit → sync skill references when sources change.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "$ROOT/scripts/hooks/on-source-edit-sync.sh"

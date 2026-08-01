#!/usr/bin/env bash
# Point this repository at the versioned git hooks under scripts/git-hooks/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

git config core.hooksPath scripts/git-hooks
chmod +x scripts/git-hooks/pre-commit scripts/hooks/on-source-edit-sync.sh \
  .cursor/hooks/sync-skill-references-on-edit.sh \
  .claude/hooks/sync-skill-references-on-edit.sh \
  scripts/sync-skill-references.sh 2>/dev/null || true

echo "Configured core.hooksPath=scripts/git-hooks"
echo "pre-commit will run: scripts/sync-skill-references.sh --check"

# Agent / git automation for skill references

| Mechanism | Path | Behavior |
|-----------|------|----------|
| Cursor Hook | `.cursor/hooks.json` → `afterFileEdit` | Sync when source files are edited |
| Claude Code Hook | `.claude/settings.json` → `PostToolUse` (`Edit\|Write\|MultiEdit`) | Same |
| Shared logic | `scripts/hooks/on-source-edit-sync.sh` | Path filter + `sync-skill-references.sh` |
| git pre-commit | `scripts/git-hooks/pre-commit` | `--check`; on failure print commands and exit 1 |

Enable git hooks once per clone:

```bash
scripts/install-git-hooks.sh
```

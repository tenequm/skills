#!/usr/bin/env bash
# Pull latest openclaw and report what changed since last refresh
set -euo pipefail

REPO_DIR="${HOME}/Projects/openclaw"
SKILL_DIR="${HOME}/.claude/skills/openclaw-ref"
STAMP_FILE="${SKILL_DIR}/.last-refresh"

cd "$REPO_DIR"

# Abort rebase if one is stuck
git rebase --abort 2>/dev/null || true

# Stash local changes if any (don't lose work)
STASHED=false
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  echo "=== Stashing local changes ==="
  git stash push -m "refresh-openclaw auto-stash $(date -u +%Y%m%dT%H%M%S)" 2>&1
  STASHED=true
fi

# Record current HEAD
OLD_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# Pull latest (plain pull, no rebase to avoid conflicts)
echo "=== Pulling latest openclaw ==="
git pull --ff-only 2>&1 || {
  echo "WARN: fast-forward failed, trying merge pull"
  git pull --no-rebase 2>&1 || echo "WARN: git pull failed, continuing with current state"
}

NEW_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# Restore stash if we made one
if [ "$STASHED" = true ]; then
  echo "=== Restoring stashed changes ==="
  git stash pop 2>&1 || echo "WARN: stash pop failed, changes remain in stash"
fi

if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
  echo "=== No new commits ==="
else
  echo "=== New commits ($OLD_HEAD..$NEW_HEAD) ==="
  git log --oneline "$OLD_HEAD..$NEW_HEAD" 2>/dev/null | head -20

  echo ""
  echo "=== Changed files (relevant to skill) ==="
  git diff --name-only "$OLD_HEAD..$NEW_HEAD" 2>/dev/null | \
    grep -E '^(src/plugins/|src/plugin-sdk/|src/config/|src/gateway/|src/commands/|extensions/|docs/|src/cli/|src/channels/|src/telegram/|src/discord/|src/slack/)' | \
    head -40 || echo "(none matching plugin/config/boot/extension paths)"
fi

# Report last refresh time
if [ -f "$STAMP_FILE" ]; then
  echo ""
  echo "=== Last refresh: $(cat "$STAMP_FILE") ==="
fi

# Update stamp
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$STAMP_FILE"
echo "=== Refresh stamp updated ==="

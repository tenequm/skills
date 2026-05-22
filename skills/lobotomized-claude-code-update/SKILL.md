---
name: lobotomized-claude-code-update
description: Gated two-stage upgrade of a lobotomized Claude Code stack - the CC binary, skrabe/lobotomized-claude-code overrides, and the skrabe/tweakcc-fixed patcher. Stage 1 reports what would change; Stage 2 applies it after approval. Use to check for or apply updates to tweakcc, lobotomized-claude-code, or Claude Code system-prompt overrides.
metadata:
  version: "0.1.0"
---

# lobotomized-claude-code-update

Upgrades a lobotomized Claude Code install in two gated stages. Stage 1 reports
what would change and stops; Stage 2 performs the upgrade only after the user
explicitly approves. The split exists because the upgrade touches three
independently-versioned pieces plus an in-place binary patch - an unreviewed
surprise here leaves the user with a broken `claude`.

If the user has already seen a Stage 1 report in this conversation and approved
it, skip straight to Stage 2.

## The stack

Three pieces, version-pinned to each other:

| Piece | Location | Upstream |
|---|---|---|
| Claude Code binary | `~/.local/share/claude/versions/`, installed via `claude install <version>` | Anthropic |
| LCC overrides (~400 `.md` files) | `~/.tweakcc/lobotomized-claude-code/` | `skrabe/lobotomized-claude-code` |
| tweakcc-fixed (the patcher) | wherever `skrabe/tweakcc-fixed` was cloned (README default `~/dev/tweakcc-fixed`) | `skrabe/tweakcc-fixed` |

`~/.tweakcc/system-prompts` and `~/.tweakcc/system-reminders` are symlinks into
the LCC clone. The patcher splices LCC's overrides into the CC binary's `cli.js`
with `node <tweakcc-fixed>/dist/index.mjs --apply`.

Use **skrabe's** tweakcc-fixed only. The npm `tweakcc-fixed` package (a
different fork) and upstream `Piebald-AI/tweakcc` lack the `inlineBlobOverrides`
and `systemReminderOverrides` mechanisms that the LCC `inline-*.md` and
`system-reminders/*.md` overrides depend on - a different patcher silently
disables them.

LCC and tweakcc-fixed ship paired commits per CC release ("realign for CC
2.1.X" / "feat: support CC 2.1.X"). The latest CC version the stack supports is
the highest `prompts-2.1.X.json` in tweakcc-fixed's `data/prompts/`.

## Stage 1 - Report (read-only)

Resolve the clone paths and gather state in one block. This makes no changes.

```bash
LCC=$(dirname "$(readlink ~/.tweakcc/system-prompts)")
TF=""
for d in ~/dev/tweakcc-fixed ~/tweakcc-fixed; do
  [ -d "$d/.git" ] && git -C "$d" remote get-url origin 2>/dev/null | grep -q 'skrabe/tweakcc-fixed' && TF="$d" && break
done
[ -z "$TF" ] && TF=$(find ~ -maxdepth 5 -type d -name tweakcc-fixed -not -path '*/node_modules/*' 2>/dev/null | while read -r d; do git -C "$d" remote get-url origin 2>/dev/null | grep -q 'skrabe/tweakcc-fixed' && echo "$d" && break; done)
echo "LCC=$LCC"; echo "TF=${TF:-NOT FOUND}"

echo "### CURRENT ###"
claude --version
echo "CC binaries on disk:"; ls ~/.local/share/claude/versions/ 2>/dev/null
echo "LCC HEAD:  $(git -C "$LCC" rev-parse --short HEAD) $(git -C "$LCC" log -1 --format='%s')"
echo "TF  HEAD:  $(git -C "$TF" rev-parse --short HEAD) $(git -C "$TF" log -1 --format='%s')"

echo "### LATEST ###"
echo "CC latest (Anthropic): $(npm view @anthropic-ai/claude-code version 2>/dev/null)"
git -C "$LCC" fetch origin --quiet; git -C "$TF" fetch origin --quiet
echo "LCC origin: $(git -C "$LCC" rev-parse --short origin/HEAD) $(git -C "$LCC" log -1 --format='%s' origin/HEAD)"
echo "TF  origin: $(git -C "$TF" rev-parse --short origin/main) $(git -C "$TF" log -1 --format='%s' origin/main)"
echo "Latest supported CC: $(git -C "$TF" ls-tree -r --name-only origin/main -- data/prompts/ | grep -oE '2\.1\.[0-9]+' | sort -V | tail -1)"

echo "### DELTA ###"
echo "LCC behind: $(git -C "$LCC" rev-list --count HEAD..origin/HEAD) commits"
echo "TF  behind: $(git -C "$TF" rev-list --count HEAD..origin/main) commits"
echo "Override file changes (LCC):"
git -C "$LCC" diff --stat HEAD origin/HEAD -- system-prompts/ system-reminders/ | tail -40

echo "### BLOCKERS ###"
echo "LCC local-only commits: $(git -C "$LCC" rev-list --count origin/HEAD..HEAD)"
echo "TF  local-only commits: $(git -C "$TF" rev-list --count origin/main..HEAD)"
echo "LCC working tree:"; git -C "$LCC" status --short
echo "TF  working tree:"; git -C "$TF" status --short
echo "Stale apply cache:"; ls -la ~/.tweakcc/native-binary.backup ~/.tweakcc/native-claudejs-orig.js ~/.tweakcc/native-claudejs-patched.js 2>/dev/null || echo "  (none - clean)"
echo "latest symlink:"; ls -la ~/.local/state/claude/latest 2>/dev/null || echo "  (absent)"
```

Then present this report and **stop**:

```
## tweakcc stack upgrade - Stage 1 report

| Piece          | Current | Target | Behind     |
|----------------|---------|--------|------------|
| Claude Code    | <ver>   | <ver>  | -          |
| LCC overrides  | <sha>   | <sha>  | <N> commits|
| tweakcc-fixed  | <sha>   | <sha>  | <N> commits|

Target CC version: <the latest supported CC version>

What changes: <summary of override files added / removed / modified, from the diff --stat>

Blockers: <list, or "none">

Recommendation: <proceed | already up to date | resolve blockers first>
```

Decide the **target CC version** as the latest supported CC version (highest
`prompts-2.1.X.json`), provided Anthropic's npm `latest` is at or above it. If
the stack is already at target and 0 commits behind, say so - nothing to do.

Read `git status --short` carefully: untracked `system-reminders/*.md` files are
expected (Stage 2 handles them), but **local-only commits or uncommitted edits
to tracked files are real blockers** - surface them and do not plan to discard
them.

**Stop here. Present the report and wait for the user to explicitly approve
before doing anything in Stage 2.**

## Stage 2 - Upgrade (only after explicit approval)

Re-run the resolve block from Stage 1 first so `$LCC` and `$TF` are set (shell
state does not persist between commands - use the resolved absolute paths in
every step below).

**Pre-flight.** If either repo has local-only commits or uncommitted changes to
tracked files, stop and ask the user how to handle them. Never force or discard.

1. **Clear the stale apply cache.** The patcher caches a pristine snapshot of
   the CC binary. If that snapshot is from an older CC version, `--apply` writes
   old-version-derived content into the new binary and corrupts it. Remove the
   cache so the patcher re-snapshots the fresh binary:
   ```bash
   rm -f ~/.tweakcc/native-binary.backup ~/.tweakcc/native-claudejs-orig.js ~/.tweakcc/native-claudejs-patched.js
   ```

2. **Back up and clear untracked override files.** The patcher auto-seeds
   `system-reminders/*.md` (including per-MCP-server files) on `--apply`. Because
   that directory is symlinked into the LCC clone, those files show up as
   untracked and will block `git pull` once upstream tracks same-named files.
   They re-seed on the next `--apply`, so back them up and clear them:
   ```bash
   cp -R "$LCC/system-reminders/" /tmp/tweakcc-upgrade-backup-system-reminders/
   git -C "$LCC" clean -fd -- system-reminders/
   ```

3. **Install the target CC binary** (pristine; may prompt for network/auth):
   ```bash
   claude install <target-version>
   ```

4. **Update the repos.** Both must fast-forward cleanly:
   ```bash
   git -C "$LCC" pull --ff-only
   git -C "$TF" pull --ff-only
   pnpm --dir "$TF" install && pnpm --dir "$TF" build
   ```

5. **Re-apply the overrides:**
   ```bash
   node "$TF/dist/index.mjs" --apply
   ```
   Read the output. A clean run reports per-prompt char savings and no errors.
   Any error or a complaint about a missing prompt means the override set and
   the CC binary version are out of sync - stop and investigate, do not ignore it.

6. **Check the `latest` symlink.** The CC launcher resolves
   `~/.local/state/claude/latest`; if it points at a version that is not on
   disk, it silently falls back to newest-by-mtime. Confirm it points at the
   target version under `~/.local/share/claude/versions/`, and repoint it if not.

7. **Verify:**
   ```bash
   claude --version
   claude --print "say hello"
   ```
   `claude --version` should report the target CC version. The current session
   still runs the old binary - tell the user to relaunch `claude` to pick up the
   upgrade.

Finish with a short summary: old -> new CC version, both repo SHAs moved, apply
result, and the relaunch reminder.

## Why the guardrails matter

- **Stale apply cache** is the highest-severity footgun - it produces a binary
  that reports the wrong version and behaves like an older CC. Always clear it
  before `--apply` on a version bump.
- **Untracked `system-reminders/` files** are harmless in themselves (they
  re-seed), but they will hard-block `git pull --ff-only`. Clearing them is the
  fix; the backup is just a safety net.
- **`--ff-only`** keeps the upgrade honest: if a repo cannot fast-forward, there
  is local divergence that needs a human decision, not an automatic merge.
- **Re-apply is mandatory** after every CC binary change - a fresh `claude
  install` is pristine and carries none of the overrides until `--apply` runs.

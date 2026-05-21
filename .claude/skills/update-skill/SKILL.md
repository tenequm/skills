---
name: update-skill
description: "Thorough on-demand refresh of one skill in this repo. Researches kb/upstream/docs in parallel, gates twice for approval, bumps version, updates CHANGELOG, runs just check, commits and watches CI. Use to update, refresh, or check the freshness of a specific skill."
argument-hint: "[skill-name]"
disable-model-invocation: true
metadata:
  version: "0.2.0"
---

# Update Skill

Run a thorough on-demand refresh of one skill in this repo. Two hard human-approval gates ensure no edits or commits happen without explicit confirmation.

The target skill is: $ARGUMENTS

If no argument was provided, run `ls ${CLAUDE_PROJECT_DIR}/skills/` and ask the user which to update. Stop until confirmed. Then verify `${CLAUDE_PROJECT_DIR}/skills/$ARGUMENTS/SKILL.md` exists; if not, list skills and ask again. Throughout this run, `<name>` refers to the resolved skill name.

## Operating rules

These rules apply across all phases:

- **GATE 1 stops before any edit.** Do NOT call Edit or Write until the user replies affirmatively to the GATE 1 banner.
- **GATE 2 stops before any commit or push.** Do NOT run `git commit` or `git push` until the user replies affirmatively to the GATE 2 banner.
- **Privacy scan is a hard blocker.** Every skill here publishes publicly. The run does not reach a commit while a Phase 6 leak finding is unresolved.
- **Sticky posture.** Once GATE 1 has been emitted, "report findings first" persists across follow-up rounds in the same session. If the user replies `changes` or asks for revisions, re-emit the gate after revising; never silently apply.
- **Non-resume.** If the session is interrupted between GATE 1 and GATE 2, re-run `/update-skill <name>` from scratch. There is no checkpoint or resume mechanism.
- **No `--no-verify`, no `--amend`, no force-push** unless the user explicitly authorizes it for this run. Per project CLAUDE.md.

## Phase 1 - Pre-flight read

Read every file in `skills/<name>/` end-to-end, in parallel:
- `skills/<name>/SKILL.md`
- All files under `skills/<name>/references/` (use Glob first to enumerate)
- `skills/<name>/CHANGELOG.md` (if present)

Capture state for the rest of the run:
- `metadata.version` (current)
- `metadata.upstream` (current; parse to `{name: version}` map; empty if absent)
- Topmost CHANGELOG entry date (if `CHANGELOG.md` exists; this is the "last verified" signal)
- `git log -1 --format=%cs -- skills/<name>/` date (last touch)
- `bootstrap_needed` flag = true if `metadata.upstream` is missing OR `CHANGELOG.md` is missing

## Phase 2 - Parallel research

Dispatch three research subagents in a single message, one per angle. **Adapt each angle to the skill**: a skill wrapping a package researches that package's releases and source; a skill tracking living docs or a spec researches those docs and their source repos; a skill with no upstream at all still gets the usage angle.

- **Usage** (kb): mine `mcp__kb__kb_search` with NO `project` filter for footguns, scenario-specific breakage, inefficiencies, gaps, and recurring misunderstandings the skill could absorb. These are **advisory leads, not facts** - never verified, ground-checked in Phase 3.
- **Upstream**: releases, commits, and merged PRs since the last-verified date. Read real source - clone to `~/pjv/<owner>/<repo>` (lowercase) or use the GitHub MCP pinned to a concrete tag/SHA.
- **Docs**: the current canonical docs, read from source (raw `.md` or cloned repo), not model-summarized. Compare them against the skill's current `SKILL.md` and `references/`, flagging API changes, deprecated or removed symbols, and patterns the skill should adopt.

Every finding is one bulleted line: `[KIND]` (`ADD`/`CHANGE`/`DEPRECATE`/`REMOVE`/`FIX`/`SECURITY`), a one-line summary, an exact quote from the source (no paraphrase), and a citation. kb findings also carry `status: advisory`. Merge all returns into one list, deduped by `(KIND, citation)`.

## Phase 3 - Verify, report, GATE 1

### Ground-truth verification (before the report)

No row ships unverified. Before a finding becomes a row, confirm it against primary source read **today**:

- Verify the finding's claim **and the existing skill text it touches** - links, enumerated lists, pinned versions, version-coupled examples. Spot-check the skill's other upstream-coupled claims even where no finding landed; silent staleness is the common miss.
- A row asserting upstream state (a bug, API shape, version, behavior) cites the primary source checked - cloned `repo@SHA file:line`, a release, or a docs URL; a kb citation alone is insufficient, so re-ground it or drop it. A row that is purely experiential enrichment (a recurring gap or confusion) may keep its kb citation, but verify the wording you write is technically correct.
- Drop a kb-reported bug already fixed upstream; correct any finding whose kb framing the source contradicts.

### Report

Print a structured report, sections in order:

1. **Tracked packages diff** - `package | pinned | latest | delta`, or "no upstream packages tracked."
2. **Proposed `metadata.upstream`** - the new flat string. No floating tags (`@latest`/`@next`/`@beta`/`@canary`); pin to a concrete tag or SHA.
3. **Proposed CHANGELOG entry** - a Keep a Changelog block ready to commit.
4. **Proposed edits** - one row per smallest atomic change, each with a stable ID (`A1`/`C1`/`D1`/`R1`/`F1`/`S1`...): `<ID> | target file | one-line summary | citation`. Batch trivially-related changes into one row; past ~20 rows, consider whether the skill needs a rewrite rather than a patch.
5. **Bootstrap proposal** (only when `bootstrap_needed`): candidate upstream packages greppable from the skill's content, each as `<package> (mentioned <N>x, first cite: <file>:<line>)` for the user to confirm or prune; plus a seed `CHANGELOG.md`.

### No-op short-circuit

If sections 1-4 yield zero rows AND `bootstrap_needed` is false, print this verbatim and exit cleanly - no file changes, no commit:

```
All current as of <today>. Last verified per CHANGELOG.md on <date> against <metadata.upstream value>.
```

### CHANGELOG format

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. The dated entry uses only the sections it has content for (Added / Changed / Deprecated / Removed / Fixed / Security), plus a `Verified against: <pkg@version list>` trailer **only if** a tracked package version actually changed this run.

When `bootstrap_needed`, create the full file with this header:

```markdown
# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [<current-version>] - <YYYY-MM-DD>
- Initial CHANGELOG; tracking established.
```

### GATE 1 banner (verbatim)

```
GATE 1 - APPROVE TO EDIT? (yes / yes <IDs> / drop <IDs> / changes <free-form> / no)
```

Reply parsing:
- `yes` / `yes all` -> apply every row
- `yes A1-A4 C1` -> apply only those rows (and the listed package version updates, if any)
- `drop D1,R2` -> apply everything except those
- `changes <text>` -> revise the report and re-emit GATE 1
- `no` -> abort, no changes

Do NOT call Edit or Write until you receive an affirmative. Every revision round re-emits GATE 1; never silently apply.

## Phase 4 - Apply

Apply each approved row with Edit/Write; batch independent edits in parallel. Then, in order:

1. Update `metadata.upstream` to the new comma-separated `<name>@<version>` list. Reject floating tags - stop with an error if one appears.
2. Bump `metadata.version` (semver per project CLAUDE.md: patch for fixes, minor for new content/sections, major for breaking removal).
3. Append the new dated entry to `CHANGELOG.md` directly under `[Unreleased]`, above the previous entry. Add the `Verified against:` trailer only if a tracked version changed this run.
4. If `bootstrap_needed`, write the full `CHANGELOG.md` from the bootstrap header plus the approved seed entry.

## Phase 5 - just check

Run `just check` from the repo root (it regenerates `README.md` - the most common CI failure cause). On failure, surface the error verbatim, fix the root cause, and re-run until clean. No `--no-verify`, no `--amend`, no hook-skipping.

## Phase 6 - Privacy scan + diff review + GATE 2

### Privacy / leak scan (hard blocker)

Every skill here publishes publicly, and kb research draws on private cross-project conversations - a leak can reach the diff. Before showing the diff, dispatch a dedicated agent (separate from the Phase 2 research agents) to scan the added/changed lines under `skills/<name>/` and `README.md`.

It flags anything unsafe for a public skill: secrets (keys, tokens, passwords, `.env` values, connection strings), personal data (real names, emails, handles), and the easy-to-miss ones - non-public project or repo names, internal hostnames or endpoints, ticket IDs, local machine paths, kb conversation IDs. Intentional public references are fine (the public repo owner, official upstream repos and docs, published package names, spec URLs). The agent returns `[LEAK] <file>:<line> - <what> - suggested redaction: <text>` per issue, or exactly `NO LEAKS FOUND`.

An unresolved `[LEAK]` is a hard blocker: redact each finding, re-run the scan, and repeat until clean before GATE 2. Hold the commit message to the same public-safe standard.

### Diff review

Print `git status`, `git diff --stat`, and per-file diffs for `SKILL.md`, every changed `references/` file, `CHANGELOG.md`, and `README.md`. Then print this recovery hint verbatim, immediately above the gate banner:

```
To discard everything: git restore . && git clean -fd skills/<name>/
```

```
GATE 2 - APPROVE COMMIT + PUSH? (yes / no)
```

Wait for explicit confirmation. Do not commit on ambiguous responses.

## Phase 7 - Commit, push, watch

**Branch guard first.** Run `git rev-parse --abbrev-ref HEAD`. If the result is not `main`, ask the user: push to that branch and open a PR (recommended), force-push to main (only on explicit instruction - it skips PR review and publishes straight to ClawHub via CI), or cancel.

Commit with a conventional-commit message (type per content, per project CLAUDE.md) using the HEREDOC pattern:

```bash
git commit -m "$(cat <<'EOF'
<type>(<name>): <one-line summary>

<body if non-trivial>
EOF
)"
```

- **On `main`**: `git push`, then `gh run watch` the triggered run. On CI failure, surface logs verbatim; do not auto-retry.
- **On a feature branch**: `git push -u origin <branch>`, then `gh pr create` with a body summarizing the Phase 3 report. Skip `gh run watch` (PR CI is non-publishing).

After CI is green on `main`, optionally confirm the GitHub Release (`gh release view skills-$(git rev-parse --short HEAD)`) and the ClawHub publish (the slug can differ from the folder name - see `CLAWHUB_SLUG_OVERRIDES` in `scripts/generate_readme.py`).

## Done

Report a one-line summary to the user: skill name, version delta, tracked packages updated, CI status.

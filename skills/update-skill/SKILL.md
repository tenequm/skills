---
name: update-skill
description: "Thorough on-demand refresh of one skill in a skills repository: researches usage/upstream/docs in parallel, gates twice for approval, bumps version, updates CHANGELOG, runs the repo's validation, then commits and watches CI. Install the pond MCP (https://pond.cascade.fyi/) for the prior-session usage angle; without it that angle is skipped. Use to update, refresh, or check the freshness of a specific skill."
argument-hint: "[skill-name]"
disable-model-invocation: true
metadata:
  version: "0.8.1"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/update-skill
    emoji: "🔄"
  upstream: "keep-a-changelog@2.0.0"
---

# Update Skill

Run a thorough on-demand refresh of one skill in a skills repository. Two hard human-approval gates ensure no edits or commits happen without explicit confirmation.

The target skill is: $ARGUMENTS

If no argument was provided, run `ls ${CLAUDE_PROJECT_DIR}/skills/` and ask the user which to update. Stop until confirmed. Then verify `${CLAUDE_PROJECT_DIR}/skills/$ARGUMENTS/SKILL.md` exists; if not, list skills and ask again. Throughout this run, `<name>` refers to the resolved skill name.

## Operating rules

These rules apply across all phases:

- **GATE 1 stops before any edit.** Do NOT call Edit or Write until the user replies affirmatively to the GATE 1 banner.
- **GATE 2 stops before any commit or push.** Do NOT run `git commit` or `git push` until the user replies affirmatively to the GATE 2 banner.
- **Privacy scan is a hard blocker.** Skills in a public repo can publish on merge, so the run does not reach a commit while a Phase 6 leak finding is unresolved.
- **Sticky posture.** Once GATE 1 has been emitted, "report findings first" persists across follow-up rounds in the same session. If the user replies `changes` or asks for revisions, re-emit the gate after revising; never silently apply.
- **Non-resume.** If the session is interrupted between GATE 1 and GATE 2, re-run `/update-skill <name>` from scratch. There is no checkpoint or resume mechanism.
- **Duplicate triggers.** If a scheduled task or a repeated invocation fires while a run is holding at a gate, hold at the emitted gate and answer from the existing report - never redo research or re-apply edits.
- **No `--no-verify`, no `--amend`, no force-push** unless the user explicitly authorizes it for this run. Per the repo's CLAUDE.md or AGENTS.md.
- **Working directory.** Every path, every `just check`, and every working git command (`status`/`diff`/`add`/`commit`/`push`) in the phases below runs against `<workdir>` - the worktree created in Phase 0 if the user opted in, otherwise `${CLAUDE_PROJECT_DIR}`. Use absolute paths under `<workdir>`; do not mix in the main checkout once a worktree is chosen. The exception is Phase 0's own `git worktree add`/`remove`, which must run against `${CLAUDE_PROJECT_DIR}` (the main checkout).

## Phase 0 - Worktree choice (ask first)

After resolving `<name>`, ask exactly once: "Run this update in a dedicated git worktree, so you can update other skills in parallel? (yes / no)". Wait for the reply.

- **no** (default) -> set `<workdir>` = `${CLAUDE_PROJECT_DIR}` and proceed to Phase 1 in the current checkout.
- **yes** -> create an isolated worktree on a fresh branch and use it as `<workdir>` for the entire run:
  ```bash
  git -C "${CLAUDE_PROJECT_DIR}" worktree add "${CLAUDE_PROJECT_DIR}/../skills-<name>" -b chore/update-<name>
  ```
  Set `<workdir>` = `${CLAUDE_PROJECT_DIR}/../skills-<name>`. If that path or branch already exists, add the same numeric suffix (`-2`, `-3`, ...) to both the worktree path and the branch name until both are free, and carry that suffix into `<workdir>`. Every later phase - reads, edits, `just check`, diff review, commit, push - operates inside `<workdir>`. The Phase 7 branch guard will see `chore/update-<name>` and route to the push + PR flow automatically. Keep the worktree until the PR is **merged** - follow-up review rounds reuse it instead of recreating it. Then clean up in order: `git -C "${CLAUDE_PROJECT_DIR}" worktree remove "<workdir>"` first, then delete the branch (`git branch -d chore/update-<name>`) - a branch delete fails while a worktree still holds the branch. `git worktree remove` refuses if there are uncommitted changes (leave it in place and tell the user if so); `git worktree prune` clears stale entries left by interrupted runs. If a generated file (e.g. `README.md`) conflicts when the PR falls behind the default branch, rebase and re-run the generator - never hand-merge generated output. If the user aborts before a PR exists, remove the worktree and delete the branch the same way.

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
- `LICENSE.txt` (or the repo's equivalent) present and non-empty - publish pipelines and repo linters commonly hard-fail without it; if missing, queue a fix row in the Phase 3 report
- `bootstrap_needed` flag = true if `metadata.upstream` is missing OR `CHANGELOG.md` is missing - **unless the skill is upstreamless by nature** (it wraps no package, spec, or living doc - e.g. a workflow or writing skill like `polish`). For those, omitting `metadata.upstream` is correct, not a gap: derive `bootstrap_needed` from the missing `CHANGELOG.md` alone and skip the upstream-candidate proposal.

## Phase 2 - Parallel research

Dispatch three research subagents in a single message, one per angle. Subagents run in the background by default (Claude Code v2.1.198+): collect every agent's completion before starting Phase 3. If the user supplied a seed finding (a bug they hit, a release they know about), pass it verbatim to the relevant agent - specific leads converge fastest. **Adapt each angle to the skill**: a skill wrapping a package researches that package's releases and source; a skill tracking living docs or a spec researches those docs and their source repos; a skill with no upstream at all still gets the usage angle.

- **Usage** (pond - optional): if the pond MCP (`mcp__pond__pond_search`) is available, mine it with NO `project` filter for footguns, scenario-specific breakage, inefficiencies, gaps, and recurring misunderstandings the skill could absorb. Keep the query semantic (concepts, not project names); scope with filters. These are **advisory leads, not facts** - never verified, ground-checked in Phase 3. **If pond is not installed, skip this angle entirely** - dispatch only the upstream and docs agents, and note "Usage angle skipped: pond MCP not available (https://pond.cascade.fyi/)" in the Phase 3 report.
- **Upstream**: releases, commits, and merged PRs since the last-verified date. Read real source - clone to a local scratch dir (e.g. `~/pjv/<owner>/<repo>`, lowercase) or use the GitHub MCP pinned to a concrete tag/SHA. For skills wrapping a CLI, also ground-truth against the live installed binary (`<cmd> --help`, real invocations) - docs and clones lag shipped behavior.
- **Docs**: the current canonical docs, read from source (raw `.md` or cloned repo), not model-summarized. Two distinct jobs, **both required**:
  - **(a) Drift check** - compare the docs against the skill's current `SKILL.md` and `references/`, flagging API changes, deprecated or removed symbols, and patterns the skill should adopt. This is anchored to what the skill already says.
  - **(b) Coverage sweep** - enumerate upstream's *current* feature/concept surface from the docs nav / table of contents, the API index, and the "what's new" / changelog. List every major capability, primitive, or concept the skill has **zero mention of**. Do NOT anchor this to existing skill content - the whole point is to find net-new surface the skill is silent about (`ADD` findings). This is the step a "verify what's there" pass structurally misses.

Every finding is one bulleted line: `[KIND]` (`ADD`/`CHANGE`/`DEPRECATE`/`REMOVE`/`FIX`/`SECURITY`), a one-line summary, an exact quote from the source (no paraphrase), and a citation. pond findings also carry `status: advisory`. Merge all returns into one list, deduped by `(KIND, citation)`.

## Phase 3 - Verify, report, GATE 1

### Ground-truth verification (before the report)

No row ships unverified. Before a finding becomes a row, confirm it against primary source read **today**:

- Verify the finding's claim **and the existing skill text it touches** - links, enumerated lists, pinned versions, version-coupled examples. Spot-check the skill's other upstream-coupled claims even where no finding landed; silent staleness is the common miss.
- A row asserting upstream state (a bug, API shape, version, behavior) cites the primary source checked - cloned `repo@SHA file:line`, a release, or a docs URL; a pond citation alone is insufficient, so re-ground it or drop it. A row that is purely experiential enrichment (a recurring gap or confusion) may keep its pond citation, but verify the wording you write is technically correct.
- Drop a pond-reported bug already fixed upstream; correct any finding whose pond framing the source contradicts.
- **Coverage-gap rows** (net-new concepts from the Phase 2(b) sweep) are verified two ways: confirm the concept exists in today's source (cite it), **and** confirm the skill genuinely omits it - grep the skill for the concept and any synonyms before claiming it's absent, so a renamed-but-present feature isn't reported as missing.
- Scope-check every usage-derived row: a learning about private infrastructure (internal hosts, personal tooling, machine-specific setups) belongs in the user's own CLAUDE.md or memory, not a public skill. Route it there and drop the row - the Phase 6 leak scan cannot make this judgment call.

### Report

Print a structured report, sections in order:

1. **Tracked packages diff** - `package | pinned | latest | delta`, or "no upstream packages tracked."
2. **Proposed `metadata.upstream`** - the new flat string. No floating tags (`@latest`/`@next`/`@beta`/`@canary`); pin to a concrete tag or SHA.
3. **Proposed CHANGELOG entry** - a Keep a Changelog block ready to commit.
4. **Proposed edits** - one row per smallest atomic change, each with a stable ID (`A1`/`C1`/`D1`/`R1`/`F1`/`S1`...): `<ID> | target file | one-line summary | citation`. Batch trivially-related changes into one row; past ~20 rows, consider whether the skill needs a rewrite rather than a patch. When ADD rows are numerous, include the projected post-apply `SKILL.md` line count; if it would cross the repo's size cap (500 lines in this repo), plan the `references/` split as part of the proposal, not as a surprise after apply.
5. **New-concept coverage** (**always present, never omitted**) - the result of the Phase 2(b) coverage sweep. Either a table of net-new upstream concepts the skill omits (each becoming an `ADD` row above), or the explicit statement that there are none. End this section with the verbatim attestation below. Coverage need not be complete to pass - but any gap in what you could enumerate (JS-gated docs, rate limits, unreachable pages) must be named here, not silently dropped:
   ```
   Coverage sweep: enumerated upstream's current surface from <sources>. Net-new concepts the skill omits: <list> / none since <last-verified date>. Not reachable this run: <areas, or "none">.
   ```
6. **Bootstrap proposal** (only when `bootstrap_needed`): candidate upstream packages greppable from the skill's content, each as `<package> (mentioned <N>x, first cite: <file>:<line>)` for the user to confirm or prune; plus a seed `CHANGELOG.md`. Propose only upstreams whose releases would invalidate the skill's content - the package, spec, or living doc the skill teaches. A tool mentioned incidentally (a validator run once, a CLI in one example) is not an upstream candidate. If the skill is **upstreamless by nature**, say so explicitly, propose no candidates, and leave `metadata.upstream` omitted - only seed the `CHANGELOG.md`.

### No-op short-circuit

If sections 1-4 yield zero rows AND the Phase 2(b) coverage sweep found no omitted concepts (section 5 attestation says "none") AND `bootstrap_needed` is false, print this verbatim and exit cleanly - no file changes, no commit. Never short-circuit without the section 5 attestation present:

```
All current as of <today>. Last verified per CHANGELOG.md on <date> against <metadata.upstream value>.
```

### CHANGELOG format

[Keep a Changelog](https://keepachangelog.com/en/2.0.0/) format. The dated entry uses only the sections it has content for (Added / Changed / Deprecated / Removed / Fixed / Security), plus a `Verified against: <pkg@version list>` trailer **only if** a tracked package version actually changed this run. Mark breaking changes inside Changed/Removed with a leading `**Breaking:**` marker, and pin the KaC link in preambles to the version followed (both per KaC 2.0.0).

When `bootstrap_needed`, create the full file with this header:

```markdown
# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
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

1. Update `metadata.upstream` to the new comma-separated `<name>@<version>` list. Reject floating tags - stop with an error if one appears. Skip entirely if the skill is upstreamless by nature - leave `metadata.upstream` omitted.
2. Bump `metadata.version` (semver per the repo's CLAUDE.md or AGENTS.md: patch for fixes, minor for new content/sections, major for breaking removal).
3. Append the new dated entry to `CHANGELOG.md` directly under `[Unreleased]`, above the previous entry. Add the `Verified against:` trailer only if a tracked version changed this run.
4. If `bootstrap_needed`, write the full `CHANGELOG.md` from the bootstrap header plus the approved seed entry.
5. When pasting upstream doc examples into a `SKILL.md` body, never let a `!` at line start or after whitespace directly touch a backticked command - Claude Code executes it at skill load, even inside code fences, and repo linters may reject it. Keep such examples in `references/` or break the adjacency.
6. Check the post-apply `SKILL.md` line count against the repo's cap (500 here); if crossed, execute the `references/` split planned in Phase 3.

## Phase 5 - Repo validation gate

If the repo defines a validation command - check its CLAUDE.md/AGENTS.md or `Justfile`/`package.json` (e.g. `just check`, `npm run lint`, `make check`) - run it from `<workdir>` (the repo root, or the Phase 0 worktree). In this repo that is `just check`, which also regenerates `README.md` (the most common CI failure cause). On failure, surface the error verbatim, fix the root cause, and re-run until clean. If the failure looks unrelated to this run's edits, attribute before debugging: stash the changes (`git stash -u`) and re-run the gate on a clean tree. Failing identically means the breakage is pre-existing (an environment flake or repo issue) - unstash, report it to the user, and don't sink this run into debugging it. No `--no-verify`, no `--amend`, no hook-skipping. If the repo has no validation gate, skip this phase and note it.

## Phase 6 - Privacy scan + diff review + GATE 2

### Privacy / leak scan (hard blocker)

Skills in a public repo can publish on merge, and any research source can leak into the diff - especially pond, which draws on private cross-project conversations. This scan runs every time, whether or not pond was used. Before showing the diff, dispatch a dedicated agent (separate from the Phase 2 research agents) to scan the added/changed lines **and every new untracked file** under `skills/<name>/` and `README.md` (if the repo generates one). `git diff` alone misses brand-new files (e.g. a fresh `references/` doc) - enumerate them with `git status --porcelain` and give the agent their full content.

It flags anything unsafe for a public skill: secrets (keys, tokens, passwords, `.env` values, connection strings), personal data (real names, emails, handles), and the easy-to-miss ones - non-public project or repo names, internal hostnames or endpoints, ticket IDs, local machine paths, pond session IDs. Intentional public references are fine (the public repo owner, official upstream repos and docs, published package names, spec URLs). The agent returns `[LEAK] <file>:<line> - <what> - suggested redaction: <text>` per issue, or exactly `NO LEAKS FOUND`.

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

**Branch guard first.** Run `git rev-parse --abbrev-ref HEAD`. If the result is not the repo's default branch, ask the user: push to the current branch and open a PR (recommended), push directly to the default branch (only on explicit instruction - if the repo auto-publishes on merge, this skips PR review and ships straight to the registry), or cancel.

Commit with a conventional-commit message (type per content, per the repo's CLAUDE.md or AGENTS.md) using the HEREDOC pattern:

```bash
git commit -m "$(cat <<'EOF'
<type>(<name>): <one-line summary>

<body if non-trivial>
EOF
)"
```

- **On the default branch**: `git push`, then, if the repo has CI, `gh run watch` the triggered run. On CI failure, surface logs verbatim; do not auto-retry.
- **On a feature branch**: `git push -u origin <branch>`, then `gh pr create` with a body summarizing the Phase 3 report. Skip `gh run watch` at this point - PR CI is typically non-publishing, and some publish-on-merge repos run no PR CI at all. The run is not done at PR creation: once the PR merges, watch the default-branch publish run (`gh run watch`), confirm the publish landed, then do the Phase 0 cleanup (worktree first, then branch).

Updating several skills in one session? Land them together: batch into one push, or merge the PRs back-to-back and watch only the final publish run - each push to the default branch typically triggers a full republish.

If the repo auto-publishes on merge (e.g. to a registry via CI), confirm the publish landed once CI is green. The published slug and release/tag naming follow the repo's own pipeline - check its CLAUDE.md/AGENTS.md (the published slug can differ from the folder name).

## Done

Report a one-line summary to the user: skill name, version delta, tracked packages updated, CI status. If the repo's skills are consumed through an installer (e.g. `npx skills`), remind the user to refresh installed copies (`npx skills update <name>`) once the publish lands.

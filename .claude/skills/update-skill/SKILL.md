---
name: update-skill
description: "Thorough on-demand refresh of one skill in this repo. Researches kb/upstream/docs in parallel, gates twice for approval, bumps version, updates CHANGELOG, runs just check, commits and watches CI. Use to update, refresh, or check the freshness of a specific skill."
argument-hint: "[skill-name]"
disable-model-invocation: true
metadata:
  version: "0.1.0"
---

# Update Skill

Run a thorough on-demand refresh of one skill in this repo. Two hard human-approval gates ensure no edits or commits happen without explicit confirmation.

The target skill is: $ARGUMENTS

If no argument was provided, run `ls ${CLAUDE_PROJECT_DIR}/skills/` and ask the user which to update. Stop until confirmed. Then verify `${CLAUDE_PROJECT_DIR}/skills/$ARGUMENTS/SKILL.md` exists; if not, list skills and ask again. Throughout this run, `<name>` refers to the resolved skill name.

## Operating rules

These rules apply across all phases:

- **GATE 1 stops before any edit.** Do NOT call Edit or Write until the user replies affirmatively to the GATE 1 banner.
- **GATE 2 stops before any commit or push.** Do NOT run `git commit` or `git push` until the user replies affirmatively to the GATE 2 banner.
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

No mutations in this phase.

## Phase 2 - Parallel research (3 subagents in one Task message)

Dispatch all three subagents in a single message containing three Task tool calls. Each subagent MUST return findings as a bulleted list. Each item is prefixed with `[KIND]` (one of `ADD` / `CHANGE` / `DEPRECATE` / `REMOVE` / `FIX` / `SECURITY`), includes a live URL citation, and **quotes the exact symbol or section** as currently documented at that URL. No paraphrasing. This requirement folds validation into research and prevents hallucinated citations.

### Subagent A - kb research (cross-project usage patterns)

Brief the agent verbatim:

> Research real-world usage of the `<name>` skill across all conversations.
>
> Use `mcp__kb__kb_search` with NO `project` filter. Search across all projects to surface:
> - where this skill helped users complete a task
> - where the skill fell short or missed something users needed
> - recurring user issues or misunderstandings related to the skill's domain
> - common patterns of problems the skill could help avoid but currently doesn't
>
> Query shape: skill name, tracked package names from `metadata.upstream` (`<comma-separated list>`), key concepts from the skill body (`<extracted concepts>`).
>
> Return findings as a bulleted list. Each line: `[KIND] <one-line summary> - cite: <kb message id or URL> - quote: "<exact phrase from the source>"`. Use `[ADD]` for missing capabilities, `[CHANGE]` for outdated guidance, `[FIX]` for bugs, etc.

### Subagent B - upstream GitHub research

Brief the agent verbatim:

> Research upstream changes for packages tracked by the `<name>` skill.
>
> For each package in `metadata.upstream` (`<list>`):
> 1. Use `mcp__surf__surf_github_get` with `mode: "releases"` to list releases since the pinned version.
> 2. Use `mcp__surf__surf_github_get` with `mode: "commits"` for the same range if releases are sparse.
> 3. Use `mcp__surf__surf_github_search` to find merged PRs in the upstream repo since the topmost CHANGELOG entry date (`<date>`).
>
> For each significant change found, return a bulleted line: `[KIND] <one-line summary> - cite: <release URL or PR URL> - quote: "<exact wording from release notes or PR title>"`. Skip cosmetic-only releases.
>
> If `metadata.upstream` is empty, return an empty list.

### Subagent C - current docs research

Brief the agent verbatim:

> Verify current documentation for tracked packages in the `<name>` skill.
>
> For each package in `metadata.upstream`, find the canonical docs URL. Use `WebFetch` to read the relevant section.
>
> Compare current docs against sections in `skills/<name>/SKILL.md` and `skills/<name>/references/*`. Surface API changes, deprecated symbols, new patterns the skill should mention.
>
> Return findings as a bulleted list. Each line: `[KIND] <one-line summary> - cite: <docs URL> - quote: "<exact phrase from the docs>"`.
>
> If a referenced API/symbol no longer exists at the cited URL, mark it `[REMOVE]` or `[CHANGE]`.

After all three subagents return, merge into a single deduped list (by `(KIND, citation URL)`).

## Phase 3 - Findings report + GATE 1

Print a structured report with these sections in order:

1. **Tracked packages diff** - table: `package | pinned | latest | delta`. If `metadata.upstream` is empty, state "no upstream packages tracked."

2. **Proposed `metadata.upstream`** - the new flat string. Reject any floating tag (`@latest`, `@next`, `@beta`, `@canary`) at this stage; if a subagent surfaced one, replace with the concrete release tag or commit SHA before writing.

3. **Proposed CHANGELOG entry draft** - full Keep a Changelog markdown block, ready to commit (template below).

4. **Proposed edits per row** - smallest atomic units. **Each row gets a stable ID**: `A1`, `A2` ... for ADD; `C1`, `C2` ... for CHANGE; `D1` ... for DEPRECATE; `R1` ... for REMOVE; `F1` ... for FIX; `S1` ... for SECURITY. Each row format: `<ID> | target file | one-line summary | citation`.

5. **Bootstrap proposal** (only when `bootstrap_needed`): list candidate upstream packages found in the skill's content (greppable from SKILL.md code blocks, `references/`, any pre-existing tracked field like `effectVersionTracked`). Format each candidate: `<package> (mentioned <N> times, first cite: <file>:<line>)`. The user confirms or prunes. Also propose a seed `CHANGELOG.md` body using the template below.

### No-op short-circuit

If steps 1-4 produced zero rows requiring change AND `bootstrap_needed` is false, print this verbatim and exit:

```
All current as of <today>. Last verified per CHANGELOG.md on <date> against <metadata.upstream value>.
```

No file changes. No commit. Exit cleanly.

### CHANGELOG entry template (use in step 3)

```markdown
## [<new-version>] - <YYYY-MM-DD>

### Added
- ...

### Changed
- ...

Verified against: <comma-separated package@version list, only if at least one version actually changed in this run>
```

Use only the sections you have content for. Omit empty sections (Added / Changed / Deprecated / Removed / Fixed / Security).

### CHANGELOG bootstrap header (full file, used during bootstrap)

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
- `yes` or `yes all` -> apply every row in the report
- `yes A1-A4 C1` -> apply only those rows (and the listed package version updates if any)
- `drop D1,R2` -> apply everything except those rows
- `changes <text>` -> revise the report per the user's text and re-emit GATE 1
- `no` -> abort the run, no changes

Do NOT call Edit or Write until you receive an affirmative. The sticky-posture rule applies: every revision round re-emits GATE 1; never silently apply.

## Phase 4 - Apply

For each approved row, perform the edit using Edit or Write. Batch independent edits in parallel where possible.

After edits, in this order:

1. Update `metadata.upstream` flat string to the new comma-separated `<name>@<version>` list. **Reject floating tags** (`@latest`, `@next`, `@beta`, `@canary`) by raising an error and stopping. The GATE 1 review should have caught these; enforce here too.

2. Bump `metadata.version` per semver:
   - **patch** (0.3.0 -> 0.3.1) for fixes, typo corrections, version-pin refresh
   - **minor** (0.3.0 -> 0.4.0) for new content, new sections, new references/
   - **major** (0.3.0 -> 1.0.0) for breaking removal or restructure

3. Append the new dated entry to `skills/<name>/CHANGELOG.md` directly under the `[Unreleased]` header (above the previous most-recent dated entry). Include the `Verified against:` trailer ONLY if at least one tracked package version changed in this run.

4. If `bootstrap_needed` was true, write the full `CHANGELOG.md` file using the bootstrap header template (see Phase 3) plus the seed entry the user approved.

## Phase 5 - just check

Run `just check` from the repo root.

This auto-regenerates `README.md`, which is the most common CI failure cause. On failure:

- Surface the error verbatim to the user.
- Diagnose the root cause and fix.
- Re-run `just check` until it exits clean.
- Do NOT use `--no-verify`. Do NOT amend the previous commit. Do NOT skip hooks.

## Phase 6 - Diff review + GATE 2

Print:

1. `git status`
2. `git diff --stat`
3. Per-file diffs for: `skills/<name>/SKILL.md`, every changed file under `skills/<name>/references/`, `skills/<name>/CHANGELOG.md`, `README.md`.

Then print this recovery hint **verbatim** immediately above the GATE 2 banner:

```
To discard everything: git restore . && git clean -fd skills/<name>/
```

Then emit the gate banner verbatim:

```
GATE 2 - APPROVE COMMIT + PUSH? (yes / no)
```

Wait for explicit confirmation. Do not commit on ambiguous responses.

## Phase 7 - Commit, push, watch

### Branch guard (run first)

Run `git rev-parse --abbrev-ref HEAD`. If the result is not `main`, print:

```
On branch <X>. Push there and open a PR (recommended) / force-push to main / cancel?
```

- **PR flow (recommended)** -> `git push -u origin <X>`, then `gh pr create` with a body summarizing changes from the Phase 3 report.
- **Force-push to main** -> only if the user explicitly says so. Risks publishing a half-baked skill to ClawHub on every CI run.
- **Cancel** -> stop the run.

### Commit (verbatim HEREDOC pattern)

```bash
git commit -m "$(cat <<'EOF'
<type>(<name>): <one-line summary>

<body if non-trivial>
EOF
)"
```

Type chosen by content:
- `feat` for new sections or new references/
- `fix` for corrections
- `chore` for routine version refreshes
- `docs` for prose-only edits

### Push and watch

- **On `main`**: `git push`, then `gh run watch` on the triggered workflow. On CI failure, surface logs verbatim. Do not auto-retry.
- **On feature branch (PR flow)**: `git push -u origin <branch>` and `gh pr create` already done above. Skip `gh run watch` (CI on PRs is non-publishing).

After CI green on `main`, optionally verify:

- `gh release view skills-$(git rev-parse --short HEAD)` -> confirm GitHub Release created
- `clawhub view <override-slug-or-folder>` -> confirm ClawHub publish (slug from `CLAWHUB_SLUG_OVERRIDES` in `scripts/generate_readme.py`)

## Done

Report a one-line summary to the user: skill name, version delta, tracked packages updated, CI status.
